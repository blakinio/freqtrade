from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ai_platform.portal.execution.driver import CommandResult
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.host_isolation import (
    LinuxNftablesBtrfsIsolationAttestor,
    MappingMarketDataEgressPolicyProvider,
    MarketDataEgressPolicy,
)
from ai_platform.portal.execution.isolation import (
    LogIsolationBackend,
    NetworkIsolationBackend,
    RuntimeHostCapabilityReport,
    RuntimeIsolationPlan,
    RuntimeIsolationResolver,
    StorageIsolationBackend,
    baseline_portal_isolation_profile,
)


NOW = datetime(2026, 8, 9, 20, 0, tzinfo=UTC)
NETWORK_ID = "a" * 64
NETWORK_NAME = "portal-net-test"
BRIDGE = f"br-{NETWORK_ID[:12]}"


class _QueueRunner:
    def __init__(self, *results: CommandResult) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: Sequence[str]) -> CommandResult:
        self.calls.append(tuple(args))
        if not self.results:
            raise AssertionError(f"unexpected command: {tuple(args)!r}")
        return self.results.pop(0)


class _NetworkRunner:
    def __init__(self, runtime_id: str = "runtime-1") -> None:
        self.runtime_id = runtime_id
        self.calls: list[tuple[str, ...]] = []
        self.table_reads = 0

    def run(self, args: Sequence[str]) -> CommandResult:
        call = tuple(args)
        self.calls.append(call)
        if call[:3] == ("docker", "network", "create"):
            return CommandResult(0, stdout=NETWORK_ID)
        if call[:3] == ("docker", "network", "inspect"):
            return CommandResult(
                0,
                stdout=json.dumps(
                    {
                        "Id": NETWORK_ID,
                        "EnableIPv6": False,
                        "Labels": {"ai.portal.runtime_id": self.runtime_id},
                        "Containers": {},
                    }
                ),
            )
        if call[:4] == ("nft", "list", "table", "inet"):
            self.table_reads += 1
            if self.table_reads == 1:
                return CommandResult(1, stderr="No such file or directory")
            return CommandResult(
                0,
                stdout=(
                    f"table inet portal_test {{ hook input hook forward {BRIDGE} "
                    "8.8.8.0/24 tcp dport 443 drop }}"
                ),
            )
        if call[0] == "nft":
            return CommandResult(0)
        if call[:3] == ("docker", "network", "rm"):
            return CommandResult(0)
        raise AssertionError(f"unexpected command: {call!r}")


def _policy() -> MarketDataEgressPolicy:
    return MarketDataEgressPolicy(
        policy_version="public-data-v1",
        allowed_ipv4_cidrs=("8.8.8.0/24",),
        allowed_tcp_ports=(443,),
    )


def _plan(policy: MarketDataEgressPolicy) -> RuntimeIsolationPlan:
    profile = baseline_portal_isolation_profile()
    report = RuntimeHostCapabilityReport(
        generated_at=NOW,
        host_boot_id="boot-1",
        cgroup_mode="v2",
        cgroup_controllers=("cpu", "cpuset", "memory", "pids"),
        supports_readonly_root=True,
        supports_tmpfs=True,
        supports_no_new_privileges=True,
        supports_capability_drop=True,
        supports_required_seccomp=True,
        supports_memory_hard_limit=True,
        supports_swap_bound_or_disable=True,
        supports_pid_hard_limit=True,
        supports_cpu_cfs=True,
        cpuset_cpus=(0, 1),
        storage_backend=StorageIsolationBackend.BOUNDED_VOLUME,
        network_backend=NetworkIsolationBackend.NFTABLES,
        log_backend=LogIsolationBackend.DOCKER_LOCAL,
    )
    return RuntimeIsolationResolver().resolve(
        profile=profile,
        expected_profile_digest=profile.digest(),
        report=report,
        runtime_image_digest="1" * 64,
        gateway_artifact_digest="2" * 64,
        gateway_contract_version="v1",
        gateway_contract_digest="3" * 64,
        market_data_egress_policy_version=policy.policy_version,
        market_data_egress_policy_digest=policy.digest(),
        now=NOW,
    )


def _provider(policy: MarketDataEgressPolicy) -> MappingMarketDataEgressPolicyProvider:
    return MappingMarketDataEgressPolicyProvider({policy.digest(): policy})


def test_market_data_policy_is_digest_bound_and_rejects_private_destinations() -> None:
    policy = _policy()

    assert policy.digest() == _policy().digest()
    with pytest.raises(ValueError, match="globally routable"):
        MarketDataEgressPolicy(
            policy_version="bad-v1",
            allowed_ipv4_cidrs=("10.0.0.0/8",),
        )


