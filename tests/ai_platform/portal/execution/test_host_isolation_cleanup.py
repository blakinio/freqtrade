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


def test_cleanup_retains_firewall_when_docker_network_removal_fails(tmp_path: Path) -> None:
    runner = _Runner(CommandResult(1, stderr="network has active endpoints"))

    with pytest.raises(RuntimeDriverError) as exc_info:
        _backend(runner, tmp_path).cleanup_network("portal-net-1", "runtime-1")

    assert exc_info.value.reason_code == "HOST_NETWORK_CLEANUP_FAILED"
    assert "retaining nftables policy" in str(exc_info.value)
    assert runner.calls == [("docker", "network", "rm", "portal-net-1")]


def test_cleanup_removes_firewall_only_after_network_teardown(tmp_path: Path) -> None:
    runner = _Runner(CommandResult(0), CommandResult(0))

    _backend(runner, tmp_path).cleanup_network("portal-net-1", "runtime-1")

    assert runner.calls[0] == ("docker", "network", "rm", "portal-net-1")
    assert runner.calls[1][:4] == ("nft", "delete", "table", "inet")


def test_cleanup_reports_nft_failure_after_network_is_absent(tmp_path: Path) -> None:
    runner = _Runner(CommandResult(0), CommandResult(1, stderr="nft backend unavailable"))

    with pytest.raises(RuntimeDriverError) as exc_info:
        _backend(runner, tmp_path).cleanup_network("portal-net-1", "runtime-1")

    assert exc_info.value.reason_code == "HOST_NETWORK_CLEANUP_FAILED"
    assert len(runner.calls) == 2


def test_cleanup_is_idempotent_when_resources_are_already_absent(tmp_path: Path) -> None:
    runner = _Runner(
        CommandResult(1, stderr="Error response from daemon: network portal-net-1 not found"),
        CommandResult(1, stderr="Error: No such file or directory"),
    )

    _backend(runner, tmp_path).cleanup_network("portal-net-1", "runtime-1")

    assert len(runner.calls) == 2
