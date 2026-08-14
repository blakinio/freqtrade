from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from copy import deepcopy
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
TABLE = f"portal_{hashlib.sha256(NETWORK_NAME.encode()).hexdigest()[:20]}"
BTRFS_UUID = "11111111-2222-3333-4444-555555555555"


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
        self.active = False

    def run(self, args: Sequence[str]) -> CommandResult:
        call = tuple(args)
        self.calls.append(call)
        if call[:3] == ("docker", "network", "create"):
            return CommandResult(0, stdout=NETWORK_ID)
        if call[:3] == ("docker", "network", "inspect"):
            return CommandResult(0, stdout=json.dumps(_network_info(self.runtime_id)))
        if call[:4] == ("nft", "list", "table", "inet"):
            return CommandResult(1, stderr="No such file or directory")
        if call[:5] == ("nft", "-j", "list", "table", "inet"):
            return CommandResult(0, stdout=json.dumps(_nft_payload(_policy(), active=self.active)))
        if call[:3] == ("nft", "insert", "rule"):
            assert call[-2:] == ("jump", "egress")
            self.active = True
            return CommandResult(0)
        if call[0] == "nft":
            return CommandResult(0)
        if call[:3] == ("docker", "network", "rm"):
            return CommandResult(0)
        raise AssertionError(f"unexpected command: {call!r}")


