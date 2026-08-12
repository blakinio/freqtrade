from __future__ import annotations

import json
import os
import socket
import struct
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from .types import SupervisorRequest


MAX_REQUEST_BYTES = 16 * 1024


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
    ) -> None:
        if not path.is_absolute() and not str(path).replace("\\", "/").startswith("/"):
            raise ValueError("supervisor socket path must be absolute")
        if not allowed_peer_uids or any(uid < 0 for uid in allowed_peer_uids):
            raise ValueError("at least one valid peer uid is required")
        self._path = path
        self._supervisor = supervisor
        self._allowed_peer_uids = allowed_peer_uids
        self._peer_uid = peer_uid

    def handle(self, connection: socket.socket) -> None:
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
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists() or self._path.is_symlink():
            raise SupervisorTransportError("refusing to replace an existing socket path")
        address_family = getattr(socket, "AF_UNIX", None)
        if address_family is None:
            raise SupervisorTransportError("AF_UNIX is unavailable")
        listener = socket.socket(address_family, socket.SOCK_STREAM)
        try:
            listener.bind(str(self._path))
            self._path.chmod(0o660)
            listener.listen(16)
            while True:
                connection, _ = listener.accept()
                with connection:
                    self.handle(connection)
        finally:
            listener.close()

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
