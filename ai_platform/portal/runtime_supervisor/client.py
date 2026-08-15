from __future__ import annotations

import socket
import stat
from pathlib import Path

from pydantic import ValidationError

from .transport import MAX_REQUEST_BYTES, REQUEST_TIMEOUT_SECONDS, TRUSTED_SOCKET_ROOT
from .types import SupervisorOutcome, SupervisorRequest


MAX_RESPONSE_BYTES = 32 * 1024


class SupervisorClientError(RuntimeError):
    pass


class UnixSocketSupervisorClient:
    """Least-privilege local client for the Runtime Supervisor.

    It can speak only the fixed SupervisorRequest contract over a trusted local UDS;
    it owns no Docker/container-engine handle and has no network endpoint fallback.
    """

    def __init__(self, path: Path, *, timeout_seconds: float = REQUEST_TIMEOUT_SECONDS) -> None:
        if path.parent != TRUSTED_SOCKET_ROOT:
            raise ValueError("supervisor socket must be directly under the trusted root")
        if not 0 < timeout_seconds <= REQUEST_TIMEOUT_SECONDS:
            raise ValueError("supervisor timeout exceeds the bounded transport limit")
        self._path = path
        self._timeout_seconds = timeout_seconds

    def execute(self, request: SupervisorRequest) -> SupervisorOutcome:
        self._validate_socket()
        payload = request.model_dump_json().encode() + b"\n"
        if len(payload) > MAX_REQUEST_BYTES:
            raise SupervisorClientError("supervisor request exceeds transport limit")
        family = getattr(socket, "AF_UNIX", None)
        if family is None:
            raise SupervisorClientError("AF_UNIX is unavailable")
        try:
            with socket.socket(family, socket.SOCK_STREAM) as connection:
                connection.settimeout(self._timeout_seconds)
                connection.connect(str(self._path))
                connection.sendall(payload)
                response = self._read_response(connection)
        except (OSError, TimeoutError) as exc:
            raise SupervisorClientError("runtime supervisor transport failed") from exc
        try:
            return SupervisorOutcome.model_validate_json(response)
        except ValidationError as exc:
            raise SupervisorClientError("runtime supervisor returned an invalid outcome") from exc

    def _validate_socket(self) -> None:
        try:
            info = self._path.lstat()
            root_info = TRUSTED_SOCKET_ROOT.lstat()
        except FileNotFoundError as exc:
            raise SupervisorClientError("runtime supervisor socket is unavailable") from exc
        if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
            raise SupervisorClientError("trusted supervisor root is invalid")
        if root_info.st_mode & 0o007:
            raise SupervisorClientError("trusted supervisor root is accessible to unrelated identities")
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISSOCK(info.st_mode):
            raise SupervisorClientError("runtime supervisor endpoint is not a real socket")
        if info.st_mode & 0o007:
            raise SupervisorClientError("runtime supervisor socket is accessible to unrelated identities")

    @staticmethod
    def _read_response(connection: socket.socket) -> bytes:
        payload = bytearray()
        while len(payload) <= MAX_RESPONSE_BYTES:
            chunk = connection.recv(min(4096, MAX_RESPONSE_BYTES + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
            if b"\n" in chunk:
                break
        if len(payload) > MAX_RESPONSE_BYTES:
            raise SupervisorClientError("supervisor response exceeds transport limit")
        line, separator, remainder = bytes(payload).partition(b"\n")
        if not separator or remainder or not line:
            raise SupervisorClientError("supervisor response must be exactly one JSON line")
        return line