def _policy() -> MarketDataEgressPolicy:
    return MarketDataEgressPolicy(
        policy_version="public-data-v2",
        allowed_ipv4_cidrs=("8.8.8.0/24",),
        dns_resolver_ipv4_addresses=("1.1.1.1",),
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


def _network_info(runtime_id: str = "runtime-1") -> dict[str, object]:
    return {
        "Id": NETWORK_ID,
        "EnableIPv6": False,
        "Labels": {"ai.portal.runtime_id": runtime_id},
        "Containers": {},
    }


def _match(left: dict[str, object], right: object, op: str = "==") -> dict[str, object]:
    return {"match": {"op": op, "left": left, "right": right}}


def _meta(key: str, right: object) -> dict[str, object]:
    return _match({"meta": {"key": key}}, right)


def _payload(protocol: str, field: str, right: object) -> dict[str, object]:
    return _match({"payload": {"protocol": protocol, "field": field}}, right)


def _ct_states() -> dict[str, object]:
    return _match({"ct": {"key": "state"}}, {"set": ["new", "established"]}, op="in")


def _rule(chain: str, *expr: dict[str, object]) -> dict[str, object]:
    return {
        "rule": {
            "family": "inet",
            "table": TABLE,
            "chain": chain,
            "expr": [*expr, {"counter": {"packets": 0, "bytes": 0}}],
        }
    }


def _nft_payload(policy: MarketDataEgressPolicy, *, active: bool = False) -> dict[str, object]:
    nftables: list[dict[str, object]] = [
        {"metainfo": {"json_schema_version": 1}},
        {"table": {"family": "inet", "name": TABLE}},
        {
            "chain": {
                "family": "inet",
                "table": TABLE,
                "name": "input",
                "type": "filter",
                "hook": "input",
                "prio": -40,
                "policy": "accept",
            }
        },
        {
            "chain": {
                "family": "inet",
                "table": TABLE,
                "name": "forward",
                "type": "filter",
                "hook": "forward",
                "prio": -40,
                "policy": "accept",
            }
        },
        {"chain": {"family": "inet", "table": TABLE, "name": "egress"}},
        _rule("input", _meta("iifname", BRIDGE), {"drop": None}),
    ]
    if active:
        nftables.append(
            _rule(
                "forward",
                _meta("iifname", BRIDGE),
                {"jump": {"target": "egress"}},
            )
        )
    nftables.append(
        _rule(
            "forward",
            _meta("iifname", BRIDGE),
            _meta("oifname", BRIDGE),
            {"accept": None},
        )
    )
    for cidr in policy.allowed_ipv4_cidrs:
        network = cidr.split("/", 1)
        right: object = (
            {"prefix": {"addr": network[0], "len": int(network[1])}} if len(network) == 2 else cidr
        )
        for port in policy.allowed_tcp_ports:
            nftables.append(
                _rule(
                    "egress",
                    _payload("ip", "daddr", right),
                    _payload("tcp", "dport", port),
                    _ct_states(),
                    {"accept": None},
                )
            )
    for resolver in policy.dns_resolver_ipv4_addresses:
        nftables.append(
            _rule(
                "egress",
                _payload("ip", "daddr", resolver),
                _payload("udp", "dport", 53),
                {"accept": None},
            )
        )
        nftables.append(
            _rule(
                "egress",
                _payload("ip", "daddr", resolver),
                _payload("tcp", "dport", 53),
                _ct_states(),
                {"accept": None},
            )
        )
    nftables.append(_rule("forward", _meta("iifname", BRIDGE), {"drop": None}))
    return {"nftables": nftables}


def _rule_entries(payload: dict[str, object], chain: str) -> list[dict[str, object]]:
    entries = payload["nftables"]
    assert isinstance(entries, list)
    selected: list[dict[str, object]] = []
    for entry in entries:
        if not isinstance(entry, dict) or "rule" not in entry:
            continue
        rule = entry["rule"]
        if isinstance(rule, dict) and rule.get("chain") == chain:
            selected.append(entry)
    return selected


def test_market_data_policy_is_digest_bound_and_rejects_private_destinations() -> None:
    policy = _policy()

    assert policy.digest() == _policy().digest()
    with pytest.raises(ValueError, match="globally routable"):
        MarketDataEgressPolicy(
            policy_version="bad-v1",
            allowed_ipv4_cidrs=("10.0.0.0/8",),
            dns_resolver_ipv4_addresses=("1.1.1.1",),
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


def test_network_backend_stages_allowlist_but_keeps_public_egress_denied(tmp_path: Path) -> None:
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
    assert runner.active is False

    nft_calls = [call for call in runner.calls if call and call[0] == "nft"]
    assert any(call[:6] == ("nft", "add", "chain", "inet", TABLE, "egress") for call in nft_calls)
    assert any(
        len(call) > 6
        and call[2:6] == ("rule", "inet", TABLE, "egress")
        and "8.8.8.0/24" in call
        and "443" in call
        and call[-1] == "accept"
        for call in nft_calls
    )
    assert any(
        len(call) > 6
        and call[2:6] == ("rule", "inet", TABLE, "egress")
        and "1.1.1.1" in call
        and "udp" in call
        and "53" in call
        and call[-1] == "accept"
        for call in nft_calls
    )
    assert any(
        "forward" in call and "iifname" in call and BRIDGE in call and call[-1] == "drop"
        for call in nft_calls
    )
    assert not any("jump" in call for call in nft_calls)


def test_network_attestation_accepts_exact_staged_canonical_ruleset(tmp_path: Path) -> None:
    policy = _policy()
    plan = _plan(policy)
    runner = _QueueRunner(
        CommandResult(0, stdout=json.dumps(_network_info())),
        CommandResult(0, stdout=json.dumps(_nft_payload(policy))),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )
    backend._network_ids["runtime-1"] = NETWORK_ID

    backend.attest_network(plan, NETWORK_NAME, "runtime-1")

    assert runner.calls[-1] == ("nft", "-j", "list", "table", "inet", TABLE)


def test_network_activation_links_only_pre_attested_egress_chain(tmp_path: Path) -> None:
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

    backend.activate_network(plan, NETWORK_NAME, "runtime-1")

    assert runner.active is True
    insert_calls = [call for call in runner.calls if call[:3] == ("nft", "insert", "rule")]
    assert insert_calls == [
        (
            "nft",
            "insert",
            "rule",
            "inet",
            TABLE,
            "forward",
            "iifname",
            BRIDGE,
            "counter",
            "jump",
            "egress",
        )
    ]


@pytest.mark.parametrize("tamper", ["extra-accept", "swap-egress-order", "wrong-dns-verdict"])
def test_network_attestation_rejects_noncanonical_staged_ruleset(
    tmp_path: Path,
    tamper: str,
) -> None:
    policy = _policy()
    plan = _plan(policy)
    payload = deepcopy(_nft_payload(policy))
    nftables = payload["nftables"]
    assert isinstance(nftables, list)
    if tamper == "extra-accept":
        nftables.append(_rule("forward", _meta("iifname", BRIDGE), {"accept": None}))
    elif tamper == "swap-egress-order":
        egress = _rule_entries(payload, "egress")
        assert len(egress) >= 2
        first = nftables.index(egress[0])
        second = nftables.index(egress[1])
        nftables[first], nftables[second] = nftables[second], nftables[first]
    else:
        egress = _rule_entries(payload, "egress")
        dns_rule = egress[1]
        rule = dns_rule["rule"]
        assert isinstance(rule, dict)
        expr = rule["expr"]
        assert isinstance(expr, list)
        expr[-2] = {"drop": None}
    runner = _QueueRunner(
        CommandResult(0, stdout=json.dumps(_network_info())),
        CommandResult(0, stdout=json.dumps(payload)),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )
    backend._network_ids["runtime-1"] = NETWORK_ID

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.attest_network(plan, NETWORK_NAME, "runtime-1")

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


def test_network_attestation_rejects_copied_runtime_labels_on_wrong_container(
    tmp_path: Path,
) -> None:
    policy = _policy()
    plan = _plan(policy)
    network = _network_info()
    containers = network["Containers"]
    assert isinstance(containers, dict)
    containers["container-a"] = {"Name": "copied-label-attacker"}
    runner = _QueueRunner(
        CommandResult(0, stdout=json.dumps(network)),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )
    backend._network_ids["runtime-1"] = NETWORK_ID

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.attest_network(plan, NETWORK_NAME, "runtime-1")

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


def test_network_attestation_rejects_unrelated_container(tmp_path: Path) -> None:
    policy = _policy()
    plan = _plan(policy)
    network = _network_info()
    containers = network["Containers"]
    assert isinstance(containers, dict)
    containers["container-a"] = {"Name": "runtime-1"}
    runner = _QueueRunner(
        CommandResult(0, stdout=json.dumps(network)),
        CommandResult(0, stdout=json.dumps({"ai.portal.runtime_id": "runtime-other"})),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=tmp_path / "state",
        btrfs_mount=tmp_path,
    )
    backend._network_ids["runtime-1"] = NETWORK_ID

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.attest_network(plan, NETWORK_NAME, "runtime-1")

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


def _filesystem_show() -> str:
    return f"Label: none  uuid: {BTRFS_UUID}\n"


def _qgroup_output(limit: int) -> str:
    return (
        "Qgroupid Referenced Exclusive Max referenced Path\n"
        "-------- ---------- --------- -------------- ----\n"
        f"0/256 0 0 {limit} generation\n"
    )


def test_qgroup_limit_parser_accepts_legacy_max_rfer_header() -> None:
    output = "QGROUPID RFER EXCL MAX_RFER\n-------- ---- ---- --------\n0/256 0 0 8192\n"

    assert LinuxNftablesBtrfsIsolationAttestor._qgroup_max_rfer(output, "0/256") == 8192


def _qgroup_sysfs(
    tmp_path: Path,
    *,
    enabled: str = "1",
    inconsistent: str = "0",
    mode: str | None = "qgroup",
) -> Path:
    root = tmp_path / "btrfs-sysfs"
    qgroups = root / BTRFS_UUID / "qgroups"
    qgroups.mkdir(parents=True)
    (qgroups / "enabled").write_text(f"{enabled}\n", encoding="utf-8")
    (qgroups / "inconsistent").write_text(f"{inconsistent}\n", encoding="utf-8")
    if mode is not None:
        (qgroups / "mode").write_text(f"{mode}\n", encoding="utf-8")
    return root


def test_storage_backend_applies_and_attests_btrfs_referenced_limit(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    state = state_root / "generation"
    state.mkdir(parents=True)
    policy = _policy()
    plan = _plan(policy)
    sysfs = _qgroup_sysfs(tmp_path)
    runner = _QueueRunner(
        CommandResult(0, stdout="Subvolume ID: 256\n"),
        CommandResult(0),
        CommandResult(0),
        CommandResult(0),
        CommandResult(0),
        CommandResult(0, stdout=_filesystem_show()),
        CommandResult(0, stdout="1000:1000:700\n"),
        CommandResult(0, stdout="Subvolume ID: 256\n"),
        CommandResult(0, stdout=_qgroup_output(plan.durable_state_max_bytes)),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=state_root,
        btrfs_mount=tmp_path,
        btrfs_sysfs_root=sysfs,
    )

    backend.prepare_storage(plan, state)

    assert ("chown", "1000:1000", str(state.resolve())) in runner.calls
    assert ("chmod", "0700", str(state.resolve())) in runner.calls
    assert (
        "btrfs",
        "qgroup",
        "limit",
        str(plan.durable_state_max_bytes),
        str(state.resolve()),
    ) in runner.calls
    assert runner.calls[-1] == (
        "btrfs",
        "qgroup",
        "show",
        "--sync",
        "--raw",
        "-r",
        str(tmp_path.resolve()),
    )


def test_storage_attestation_rejects_missing_effective_limit(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    state = state_root / "generation"
    state.mkdir(parents=True)
    policy = _policy()
    plan = _plan(policy)
    sysfs = _qgroup_sysfs(tmp_path)
    runner = _QueueRunner(
        CommandResult(0, stdout=_filesystem_show()),
        CommandResult(0, stdout="1000:1000:700\n"),
        CommandResult(0, stdout="Subvolume ID: 256\n"),
        CommandResult(0, stdout=_qgroup_output(1234)),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=state_root,
        btrfs_mount=tmp_path,
        btrfs_sysfs_root=sysfs,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.attest_storage(plan, state)

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


def test_storage_attestation_rejects_wrong_runtime_owner_or_mode(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    state = state_root / "generation"
    state.mkdir(parents=True)
    policy = _policy()
    sysfs = _qgroup_sysfs(tmp_path)
    runner = _QueueRunner(
        CommandResult(0, stdout=_filesystem_show()),
        CommandResult(0, stdout="0:0:755\n"),
    )
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=state_root,
        btrfs_mount=tmp_path,
        btrfs_sysfs_root=sysfs,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.attest_storage(_plan(policy), state)

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


@pytest.mark.parametrize(
    ("enabled", "inconsistent", "mode"),
    (("0", "0", "qgroup"), ("1", "1", "qgroup"), ("1", "0", "squota")),
)
def test_storage_attestation_rejects_unenforced_qgroup_state(
    tmp_path: Path,
    enabled: str,
    inconsistent: str,
    mode: str,
) -> None:
    state_root = tmp_path / "state"
    state = state_root / "generation"
    state.mkdir(parents=True)
    policy = _policy()
    sysfs = _qgroup_sysfs(
        tmp_path,
        enabled=enabled,
        inconsistent=inconsistent,
        mode=mode,
    )
    runner = _QueueRunner(CommandResult(0, stdout=_filesystem_show()))
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=state_root,
        btrfs_mount=tmp_path,
        btrfs_sysfs_root=sysfs,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.attest_storage(_plan(policy), state)

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


def test_storage_attestation_fails_closed_without_sysfs_qgroup_state(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    state = state_root / "generation"
    state.mkdir(parents=True)
    policy = _policy()
    runner = _QueueRunner(CommandResult(0, stdout=_filesystem_show()))
    backend = LinuxNftablesBtrfsIsolationAttestor(
        runner,
        policy_provider=_provider(policy),
        state_root=state_root,
        btrfs_mount=tmp_path,
        btrfs_sysfs_root=tmp_path / "missing-sysfs",
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        backend.attest_storage(_plan(policy), state)

    assert exc_info.value.reason_code == "HOST_STORAGE_ISOLATION_UNSUPPORTED"


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
