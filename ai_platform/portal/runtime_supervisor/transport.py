from __future__ import annotations

import json
import os
import socket
import stat
import struct
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from .types import SupervisorRequest


MAX_REQUEST_BYTES = 16 * 1024
REQUEST_TIMEOUT_SECONDS = 5.0


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
        approved_root: Path = Path("/run/quant-platform"),
        peer_uid: Callable[[socket.socket], int] = linux_peer_uid,
    ) -> None:
        normalized_path = str(path).replace("\\", "/")
        normalized_root = str(approved_root).replace("\\", "/")
        if not path.is_absolute() and not normalized_path.startswith("/"):
            raise ValueError("supervisor socket path must be absolute")
        if (
            not approved_root.is_absolute() and not normalized_root.startswith("/")
        ) or normalized_path.rsplit("/", 1)[0] != normalized_root.rstrip("/"):
            raise ValueError("supervisor socket must be directly under the approved root")
        if not allowed_peer_uids or any(uid < 0 for uid in allowed_peer_uids):
            raise ValueError("at least one valid peer uid is required")
        self._path = path
        self._supervisor = supervisor
        self._allowed_peer_uids = allowed_peer_uids
        self._peer_uid = peer_uid
        self._approved_root = approved_root

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

    def serve_forever(self) -> None:
        if os.name != "posix":
            raise SupervisorTransportError("runtime supervisor UDS requires a POSIX host")
        self._approved_root.mkdir(parents=True, mode=0o750, exist_ok=True)
        root_stat = self._approved_root.lstat()
        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
            raise SupervisorTransportError("approved socket root must be a real directory")
        effective_uid = getattr(os, "geteuid", lambda: root_stat.st_uid)()
        if root_stat.st_uid != effective_uid or root_stat.st_mode & 0o022:
            raise SupervisorTransportError("approved socket root has unsafe ownership or mode")
        if self._path.exists() or self._path.is_symlink():
            raise SupervisorTransportError("refusing to replace an existing socket path")
        address_family = getattr(socket, "AF_UNIX", None)
        if address_family is None:
            raise SupervisorTransportError("AF_UNIX is unavailable")
        listener = socket.socket(address_family, socket.SOCK_STREAM)
        bound_inode: int | None = None
        try:
            listener.bind(str(self._path))
            bound_inode = self._path.lstat().st_ino
            self._path.chmod(0o660)
            listener.listen(16)
            while True:
                connection, _ = listener.accept()
                with connection:
                    try:
                        self.handle(connection)
                    except (TimeoutError, BrokenPipeError, ConnectionError):
                        continue
        finally:
            listener.close()
            if bound_inode is not None:
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
