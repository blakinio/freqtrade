from __future__ import annotations

import json
import os
import socket
import stat
import threading
from io import BytesIO
from pathlib import Path

import pytest

from ai_platform.portal.runtime_gateway.contract import bundled_contract_digest
from ai_platform.portal.runtime_gateway.errors import GatewayError
from ai_platform.portal.runtime_gateway.gateway import RuntimeGateway
from ai_platform.portal.runtime_gateway.models import CONTRACT_VERSION, GatewayBinding
from ai_platform.portal.runtime_gateway.transport import (
    AllowedPeer,
    PeerIdentity,
    RuntimeGatewayUnixServer,
    _read_request_frame,
    _validate_socket_path,
)


class _FakeUpstream:
    def get(self, endpoint: str) -> object:
        return {"endpoint": endpoint, "status": "ok"}


def _gateway() -> RuntimeGateway:
    return RuntimeGateway(
        GatewayBinding(
            tenant_id="tenant-1",
            bot_id="bot-1",
            generation_id="generation-42",
            mode="PAPER",
            gateway_artifact_digest=f"sha256:{'a' * 64}",
            gateway_contract_version=CONTRACT_VERSION,
            gateway_contract_digest=bundled_contract_digest(),
        ),
        _FakeUpstream(),
    )


def test_wrong_caller_identity_is_denied() -> None:
    allowed = AllowedPeer(uid=1000, gid=1000)
    assert not allowed.permits(PeerIdentity(pid=1, uid=1001, gid=1000))
    assert not allowed.permits(PeerIdentity(pid=1, uid=1000, gid=1001))
    assert allowed.permits(PeerIdentity(pid=1, uid=1000, gid=1000))


def test_excessive_request_body_is_rejected_before_json_decode() -> None:
    with pytest.raises(GatewayError) as error:
        _read_request_frame(BytesIO(b"x" * 257 + b"\n"), 256)
    assert error.value.code == "REQUEST_TOO_LARGE"


def test_stale_socket_and_symlink_are_rejected(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("Unix ownership and socket mode checks require POSIX")
    socket_path = tmp_path / "gateway.sock"
    socket_path.write_text("stale", encoding="utf-8")
    with pytest.raises(GatewayError) as stale:
        _validate_socket_path(socket_path)
    assert stale.value.code == "STALE_SOCKET"
    socket_path.unlink()
    socket_path.symlink_to(tmp_path / "missing")
    with pytest.raises(GatewayError) as symlink:
        _validate_socket_path(socket_path)
    assert symlink.value.code == "STALE_SOCKET"


def test_socket_parent_must_not_be_group_or_world_writable(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("Unix ownership and socket mode checks require POSIX")
    tmp_path.chmod(0o777)
    with pytest.raises(GatewayError) as error:
        _validate_socket_path(tmp_path / "gateway.sock")
    assert error.value.code == "SOCKET_DIRECTORY_PERMISSIONS"


def test_transport_has_no_tcp_or_browser_listener_surface() -> None:
    af_unix = getattr(socket, "AF_UNIX", -1)
    assert RuntimeGatewayUnixServer.address_family == af_unix
    assert RuntimeGatewayUnixServer.address_family != socket.AF_INET
    assert RuntimeGatewayUnixServer.address_family != socket.AF_INET6
    assert stat.S_IFSOCK != stat.S_IFREG


def test_generation_scoped_uds_round_trip(tmp_path: Path) -> None:
    if os.name == "nt" or not hasattr(socket, "SO_PEERCRED"):
        pytest.skip("Linux SO_PEERCRED integration")
    socket_path = tmp_path / "gateway.sock"
    server = RuntimeGatewayUnixServer(
        socket_path,
        _gateway(),
        AllowedPeer(
            uid=os.geteuid(),  # type: ignore[attr-defined]
            gid=os.getegid(),  # type: ignore[attr-defined]
        ),
    )
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    connection = socket.socket(RuntimeGatewayUnixServer.address_family, socket.SOCK_STREAM)
    try:
        connection.connect(str(socket_path))
        connection.sendall(
            json.dumps(
                {
                    "contract_version": CONTRACT_VERSION,
                    "tenant_id": "tenant-1",
                    "bot_id": "bot-1",
                    "generation_id": "generation-42",
                    "request_id": "request-uds",
                    "operation": "health",
                    "body": {},
                }
            ).encode()
            + b"\n"
        )
        response = json.loads(connection.makefile("rb").readline())
    finally:
        connection.close()
        thread.join(timeout=2)
        server.server_close()
    assert response["ok"] is True
    assert response["generation_id"] == "generation-42"
    assert not socket_path.exists()