def test_compatible_host_capabilities_require_btrfs_and_nftables(tmp_path: Path) -> None:
    runner = _QueueRunner(
        CommandResult(0, stdout="btrfs-progs v6"),
        CommandResult(0, stdout="Label: none"),
        CommandResult(0, stdout="nftables v1"),
    )
    policy = _policy()
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )

    capabilities = backend.capabilities()

    assert capabilities.storage_backend is StorageIsolationBackend.BOUNDED_VOLUME
    assert capabilities.network_backend is NetworkIsolationBackend.NFTABLES


def test_network_backend_builds_generation_deny_by_default_policy(tmp_path: Path) -> None:
    runner = _NetworkRunner()
    policy = _policy()
    plan = _plan(policy)
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )

    backend.prepare_network(plan, NETWORK_NAME, "runtime-1")

    create = runner.calls[0]
    assert create[:3] == ("docker", "network", "create")
    assert "--ipv6=false" in create
    assert "ai.portal.runtime_id=runtime-1" in create

    nft_calls = [call for call in runner.calls if call and call[0] == "nft"]
    assert any(
        "input" in call and "iifname" in call and BRIDGE in call and call[-1] == "drop"
        for call in nft_calls
    )
    assert any(call.count(BRIDGE) >= 2 and call[-1] == "accept" for call in nft_calls)
    assert any(
        "8.8.8.0/24" in call and "443" in call and call[-1] == "accept" for call in nft_calls
    )
    assert any(
        "forward" in call and "iifname" in call and BRIDGE in call and call[-1] == "drop"
        for call in nft_calls
    )


def test_network_attestation_rejects_unrelated_container(tmp_path: Path) -> None:
    policy = _policy()
    plan = _plan(policy)
    runner = _QueueRunner(
        CommandResult(
            0,
            stdout=json.dumps(
                {
                    "Id": NETWORK_ID,
                    "EnableIPv6": False,
                    "Labels": {"ai.portal.runtime_id": "runtime-1"},
                    "Containers": {"container-a": {}},
                }
            ),
        ),
        CommandResult(
            0,
            stdout=json.dumps({"ai.portal.runtime_id": "runtime-other"}),
        ),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.attest_network(plan, NETWORK_NAME, "runtime-1")

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


def _quota_status() -> str:
    return (
        "Quotas on /volume:\n"
        "  Enabled:                 yes\n"
        "  Mode:                    qgroup (full accounting)\n"
        "  Inconsistent:            no\n"
        "  Override limits:         no\n"
    )


def _qgroup_output(limit: int) -> str:
    return f"qgroupid rfer excl max_rfer\n-------- ---- ---- --------\n0/256 0 0 {limit}\n"


def test_storage_backend_applies_and_attests_btrfs_referenced_limit(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    state = state_root / "generation"
    state.mkdir(parents=True)
    policy = _policy()
    plan = _plan(policy)
    runner = _QueueRunner(
        CommandResult(0, stdout="Subvolume ID: 256\n"),
        CommandResult(0),
        CommandResult(0),
        CommandResult(0, stdout=_quota_status()),
        CommandResult(0, stdout="Subvolume ID: 256\n"),
        CommandResult(0, stdout=_qgroup_output(plan.durable_state_max_bytes)),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=state_root,
        btrfs_mount=tmp_path,
    )

    backend.prepare_storage(plan, state)

    assert (
        "btrfs",
        "qgroup",
        "limit",
        str(plan.durable_state_max_bytes),
        str(state.resolve()),
    ) in runner.calls


def test_storage_attestation_rejects_missing_effective_limit(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    state = state_root / "generation"
    state.mkdir(parents=True)
    policy = _policy()
    plan = _plan(policy)
    runner = _QueueRunner(
        CommandResult(0, stdout=_quota_status()),
        CommandResult(0, stdout="Subvolume ID: 256\n"),
        CommandResult(0, stdout=_qgroup_output(1234)),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=state_root,
        btrfs_mount=tmp_path,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.attest_storage(plan, state)

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


def test_storage_backend_rejects_path_escape_before_host_commands(tmp_path: Path) -> None:
    runner = _QueueRunner()
    policy = _policy()
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=tmp_path / "approved",
        btrfs_mount=tmp_path,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.prepare_storage(_plan(policy), tmp_path / "outside")

    assert exc_info.value.reason_code == "HOST_STORAGE_ISOLATION_UNSUPPORTED"
    assert runner.calls == []


def test_storage_backend_rejects_state_root_itself_before_host_commands(tmp_path: Path) -> None:
    runner = _QueueRunner()
    policy = _policy()
    state_root = tmp_path / "approved"
    state_root.mkdir()
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=state_root,
        btrfs_mount=tmp_path,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.prepare_storage(_plan(policy), state_root)

    assert exc_info.value.reason_code == "HOST_STORAGE_ISOLATION_UNSUPPORTED"
    assert state_root.is_dir()
    assert runner.calls == []
