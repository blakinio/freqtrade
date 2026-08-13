from __future__ import annotations

import json
import os
import socket
import stat
import threading
from concurrent.futures import Future
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


def test_distinct_peer_requires_dedicated_filesystem_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not hasattr(socket, "AF_UNIX"):
        return
    path = tmp_path / "supervisor.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    try:
        distinct_uid = os.geteuid() + 1
        missing_group = UnixSocketSupervisorServer(
            path,
            Supervisor(),
            allowed_peer_uids=frozenset({distinct_uid}),
            peer_uid=lambda _: distinct_uid,
        )
        with pytest.raises(SupervisorTransportError, match="dedicated filesystem group"):
            missing_group._configure_filesystem_access()

        chowns: list[tuple[Path, int, int]] = []
        monkeypatch.setattr(
            os,
            "chown",
            lambda target, uid, gid: chowns.append((Path(target), uid, gid)),
        )
        configured = UnixSocketSupervisorServer(
            path,
            Supervisor(),
            allowed_peer_uids=frozenset({distinct_uid}),
            peer_uid=lambda _: distinct_uid,
            socket_access_gid=os.getegid(),
        )
        configured._configure_filesystem_access()
        assert stat.S_IMODE(path.lstat().st_mode) == 0o660
        assert chowns == [(path, -1, os.getegid())]
    finally:
        listener.close()
        if path.exists():
            path.unlink()


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
                assert self.release_blocked.wait(10)
            return Result()

    root = tmp_path / "runtime-supervisor"
    root.mkdir(mode=0o750)
    path = root / "supervisor.sock"
    supervisor = BlockingSupervisor()
    authorized_uid = os.geteuid()
    server = UnixSocketSupervisorServer(
        path,
        supervisor,
        allowed_peer_uids=frozenset({authorized_uid}),
        peer_uid=lambda _: authorized_uid,
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
    assert ready_event.wait(5)
    assert path.exists()

    first = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    second = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        first.settimeout(5)
        second.settimeout(5)
        first.connect(str(path))
        first.sendall(_valid_payload("bot-1"))
        assert supervisor.blocked_started.wait(5)

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
        thread.join(timeout=5)

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

    root = tmp_path / "runtime-supervisor-shutdown"
    root.mkdir(mode=0o750)
    path = root / "supervisor.sock"
    authorized_uid = os.geteuid()
    server = UnixSocketSupervisorServer(
        path,
        Supervisor(),
        allowed_peer_uids=frozenset({authorized_uid}),
        peer_uid=lambda _: authorized_uid,
        max_workers=1,
        max_inflight_connections=1,
        worker_shutdown_timeout_seconds=0.05,
    )
    monkeypatch.setattr(server, "_validate_socket_root", lambda: socket.AF_UNIX)

    pending: Future[None] = Future()
    shutdown_workers = server._shutdown_workers

    def shutdown_with_pending_worker(workers: object) -> bool:
        with server._worker_futures_lock:
            server._worker_futures.add(pending)
        return shutdown_workers(workers)  # type: ignore[arg-type]

    monkeypatch.setattr(server, "_shutdown_workers", shutdown_with_pending_worker)
    stop_event = threading.Event()
    stop_event.set()

    try:
        with pytest.raises(SupervisorTransportError, match="shutdown deadline"):
            server.serve_forever(stop_event=stop_event)
        assert path.exists()
    finally:
        pending.set_result(None)
        if path.exists():
            path.unlink()
