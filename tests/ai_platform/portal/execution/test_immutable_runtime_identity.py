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


class _Runner:
    def __init__(self, *results: CommandResult) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: Sequence[str], *, timeout_seconds: float | None = None) -> CommandResult:
        del timeout_seconds
        self.calls.append(tuple(args))
        if not self.results:
            raise AssertionError(f"unexpected command: {tuple(args)!r}")
        return self.results.pop(0)


def _container_identity(container_id: str) -> CommandResult:
    return CommandResult(
        0,
        stdout=json.dumps(
            {
                "Id": container_id,
                "Config": {"Labels": {"ai.portal.runtime_id": "runtime-1"}},
            }
        ),
    )


@pytest.mark.parametrize("operation", ["inspect", "pause", "stop", "retire"])
def test_container_replacement_with_matching_label_is_rejected(operation: str) -> None:
    runner = _Runner(_container_identity("replacement-id"))
    driver = DockerCliRuntimeDriver(runner)
    driver._container_ids["runtime-1"] = "expected-id"

    with pytest.raises(RuntimeDriverError) as exc_info:
        getattr(driver, operation)("runtime-1")

    assert exc_info.value.reason_code == "GENERATION_OWNERSHIP_CONFLICT"
    assert runner.calls == [("docker", "inspect", "--format", "{{json .}}", "runtime-1")]


def test_network_replacement_with_matching_label_is_rejected(tmp_path: Path) -> None:
    runner = _Runner(
        CommandResult(
            0,
            stdout=json.dumps(
                {
                    "Id": "replacement-network-id",
                    "Labels": {"ai.portal.runtime_id": "runtime-1"},
                }
            ),
        )
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=MappingMarketDataEgressPolicyProvider({}),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )
    backend._network_ids["runtime-1"] = "expected-network-id"

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.cleanup_network("portal-net-1", "runtime-1")

    assert exc_info.value.reason_code == "GENERATION_OWNERSHIP_CONFLICT"
    assert runner.calls == [
        ("docker", "network", "inspect", "--format", "{{json .}}", "portal-net-1")
    ]
