from __future__ import annotations

import json
import socket
from pathlib import Path

from ai_platform.portal.runtime_supervisor import SupervisorRequest
from ai_platform.portal.runtime_supervisor.transport import (
    UnixSocketSupervisorServer,
    linux_peer_uid,
)


class Result:
    def model_dump_json(self) -> str:
        return '{"accepted":true}'


class Supervisor:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def execute(self, request: SupervisorRequest) -> Result:
        self.requests.append(request)
        return Result()


def exchange(server: UnixSocketSupervisorServer, payload: bytes) -> dict[str, object]:
    client, accepted = socket.socketpair()
    try:
        client.sendall(payload)
        client.shutdown(socket.SHUT_WR)
        server.handle(accepted)
        return json.loads(client.recv(65536))
    finally:
        client.close()
        accepted.close()


def test_unauthorized_peer_is_rejected_before_parsing() -> None:
    supervisor = Supervisor()
    server = UnixSocketSupervisorServer(
        Path("/run/supervisor.sock"),
        supervisor,
        allowed_peer_uids=frozenset({42}),
        peer_uid=lambda _: 7,
    )
    assert exchange(server, b'{"malformed":true}\n')["code"] == "PEER_NOT_AUTHORIZED"
    assert supervisor.requests == []


def test_raw_engine_fields_are_rejected_at_transport_boundary() -> None:
    supervisor = Supervisor()
    server = UnixSocketSupervisorServer(
        Path("/run/supervisor.sock"),
        supervisor,
        allowed_peer_uids=frozenset({42}),
        peer_uid=lambda _: 42,
    )
    assert exchange(server, b'{"image":"evil:latest"}\n')["code"] == "INVALID_REQUEST"
    assert supervisor.requests == []


def test_linux_peer_uid_uses_kernel_authenticated_credentials() -> None:
    if not hasattr(socket, "SO_PEERCRED"):
        return
    client, accepted = socket.socketpair()
    try:
        assert linux_peer_uid(accepted) == __import__("os").getuid()
    finally:
        client.close()
        accepted.close()
