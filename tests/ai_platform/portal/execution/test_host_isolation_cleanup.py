from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from ai_platform.portal.execution.driver import CommandResult
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.host_isolation import (
    LinuxNftablesBtrfsIsolationAttestor,
    MappingMarketDataEgressPolicyProvider,
)


class _Runner:
    def __init__(self, *results: CommandResult) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: Sequence[str]) -> CommandResult:
        self.calls.append(tuple(args))
        if not self.results:
            raise AssertionError(f"unexpected command: {tuple(args)!r}")
        return self.results.pop(0)


def _backend(runner: _Runner, tmp_path: Path) -> LinuxNftablesBtrfsIsolationAttestor:
    return LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=MappingMarketDataEgressPolicyProvider({}),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )


def test_cleanup_attempts_docker_network_after_nft_failure(tmp_path: Path) -> None:
    runner = _Runner(
        CommandResult(1, stderr="nft backend unavailable"),
        CommandResult(1, stderr="daemon unavailable"),
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        _backend(runner, tmp_path).cleanup_network("portal-net-1", "runtime-1")

    assert exc_info.value.reason_code == "HOST_NETWORK_CLEANUP_FAILED"
    assert runner.calls[0][:4] == ("nft", "delete", "table", "inet")
    assert runner.calls[1] == ("docker", "network", "rm", "portal-net-1")


def test_cleanup_is_idempotent_when_resources_are_already_absent(tmp_path: Path) -> None:
    runner = _Runner(
        CommandResult(1, stderr="Error: No such file or directory"),
        CommandResult(1, stderr="Error response from daemon: network portal-net-1 not found"),
    )

    _backend(runner, tmp_path).cleanup_network("portal-net-1", "runtime-1")

    assert len(runner.calls) == 2
