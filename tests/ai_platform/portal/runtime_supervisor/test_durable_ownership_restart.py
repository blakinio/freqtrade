from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from ai_platform.portal.execution.driver import CommandResult, DockerCliRuntimeDriver
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.host_isolation import (
    LinuxNftablesBtrfsIsolationAttestor,
    MappingMarketDataEgressPolicyProvider,
)
from ai_platform.portal.runtime_supervisor.service import SqliteCommandJournal


class _Runner:
    def __init__(self, *results: CommandResult) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, ...]] = []

    def run(
        self,
        args: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> CommandResult:
        del timeout_seconds
        self.calls.append(tuple(args))
        if not self.results:
            raise AssertionError(f"unexpected command: {tuple(args)!r}")
        return self.results.pop(0)


def test_sqlite_immutable_ownership_survives_restart(tmp_path: Path) -> None:
    path = tmp_path / "supervisor.sqlite3"
    journal = SqliteCommandJournal(path)
    assert journal.bind_container_id("runtime-1", "container-id")
    assert journal.bind_network_id("runtime-1", "network-id")

    restarted = SqliteCommandJournal(path)
    assert restarted.container_id("runtime-1") == "container-id"
    assert restarted.network_id("runtime-1") == "network-id"
    assert not restarted.bind_container_id("runtime-1", "replacement-container")
    assert not restarted.bind_network_id("runtime-1", "replacement-network")


def test_fresh_driver_rejects_same_label_name_replacement(tmp_path: Path) -> None:
    journal = SqliteCommandJournal(tmp_path / "supervisor.sqlite3")
    assert journal.bind_container_id("runtime-1", "expected-container-id")
    runner = _Runner(
        CommandResult(
            1,
            stderr="Error response from daemon: No such object: expected-container-id",
        ),
        CommandResult(
            0,
            stdout=json.dumps(
                {
                    "Id": "replacement-container-id",
                    "Config": {"Labels": {"ai.portal.runtime_id": "runtime-1"}},
                }
            ),
        ),
    )
    driver = DockerCliRuntimeDriver(runner)
    driver.bind_ownership_store(journal)

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.inspect("runtime-1")

    assert exc_info.value.reason_code == "GENERATION_OWNERSHIP_CONFLICT"
    assert journal.container_id("runtime-1") == "expected-container-id"
    assert runner.calls == [
        ("docker", "inspect", "--format", "{{json .}}", "expected-container-id"),
        ("docker", "inspect", "--format", "{{json .}}", "runtime-1"),
    ]


def test_fresh_network_attestor_rejects_same_name_replacement(tmp_path: Path) -> None:
    journal = SqliteCommandJournal(tmp_path / "supervisor.sqlite3")
    assert journal.bind_network_id("runtime-1", "expected-network-id")
    runner = _Runner(
        CommandResult(
            1,
            stderr="Error response from daemon: network expected-network-id not found",
        ),
        CommandResult(
            0,
            stdout=json.dumps(
                {
                    "Id": "replacement-network-id",
                    "Labels": {"ai.portal.runtime_id": "runtime-1"},
                }
            ),
        ),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=MappingMarketDataEgressPolicyProvider({}),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )
    backend.bind_ownership_store(journal)

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.cleanup_network("portal-net-1", "runtime-1")

    assert exc_info.value.reason_code == "GENERATION_OWNERSHIP_CONFLICT"
    assert journal.network_id("runtime-1") == "expected-network-id"
    assert runner.calls == [
        (
            "docker",
            "network",
            "inspect",
            "--format",
            "{{json .}}",
            "expected-network-id",
        ),
        (
            "docker",
            "network",
            "inspect",
            "--format",
            "{{json .}}",
            "portal-net-1",
        ),
    ]
