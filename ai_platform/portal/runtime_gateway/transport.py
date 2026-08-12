from __future__ import annotations

import os
import socket
import socketserver
import stat
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ai_platform.portal.runtime_gateway.errors import GatewayError
from ai_platform.portal.runtime_gateway.gateway import RuntimeGateway
from ai_platform.portal.runtime_gateway.models import GatewayLimits, GatewayResponse
from ai_platform.portal.runtime_gateway.protocol import decode_request, encode_document


_AF_UNIX = getattr(socket, "AF_UNIX", -1)


class _BinaryReader(Protocol):
    def readline(self, size: int = -1) -> bytes: ...


@dataclass(frozen=True)
class PeerIdentity:
    pid: int
    uid: int
    gid: int


@dataclass(frozen=True)
class AllowedPeer:
    uid: int
    gid: int | None = None

    def permits(self, peer: PeerIdentity) -> bool:
        return peer.uid == self.uid and (self.gid is None or peer.gid == self.gid)


class RuntimeGatewayUnixServer(socketserver.TCPServer):
    """UDS-only listener with peer identity and socket substitution checks."""

    address_family = _AF_UNIX
    allow_reuse_address = False

    def __init__(
        self,
        socket_path: Path,
        gateway: RuntimeGateway,
        allowed_peer: AllowedPeer,
        limits: GatewayLimits | None = None,
    ) -> None:
        self.gateway = gateway
        self.allowed_peer = allowed_peer
        self.limits = limits or GatewayLimits()
        self._socket_path = _validate_socket_path(socket_path)
        self._bound_identity: tuple[int, int] | None = None
        super().__init__(
            str(self._socket_path),  # type: ignore[arg-type]
            _RequestHandler,
            bind_and_activate=False,
        )
        try:
            old_umask = os.umask(0o177)
            try:
                self.server_bind()
            finally:
                os.umask(old_umask)
            self._socket_path.chmod(0o600)
            info = self._socket_path.lstat()
            self._bound_identity = (info.st_dev, info.st_ino)
            self.server_activate()
        except BaseException:
            self.server_close()
            self._unlink_owned_socket()
            raise

    def verify_request(  # type: ignore[override]
        self, request: socket.socket, client_address: Any
    ) -> bool:
        del client_address
        try:
            self.assert_socket_identity()
            peer = _peer_identity(request)
            if not self.allowed_peer.permits(peer):
                raise GatewayError("CALLER_IDENTITY_MISMATCH", "OS peer identity is not authorized")
        except GatewayError as exc:
            _send_error(request, exc, self.limits.max_response_bytes)
            return False
        return True

    def assert_socket_identity(self) -> None:
        try:
            info = self._socket_path.lstat()
        except FileNotFoundError as exc:
            raise GatewayError("STALE_SOCKET", "Gateway socket path disappeared") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISSOCK(info.st_mode):
            raise GatewayError("SOCKET_SUBSTITUTION", "Gateway socket path was substituted")
        if (info.st_dev, info.st_ino) != self._bound_identity:
            raise GatewayError("SOCKET_SUBSTITUTION", "Gateway socket identity changed")

    def server_close(self) -> None:
        super().server_close()
        self._unlink_owned_socket()

    def _unlink_owned_socket(self) -> None:
        if self._bound_identity is None:
            return
        try:
            info = self._socket_path.lstat()
        except FileNotFoundError:
            return
        if (info.st_dev, info.st_ino) == self._bound_identity and stat.S_ISSOCK(info.st_mode):
            self._socket_path.unlink()


class _RequestHandler(socketserver.StreamRequestHandler):
    server: RuntimeGatewayUnixServer

    def handle(self) -> None:
        try:
            raw = _read_request_frame(self.rfile, self.server.limits.max_request_bytes)
        except GatewayError as exc:
            _send_error(
                self.request,
                exc,
                self.server.limits.max_response_bytes,
            )
            return
        try:
            self.server.assert_socket_identity()
            request = decode_request(raw)
            response = self.server.gateway.handle(request)
            encoded = encode_document(response.as_dict(), self.server.limits.max_response_bytes)
        except GatewayError as exc:
            encoded = _error_bytes(exc, self.server.limits.max_response_bytes)
        self.request.sendall(encoded)


def _read_request_frame(stream: _BinaryReader, limit: int) -> bytes:
    raw = stream.readline(limit + 2)
    if len(raw) > limit or not raw.endswith(b"\n"):
        raise GatewayError("REQUEST_TOO_LARGE", "request exceeds reviewed bound")
    return raw[:-1]


def _validate_socket_path(path: Path) -> Path:
    if not path.is_absolute():
        raise GatewayError("INVALID_SOCKET_PATH", "Gateway socket path must be absolute")
    parent = path.parent.resolve(strict=True)
    if path.exists() or path.is_symlink():
        raise GatewayError("STALE_SOCKET", "Gateway socket path already exists")
    info = parent.stat()
    if not stat.S_ISDIR(info.st_mode):
        raise GatewayError("INVALID_SOCKET_PATH", "Gateway socket parent is not a directory")
    get_effective_uid = getattr(os, "geteuid", None)
    if get_effective_uid is None:
        raise GatewayError("UDS_UNAVAILABLE", "POSIX ownership checks are required")
    if info.st_uid != get_effective_uid():
        raise GatewayError("SOCKET_DIRECTORY_OWNER_MISMATCH", "socket directory owner mismatch")
    if info.st_mode & 0o022:
        raise GatewayError(
            "SOCKET_DIRECTORY_PERMISSIONS", "socket directory is group/world writable"
        )
    return parent / path.name


def _peer_identity(connection: socket.socket) -> PeerIdentity:
    if not hasattr(socket, "SO_PEERCRED"):
        raise GatewayError("PEER_CREDENTIALS_UNAVAILABLE", "SO_PEERCRED is required")
    raw = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    pid, uid, gid = struct.unpack("3i", raw)
    return PeerIdentity(pid=pid, uid=uid, gid=gid)


def _error_bytes(error: GatewayError, max_bytes: int) -> bytes:
    response = GatewayResponse(
        request_id="unknown",
        generation_id="unknown",
        operation="unknown",
        ok=False,
        authoritative=False,
        error={"code": error.code, "message": error.message},
    )
    return encode_document(response.as_dict(), max_bytes)


def _send_error(connection: socket.socket, error: GatewayError, max_bytes: int) -> None:
    try:
        connection.sendall(_error_bytes(error, max_bytes))
    except OSError:
        pass
