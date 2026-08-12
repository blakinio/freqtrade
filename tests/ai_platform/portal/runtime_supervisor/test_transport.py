from __future__ import annotations

import json
import socket
import threading
from pathlib import Path
from uuid import uuid4

import pytest

from ai_platform.portal.runtime_supervisor import SupervisorRequest
from ai_platform.portal.runtime_supervisor.transport import (
    SupervisorTransportError,
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
        Path("/run/quant-platform/supervisor.sock"),
        supervisor,
        allowed_peer_uids=frozenset({42}),
        peer_uid=lambda _: 7,
    )
    assert exchange(server, b'{"malformed":true}\n')["code"] == "PEER_NOT_AUTHORIZED"
    assert supervisor.requests == []


def test_raw_engine_fields_are_rejected_at_transport_boundary() -> None:
    supervisor = Supervisor()
    server = UnixSocketSupervisorServer(
        Path("/run/quant-platform/supervisor.sock"),
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


def _valid_payload(bot_id: str) -> bytes:
    request = SupervisorRequest.model_validate(
        {
            "tenant_id": "tenant-1",
            "bot_id": bot_id,
            "generation_id": "gen-1",
            "generation_spec_digest": "a" * 64,
            "operation": "InspectGeneration",
            "command_id": uuid4(),
            "expected_generation_ordinal": 1,
            "expected_state_version": 1,
            "correlation_id": uuid4(),
        }
    )
    return request.model_dump_json().encode() + b"\n"


def test_accept_loop_remains_responsive_while_other_lifecycle_handler_is_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not hasattr(socket, "AF_UNIX"):
        return

    class BlockingSupervisor(Supervisor):
        def __init__(self) -> None:
            super().__init__()
            self.blocked_started = threading.Event()
            self.release_blocked = threading.Event()

        def execute(self, request: SupervisorRequest) -> Result:
            self.requests.append(request)
            if request.bot_id == "bot-1":
                self.blocked_started.set()
                assert self.release_blocked.wait(2)
            return Result()

    root = tmp_path / "runtime-supervisor"
    root.mkdir(mode=0o750)
    path = root / "supervisor.sock"
    supervisor = BlockingSupervisor()
    server = UnixSocketSupervisorServer(
        path,
        supervisor,
        allowed_peer_uids=frozenset({42}),
        peer_uid=lambda _: 42,
        max_workers=2,
        max_inflight_connections=2,
    )
    monkeypatch.setattr(server, "_validate_socket_root", lambda: socket.AF_UNIX)
    stop_event = threading.Event()
    ready_event = threading.Event()
    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"stop_event": stop_event, "ready_event": ready_event},
        daemon=True,
    )
    thread.start()
    assert ready_event.wait(1)
    assert path.exists()

    first = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    second = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        first.settimeout(2)
        second.settimeout(1)
        first.connect(str(path))
        first.sendall(_valid_payload("bot-1"))
        assert supervisor.blocked_started.wait(1)

        second.connect(str(path))
        second.sendall(_valid_payload("bot-2"))
        assert json.loads(second.recv(65536))["accepted"] is True

        supervisor.release_blocked.set()
        assert json.loads(first.recv(65536))["accepted"] is True
    finally:
        supervisor.release_blocked.set()
        first.close()
        second.close()
        stop_event.set()
        thread.join(timeout=2)

    assert not thread.is_alive()
    assert {request.bot_id for request in supervisor.requests} == {"bot-1", "bot-2"}


def test_directory_validation_rejects_symlink_and_writable_directory(tmp_path: Path) -> None:
    safe = tmp_path / "safe"
    safe.mkdir(mode=0o750)
    symlink = tmp_path / "link"
    symlink.symlink_to(safe, target_is_directory=True)
    with __import__("pytest").raises(SupervisorTransportError):
        UnixSocketSupervisorServer._validate_directory(symlink, __import__("os").geteuid())

    writable = tmp_path / "writable"
    writable.mkdir(mode=0o777)
    writable.chmod(0o777)
    with __import__("pytest").raises(SupervisorTransportError):
        UnixSocketSupervisorServer._validate_directory(writable, __import__("os").geteuid())


def test_shutdown_is_bounded_and_retains_socket_for_hung_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not hasattr(socket, "AF_UNIX"):
        return

    class HungSupervisor(Supervisor):
        def __init__(self) -> None:
            super().__init__()
            self.started = threading.Event()
            self.release = threading.Event()

        def execute(self, request: SupervisorRequest) -> Result:
            self.requests.append(request)
            self.started.set()
            assert self.release.wait(2)
            return Result()

    root = tmp_path / "runtime-supervisor-shutdown"
    root.mkdir(mode=0o750)
    path = root / "supervisor.sock"
    supervisor = HungSupervisor()
    server = UnixSocketSupervisorServer(
        path,
        supervisor,
        allowed_peer_uids=frozenset({42}),
        peer_uid=lambda _: 42,
        max_workers=1,
        max_inflight_connections=1,
        worker_shutdown_timeout_seconds=0.05,
    )
    monkeypatch.setattr(server, "_validate_socket_root", lambda: socket.AF_UNIX)
    stop_event = threading.Event()
    ready_event = threading.Event()
    errors: list[BaseException] = []

    def run_server() -> None:
        try:
            server.serve_forever(stop_event=stop_event, ready_event=ready_event)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    assert ready_event.wait(1)
    assert path.exists()

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(str(path))
        client.sendall(_valid_payload("bot-hung"))
        assert supervisor.started.wait(1)
        stop_event.set()
        thread.join(timeout=0.5)
        assert not thread.is_alive()
        assert errors and isinstance(errors[0], SupervisorTransportError)
        assert path.exists()
    finally:
        supervisor.release.set()
        client.close()
        if path.exists():
            path.unlink()
