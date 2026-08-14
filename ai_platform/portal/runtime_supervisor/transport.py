from __future__ import annotations

import json
import os
import socket
import stat
import struct
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from .types import SupervisorRequest


MAX_REQUEST_BYTES = 16 * 1024
REQUEST_TIMEOUT_SECONDS = 5.0
ACCEPT_POLL_SECONDS = 0.25
MAX_CONNECTION_WORKERS = 8
MAX_INFLIGHT_CONNECTIONS = 16
WORKER_SHUTDOWN_TIMEOUT_SECONDS = 5.0
TRUSTED_SOCKET_ROOT = Path("/run/quant-platform")


class SupervisorTransportError(RuntimeError):
    pass


class SupervisorResult(Protocol):
    def model_dump_json(self) -> str: ...


class SupervisorExecutor(Protocol):
    def execute(self, request: SupervisorRequest) -> SupervisorResult: ...


def linux_peer_uid(connection: socket.socket) -> int:
    """Return the authenticated local process uid from Linux SO_PEERCRED."""

    if not hasattr(socket, "SO_PEERCRED"):
        raise SupervisorTransportError("SO_PEERCRED is unavailable")
    credentials = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
    _pid, uid, _gid = struct.unpack("3i", credentials)
    return uid


class UnixSocketSupervisorServer:
    """Bounded UDS transport; never HTTP and never routable off-host."""

    def __init__(
        self,
        path: Path,
        supervisor: SupervisorExecutor,
        *,
        allowed_peer_uids: frozenset[int],
        peer_uid: Callable[[socket.socket], int] = linux_peer_uid,
        socket_access_gid: int | None = None,
        max_workers: int = MAX_CONNECTION_WORKERS,
        max_inflight_connections: int = MAX_INFLIGHT_CONNECTIONS,
        worker_shutdown_timeout_seconds: float = WORKER_SHUTDOWN_TIMEOUT_SECONDS,
    ) -> None:
        normalized_path = str(path).replace("\\", "/")
        if not path.is_absolute() and not normalized_path.startswith("/"):
            raise ValueError("supervisor socket path must be absolute")
        if not allowed_peer_uids or any(uid < 0 for uid in allowed_peer_uids):
            raise ValueError("at least one valid peer uid is required")
        if socket_access_gid is not None and socket_access_gid < 0:
            raise ValueError("socket access gid must be non-negative")
        if not 0 < max_workers <= MAX_CONNECTION_WORKERS:
            raise ValueError("worker count exceeds the bounded supervisor limit")
        if not max_workers <= max_inflight_connections <= MAX_INFLIGHT_CONNECTIONS:
            raise ValueError("inflight connection count exceeds the bounded supervisor limit")
        if not 0 < worker_shutdown_timeout_seconds <= WORKER_SHUTDOWN_TIMEOUT_SECONDS:
            raise ValueError("worker shutdown timeout exceeds the bounded supervisor limit")
        self._path = path
        self._supervisor = supervisor
        self._allowed_peer_uids = allowed_peer_uids
        self._peer_uid = peer_uid
        self._socket_access_gid = socket_access_gid
        self._max_workers = max_workers
        self._max_inflight_connections = max_inflight_connections
        self._worker_shutdown_timeout_seconds = worker_shutdown_timeout_seconds
        self._worker_futures: set[Future[None]] = set()
        self._worker_futures_lock = threading.Lock()

    def handle(self, connection: socket.socket) -> None:
        connection.settimeout(REQUEST_TIMEOUT_SECONDS)
        if self._peer_uid(connection) not in self._allowed_peer_uids:
            self._send(connection, {"accepted": False, "code": "PEER_NOT_AUTHORIZED"})
            return
        try:
            payload = self._read_request(connection)
        except SupervisorTransportError:
            self._send(connection, {"accepted": False, "code": "INVALID_REQUEST"})
            return
        try:
            request = SupervisorRequest.model_validate_json(payload)
        except ValidationError:
            self._send(connection, {"accepted": False, "code": "INVALID_REQUEST"})
            return
        outcome = self._supervisor.execute(request)
        connection.sendall(outcome.model_dump_json().encode() + b"\n")

    def serve_forever(
        self,
        *,
        stop_event: threading.Event | None = None,
        ready_event: threading.Event | None = None,
    ) -> None:
        address_family = self._validate_socket_root()
        listener = socket.socket(address_family, socket.SOCK_STREAM)
        workers = ThreadPoolExecutor(
            max_workers=self._max_workers, thread_name_prefix="runtime-supervisor-uds"
        )
        inflight = threading.BoundedSemaphore(self._max_inflight_connections)
        bound_inode: int | None = None
        try:
            listener.bind(str(self._path))
            bound_inode = self._path.lstat().st_ino
            self._configure_filesystem_access()
            listener.listen(self._max_inflight_connections)
            listener.settimeout(ACCEPT_POLL_SECONDS)
            if ready_event is not None:
                ready_event.set()
            self._accept_loop(listener, workers, inflight, stop_event)
        finally:
            listener.close()
            drained = self._shutdown_workers(workers)
            if drained:
                self._unlink_owned_socket(bound_inode)
            elif bound_inode is not None:
                raise SupervisorTransportError(
                    "lifecycle workers exceeded the shutdown deadline; owned socket retained"
                )

    def _validate_socket_root(self) -> int:
        if os.name != "posix":
            raise SupervisorTransportError("runtime supervisor UDS requires a POSIX host")
        if self._path.parent != TRUSTED_SOCKET_ROOT:
            raise SupervisorTransportError(
                "supervisor socket must be directly under the fixed trusted root"
            )
        effective_uid = getattr(os, "geteuid", lambda: 0)()
        self._validate_directory_chain(TRUSTED_SOCKET_ROOT.parent, effective_uid)
        created_root = False
        try:
            TRUSTED_SOCKET_ROOT.mkdir(mode=0o750, parents=False, exist_ok=False)
            created_root = True
        except FileExistsError:
            pass
        if created_root and self._requires_group_access(effective_uid):
            if self._socket_access_gid is None:
                raise SupervisorTransportError(
                    "distinct lifecycle worker requires a dedicated filesystem group"
                )
            try:
                os.chown(TRUSTED_SOCKET_ROOT, -1, self._socket_access_gid)
                TRUSTED_SOCKET_ROOT.chmod(0o750)
            except OSError as exc:
                raise SupervisorTransportError(
                    "could not configure trusted socket-root group ownership"
                ) from exc
        self._validate_directory_chain(TRUSTED_SOCKET_ROOT, effective_uid)
        self._validate_peer_directory_access(effective_uid)
        if self._path.exists() or self._path.is_symlink():
            raise SupervisorTransportError("refusing to replace an existing socket path")
        address_family = getattr(socket, "AF_UNIX", None)
        if address_family is None:
            raise SupervisorTransportError("AF_UNIX is unavailable")
        return address_family

    def _requires_group_access(self, effective_uid: int) -> bool:
        return any(uid != effective_uid for uid in self._allowed_peer_uids)

    def _validate_peer_directory_access(self, effective_uid: int) -> None:
        info = TRUSTED_SOCKET_ROOT.lstat()
        if info.st_mode & 0o007:
            raise SupervisorTransportError(
                "trusted socket root must not be accessible to unrelated identities"
            )
        if not self._requires_group_access(effective_uid):
            return
        if self._socket_access_gid is None:
            raise SupervisorTransportError(
                "distinct lifecycle worker requires a dedicated filesystem group"
            )
        if info.st_gid != self._socket_access_gid or not info.st_mode & stat.S_IXGRP:
            raise SupervisorTransportError(
                "trusted socket root does not grant the configured lifecycle-worker group"
            )

    def _configure_filesystem_access(self) -> None:
        effective_uid = getattr(os, "geteuid", lambda: 0)()
        try:
            if self._requires_group_access(effective_uid):
                if self._socket_access_gid is None:
                    raise SupervisorTransportError(
                        "distinct lifecycle worker requires a dedicated filesystem group"
                    )
                os.chown(self._path, -1, self._socket_access_gid)
                self._path.chmod(0o660)
            else:
                self._path.chmod(0o600)
        except OSError as exc:
            raise SupervisorTransportError(
                "could not configure supervisor socket filesystem access"
            ) from exc

    @classmethod
    def _validate_directory_chain(cls, path: Path, effective_uid: int) -> None:
        if not path.is_absolute():
            raise SupervisorTransportError("trusted socket root chain must be absolute")
        current = Path(path.anchor)
        cls._validate_directory(current, effective_uid)
        for part in path.parts[1:]:
            current = current / part
            cls._validate_directory(current, effective_uid)

    @staticmethod
    def _validate_directory(path: Path, effective_uid: int) -> None:
        try:
            directory_stat = path.lstat()
        except FileNotFoundError as exc:
            raise SupervisorTransportError("trusted socket root ancestor is missing") from exc
        if stat.S_ISLNK(directory_stat.st_mode) or not stat.S_ISDIR(directory_stat.st_mode):
            raise SupervisorTransportError("trusted socket root ancestors must be real directories")
        if directory_stat.st_uid not in {0, effective_uid} or directory_stat.st_mode & 0o022:
            raise SupervisorTransportError(
                "trusted socket root ancestor has unsafe ownership or mode"
            )

    def _accept_loop(
        self,
        listener: socket.socket,
        workers: ThreadPoolExecutor,
        inflight: threading.BoundedSemaphore,
        stop_event: threading.Event | None,
    ) -> None:
        while stop_event is None or not stop_event.is_set():
            self._dispatch_connection(listener, workers, inflight)

    def _dispatch_connection(
        self,
        listener: socket.socket,
        workers: ThreadPoolExecutor,
        inflight: threading.BoundedSemaphore,
    ) -> None:
        if not inflight.acquire(timeout=ACCEPT_POLL_SECONDS):
            return
        try:
            connection, _ = listener.accept()
        except TimeoutError:
            inflight.release()
            return
        except OSError:
            inflight.release()
            raise
        try:
            future = workers.submit(self._serve_connection, connection)
        except RuntimeError:
            connection.close()
            inflight.release()
            raise
        self._track_worker(future, inflight)

    def _track_worker(self, future: Future[None], inflight: threading.BoundedSemaphore) -> None:
        with self._worker_futures_lock:
            self._worker_futures.add(future)

        def complete(done: Future[None]) -> None:
            with self._worker_futures_lock:
                self._worker_futures.discard(done)
            inflight.release()

        future.add_done_callback(complete)

    def _shutdown_workers(self, workers: ThreadPoolExecutor) -> bool:
        workers.shutdown(wait=False, cancel_futures=True)
        with self._worker_futures_lock:
            active = tuple(self._worker_futures)
        if not active:
            return True
        _done, pending = wait(active, timeout=self._worker_shutdown_timeout_seconds)
        if pending:
            return False
        workers.shutdown(wait=True, cancel_futures=True)
        return True

    def _serve_connection(self, connection: socket.socket) -> None:
        with connection:
            try:
                self.handle(connection)
            except (TimeoutError, BrokenPipeError, ConnectionError):
                return

    def _unlink_owned_socket(self, bound_inode: int | None) -> None:
        if bound_inode is None:
            return
        try:
            current = self._path.lstat()
            if stat.S_ISSOCK(current.st_mode) and current.st_ino == bound_inode:
                self._path.unlink()
        except FileNotFoundError:
            pass

    @staticmethod
    def _read_request(connection: socket.socket) -> bytes:
        payload = bytearray()
        while len(payload) <= MAX_REQUEST_BYTES:
            chunk = connection.recv(min(4096, MAX_REQUEST_BYTES + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
            if b"\n" in chunk:
                break
        if len(payload) > MAX_REQUEST_BYTES:
            raise SupervisorTransportError("request exceeds maximum size")
        line, separator, remainder = bytes(payload).partition(b"\n")
        if not separator or remainder or not line:
            raise SupervisorTransportError("request must be exactly one bounded JSON line")
        return line

    @staticmethod
    def _send(connection: socket.socket, payload: dict[str, object]) -> None:
        connection.sendall(json.dumps(payload, sort_keys=True).encode() + b"\n")
