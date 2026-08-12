from __future__ import annotations

import os
import socket
import socketserver
import stat
import struct
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
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
        self._socket_path = _validate_socket_path(socket_path, allowed_peer)
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
            _grant_peer_filesystem_access(self._socket_path, allowed_peer)
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
            _send_error(
                request,
                exc,
                self.limits.max_response_bytes,
                self.limits.io_timeout_seconds,
            )
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
            raw = _read_socket_frame(
                self.request,
                self.server.limits.max_request_bytes,
                self.server.limits.io_timeout_seconds,
            )
        except GatewayError as exc:
            _send_error(
                self.request,
                exc,
                self.server.limits.max_response_bytes,
                self.server.limits.io_timeout_seconds,
            )
            return
        try:
            self.server.assert_socket_identity()
            request = decode_request(raw)
            response = self.server.gateway.handle(request)
            encoded = encode_document(response.as_dict(), self.server.limits.max_response_bytes)
        except GatewayError as exc:
            encoded = _error_bytes(exc, self.server.limits.max_response_bytes)
        _send_bounded(self.request, encoded, self.server.limits.io_timeout_seconds)


def _read_request_frame(stream: _BinaryReader, limit: int) -> bytes:
    """Bounded pure-reader helper retained for deterministic unit validation."""

    raw = stream.readline(limit + 2)
    if len(raw) > limit or not raw.endswith(b"\n"):
        raise GatewayError("REQUEST_TOO_LARGE", "request exceeds reviewed bound")
    return raw[:-1]


def _read_socket_frame(connection: socket.socket, limit: int, timeout_seconds: float) -> bytes:
    deadline = monotonic() + timeout_seconds
    payload = bytearray()
    while True:
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise GatewayError(
                "REQUEST_TIMEOUT", "request did not complete within reviewed deadline"
            )
        connection.settimeout(remaining)
        try:
            chunk = connection.recv(min(4096, limit + 2 - len(payload)))
        except TimeoutError as exc:
            raise GatewayError(
                "REQUEST_TIMEOUT", "request did not complete within reviewed deadline"
            ) from exc
        except OSError as exc:
            raise GatewayError("REQUEST_IO_ERROR", "request transport failed") from exc
        if not chunk:
            raise GatewayError("MALFORMED_REQUEST", "request ended before frame terminator")
        payload.extend(chunk)
        newline = payload.find(b"\n")
        if newline >= 0:
            if newline > limit:
                raise GatewayError("REQUEST_TOO_LARGE", "request exceeds reviewed bound")
            if newline != len(payload) - 1:
                raise GatewayError("MALFORMED_REQUEST", "request contains trailing frame data")
            return bytes(payload[:newline])
        if len(payload) > limit:
            raise GatewayError("REQUEST_TOO_LARGE", "request exceeds reviewed bound")


def _send_bounded(connection: socket.socket, payload: bytes, timeout_seconds: float) -> None:
    deadline = monotonic() + timeout_seconds
    view = memoryview(payload)
    while view:
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise GatewayError("RESPONSE_TIMEOUT", "response exceeded reviewed write deadline")
        connection.settimeout(remaining)
        try:
            sent = connection.send(view)
        except TimeoutError as exc:
            raise GatewayError(
                "RESPONSE_TIMEOUT", "response exceeded reviewed write deadline"
            ) from exc
        except OSError as exc:
            raise GatewayError("RESPONSE_IO_ERROR", "response transport failed") from exc
        if sent <= 0:
            raise GatewayError("RESPONSE_IO_ERROR", "response transport closed")
        view = view[sent:]


def _validate_socket_path(path: Path, allowed_peer: AllowedPeer | None = None) -> Path:
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
    effective_uid = get_effective_uid()
    peer = allowed_peer or AllowedPeer(uid=effective_uid)
    if info.st_uid != effective_uid:
        raise GatewayError("SOCKET_DIRECTORY_OWNER_MISMATCH", "socket directory owner mismatch")
    if info.st_mode & 0o022:
        raise GatewayError(
            "SOCKET_DIRECTORY_PERMISSIONS", "socket directory is group/world writable"
        )
    if info.st_mode & 0o007:
        raise GatewayError("SOCKET_DIRECTORY_PERMISSIONS", "socket directory is world accessible")
    if peer.uid != effective_uid:
        if peer.gid is None:
            raise GatewayError(
                "SOCKET_PEER_ACCESS_UNCONFIGURED",
                "distinct worker identity requires a dedicated filesystem group",
            )
        if info.st_gid != peer.gid:
            raise GatewayError(
                "SOCKET_DIRECTORY_GROUP_MISMATCH", "socket directory group does not match worker"
            )
        if not info.st_mode & stat.S_IXGRP:
            raise GatewayError(
                "SOCKET_DIRECTORY_PEER_ACCESS",
                "socket directory does not grant worker-group traversal",
            )
    return parent / path.name


def _grant_peer_filesystem_access(path: Path, allowed_peer: AllowedPeer) -> None:
    get_effective_uid = getattr(os, "geteuid", None)
    if get_effective_uid is None:
        raise GatewayError("UDS_UNAVAILABLE", "POSIX ownership checks are required")
    effective_uid = get_effective_uid()
    if allowed_peer.uid == effective_uid:
        path.chmod(0o600)
        return
    if allowed_peer.gid is None:
        raise GatewayError(
            "SOCKET_PEER_ACCESS_UNCONFIGURED",
            "distinct worker identity requires a dedicated filesystem group",
        )
    try:
        os.chown(path, -1, allowed_peer.gid)
        path.chmod(0o660)
    except OSError as exc:
        raise GatewayError(
            "SOCKET_PEER_ACCESS_FAILED", "could not grant configured worker filesystem access"
        ) from exc


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


def _send_error(
    connection: socket.socket,
    error: GatewayError,
    max_bytes: int,
    timeout_seconds: float,
) -> None:
    try:
        _send_bounded(connection, _error_bytes(error, max_bytes), timeout_seconds)
    except (GatewayError, OSError):
        pass
