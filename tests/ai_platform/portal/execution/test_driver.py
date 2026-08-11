# ruff: noqa: S108 -- /tmp is a fixed in-container tmpfs security boundary.

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ai_platform.portal.execution.driver import (
    CommandResult,
    DockerCliRuntimeDriver,
    DockerHostCapabilityProbe,
    ExternalIsolationCapabilities,
)
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.isolation import (
    LogIsolationBackend,
    MappingRuntimeIsolationPlanProvider,
    NetworkIsolationBackend,
    RuntimeHostCapabilityReport,
    RuntimeIsolationPlan,
    RuntimeIsolationPlanBinding,
    RuntimeIsolationResolver,
    StorageIsolationBackend,
    baseline_portal_isolation_profile,
)
from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec


NOW = datetime(2026, 8, 9, 20, 0, tzinfo=UTC)
IMAGE_DIGEST = "1" * 64
IMAGE = f"freqtradeorg/freqtrade@sha256:{IMAGE_DIGEST}"
DNS_RESOLVERS = ("1.1.1.1",)


class _Runner:
    def __init__(self, *results: CommandResult) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: Sequence[str]) -> CommandResult:
        self.calls.append(tuple(args))
        if not self.results:
            raise AssertionError(f"unexpected command: {tuple(args)!r}")
        return self.results.pop(0)


class _Attestor:
    def __init__(self, *, fail_activation: bool = False) -> None:
        self.prepared_storage: list[Path] = []
        self.prepared_networks: list[str] = []
        self.attested_storage: list[Path] = []
        self.attested_networks: list[str] = []
        self.attested_active_networks: list[str] = []
        self.activated_networks: list[str] = []
        self.cleaned: list[str] = []
        self.fail_activation = fail_activation
        self.gateway_attestations: list[tuple[str, str, str]] = []

    def attest(self, artifact_digest: str, contract_version: str, contract_digest: str) -> None:
        self.gateway_attestations.append((artifact_digest, contract_version, contract_digest))

    def capabilities(self) -> ExternalIsolationCapabilities:
        return ExternalIsolationCapabilities(
            storage_backend=StorageIsolationBackend.BOUNDED_VOLUME,
            network_backend=NetworkIsolationBackend.CONSTRAINED_PROXY,
        )

    def dns_resolvers(self, plan: RuntimeIsolationPlan) -> tuple[str, ...]:
        assert plan.market_data_egress_policy_version == "public-data-v1"
        return DNS_RESOLVERS

    def prepare_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None:
        assert plan.durable_state_max_bytes > 0
        self.prepared_storage.append(state_path)

    def prepare_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        assert runtime_id == "runtime-1"
        assert plan.network_backend is NetworkIsolationBackend.CONSTRAINED_PROXY
        self.prepared_networks.append(network_name)

    def activate_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        assert runtime_id == "runtime-1"
        assert plan.market_data_egress_policy_version == "public-data-v1"
        if self.fail_activation:
            raise RuntimeDriverError(
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
                "activation failed",
            )
        self.activated_networks.append(network_name)

    def attest_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None:
        assert plan.storage_backend is StorageIsolationBackend.BOUNDED_VOLUME
        self.attested_storage.append(state_path)

    def attest_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        assert runtime_id == "runtime-1"
        assert plan.market_data_egress_policy_version == "public-data-v1"
        self.attested_networks.append(network_name)

    def attest_active_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        assert runtime_id == "runtime-1"
        assert plan.market_data_egress_policy_version == "public-data-v1"
        self.attested_active_networks.append(network_name)

    def cleanup_network(self, network_name: str, runtime_id: str) -> None:
        assert runtime_id == "runtime-1"
        self.cleaned.append(network_name)


def _report() -> RuntimeHostCapabilityReport:
    return RuntimeHostCapabilityReport(
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
        network_backend=NetworkIsolationBackend.CONSTRAINED_PROXY,
        log_backend=LogIsolationBackend.DOCKER_LOCAL,
    )


def _plan() -> RuntimeIsolationPlan:
    profile = baseline_portal_isolation_profile()
    return RuntimeIsolationResolver().resolve(
        profile=profile,
        expected_profile_digest=profile.digest(),
        report=_report(),
        runtime_image_digest=IMAGE_DIGEST,
        gateway_artifact_digest="2" * 64,
        gateway_contract_version="v1",
        gateway_contract_digest="3" * 64,
        market_data_egress_policy_version="public-data-v1",
        market_data_egress_policy_digest="4" * 64,
        now=NOW,
    )


def _provider(plan: RuntimeIsolationPlan) -> MappingRuntimeIsolationPlanProvider:
    binding = RuntimeIsolationPlanBinding(
        isolation_plan_digest=plan.digest(),
        plan=plan,
    )
    return MappingRuntimeIsolationPlanProvider({"runtime-1": binding})


def _spec(tmp_path: Path) -> RuntimeContainerSpec:
    config = tmp_path / "inputs" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text("{}\n", encoding="utf-8")
    state = tmp_path / "state"
    state.mkdir()
    return RuntimeContainerSpec(
        runtime_id="runtime-1",
        image=IMAGE,
        config_path=config,
        state_path=state,
        strategy_name="PortalStrategy",
        labels={"ai.portal.request_id": "request-1"},
    )


def _network() -> str:
    digest = hashlib.sha256(b"network\0runtime-1").hexdigest()[:24]
    return f"portal-net-{digest}"


def _inspect(spec: RuntimeContainerSpec, plan: RuntimeIsolationPlan) -> dict[str, object]:
    return {
        "Config": {
            "User": plan.runtime_user,
            "Image": spec.image,
            "Entrypoint": [DockerCliRuntimeDriver._QUARANTINE_ENTRYPOINT],
            "Cmd": [
                "freqtrade",
                "trade",
                "--config",
                "/runtime/config/config.json",
                "--strategy",
                spec.strategy_name,
            ],
            "Env": [f"PORTAL_LOG_PROBE_BYTES={plan.log_max_bytes * (plan.log_rotation_count + 1)}"],
            "Labels": {
                **spec.labels,
                "ai.portal.runtime_id": spec.runtime_id,
                "ai.portal.isolation_plan_digest": plan.digest(),
            },
        },
        "HostConfig": {
            "Privileged": False,
            "ReadonlyRootfs": True,
            "SecurityOpt": ["no-new-privileges=true"],
            "CapDrop": ["ALL"],
            "CapAdd": None,
            "PidMode": "",
            "IpcMode": "private",
            "UTSMode": "",
            "NetworkMode": _network(),
            "Dns": list(DNS_RESOLVERS),
            "Devices": [],
            "PortBindings": {},
            "RestartPolicy": {"Name": "no"},
            "Memory": plan.memory_limit_bytes,
            "MemorySwap": plan.memory_swap_limit_bytes,
            "PidsLimit": plan.pids_limit,
            "NanoCpus": plan.cpu_millis * 1_000_000,
            "CpusetCpus": "",
            "LogConfig": {
                "Type": "local",
                "Config": {
                    "max-size": str(plan.log_max_bytes),
                    "max-file": str(plan.log_rotation_count),
                },
            },
            "Tmpfs": {
                "/tmp": f"rw,noexec,nosuid,nodev,size={plan.tmpfs_max_bytes}",
                "/run": f"rw,noexec,nosuid,nodev,size={plan.run_tmpfs_max_bytes}",
            },
        },
        "Mounts": [
            {
                "Type": "bind",
                "Destination": "/runtime/config",
                "Source": str(spec.config_path.parent.resolve()),
                "RW": False,
            },
            {
                "Type": "bind",
                "Destination": "/runtime/state",
                "Source": str(spec.state_path.resolve()),
                "RW": True,
            },
            {"Type": "tmpfs", "Destination": "/tmp", "Source": "", "RW": True},
        ],
    }


def _effective_results(plan: RuntimeIsolationPlan) -> list[CommandResult]:
    return [
        CommandResult(0),
        CommandResult(
            0,
            stdout=(
                f"memory={plan.memory_limit_bytes}\n"
                f"swap={plan.memory_swap_limit_bytes - plan.memory_limit_bytes}\n"
                f"pids={plan.pids_limit}\n"
                "cpu=100000 100000\ncpuset=\n"
            ),
        ),
        CommandResult(
            0,
            stdout=(
                "overlay / overlay ro,relatime 0 0\n"
                f"tmpfs /tmp tmpfs rw,nosuid,nodev,noexec,size={plan.tmpfs_max_bytes} 0 0\n"
                f"tmpfs /run tmpfs rw,nosuid,nodev,noexec,size={plan.run_tmpfs_max_bytes} 0 0\n"
            ),
        ),
        CommandResult(0),
        CommandResult(0, stdout=f"retained\n{DockerCliRuntimeDriver._LOG_PROBE_END}\n"),
    ]


def _provision_results(
    spec: RuntimeContainerSpec,
    plan: RuntimeIsolationPlan,
) -> list[CommandResult]:
    return [
        CommandResult(1, stderr="Error: No such object: runtime-1"),
        CommandResult(0, stdout=json.dumps([f"repo@sha256:{IMAGE_DIGEST}"])),
        CommandResult(0, stdout="container-id"),
        CommandResult(0, stdout=json.dumps([_inspect(spec, plan)])),
        CommandResult(0),
        *_effective_results(plan),
    ]


def _reattest_results(
    spec: RuntimeContainerSpec,
    plan: RuntimeIsolationPlan,
) -> list[CommandResult]:
    return [
        CommandResult(0, stdout=json.dumps([_inspect(spec, plan)])),
        *_effective_results(plan),
    ]


def test_provision_builds_quarantined_hardened_container(tmp_path: Path) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    runner = _Runner(*_provision_results(spec, plan))
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )

    assert driver.provision(spec) is DriverRuntimeState.CREATED

    create = runner.calls[2]
    for flag in (
        "--read-only",
        "--security-opt",
        "--cap-drop",
        "--pids-limit",
        "--memory",
        "--memory-swap",
        "--cpus",
        "--tmpfs",
        "--log-driver",
        "--dns",
        "--network",
    ):
        assert flag in create
    assert "no-new-privileges=true" in create
    assert "ALL" in create
    assert "1.1.1.1" in create
    assert "-p" not in create
    assert "--publish" not in create
    assert "--entrypoint" not in create
    assert not any("docker.sock" in value for value in create)
    assert "Seccomp:" in runner.calls[5][-1]
    assert "/proc/swaps" in runner.calls[6][-1]
    assert runner.calls[8][:3] == ("docker", "exec", "runtime-1")
    assert runner.calls[9] == ("docker", "logs", "runtime-1")
    assert attestor.prepared_storage == [spec.state_path]
    assert attestor.prepared_networks == [_network()]
    assert attestor.attested_storage == [spec.state_path]
    assert attestor.attested_networks == [_network()]
    assert attestor.activated_networks == []


def test_release_repeats_attestation_then_activates_egress_before_gate(tmp_path: Path) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    runner = _Runner(*_provision_results(spec, plan))
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )
    driver.provision(spec)
    initial_attest_count = len(attestor.attested_networks)
    assert attestor.activated_networks == []
    runner.results.extend(
        [
            CommandResult(0, stdout="running\n"),
            CommandResult(1),
            *_reattest_results(spec, plan),
            CommandResult(0),
        ]
    )

    assert driver.start("runtime-1") is DriverRuntimeState.STARTING
    assert len(attestor.attested_networks) == initial_attest_count + 1
    assert attestor.activated_networks == [_network()]
    assert runner.calls[-1][:5] == (
        "docker",
        "exec",
        "runtime-1",
        "/bin/sh",
        "-ec",
    )
    assert DockerCliRuntimeDriver._RELEASE in runner.calls[-1]


def test_release_fails_closed_if_structure_changes_after_initial_attestation(
    tmp_path: Path,
) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    runner = _Runner(*_provision_results(spec, plan))
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )
    driver.provision(spec)
    tampered = _inspect(spec, plan)
    host = tampered["HostConfig"]
    assert isinstance(host, dict)
    host["Privileged"] = True
    runner.results.extend(
        [
            CommandResult(0, stdout="running\n"),
            CommandResult(1),
            CommandResult(0, stdout=json.dumps([tampered])),
            CommandResult(0),
        ]
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.start("runtime-1")

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"
    assert attestor.activated_networks == []
    assert attestor.cleaned == [_network()]
    assert all(DockerCliRuntimeDriver._RELEASE not in call for call in runner.calls)


def test_release_activation_failure_removes_runtime_before_application_gate(tmp_path: Path) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    runner = _Runner(*_provision_results(spec, plan))
    attestor = _Attestor(fail_activation=True)
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )
    driver.provision(spec)
    runner.results.extend(
        [
            CommandResult(0, stdout="running\n"),
            CommandResult(1),
            *_reattest_results(spec, plan),
            CommandResult(0),
        ]
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.start("runtime-1")

    assert exc_info.value.reason_code == "HOST_NETWORK_ISOLATION_UNSUPPORTED"
    assert attestor.activated_networks == []
    assert attestor.cleaned == [_network()]
    assert runner.calls[-1] == ("docker", "rm", "-f", "runtime-1")
    assert all(DockerCliRuntimeDriver._RELEASE not in call for call in runner.calls)


def test_missing_plan_fails_before_engine_mutation(tmp_path: Path) -> None:
    runner = _Runner()
    driver = DockerCliRuntimeDriver(runner)

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.provision(_spec(tmp_path))

    assert exc_info.value.reason_code == "ISOLATION_PLAN_MISMATCH"
    assert runner.calls == []


def test_missing_storage_backend_fails_before_create(tmp_path: Path) -> None:
    plan = _plan()
    runner = _Runner(CommandResult(1, stderr="Error: No such object: runtime-1"))
    driver = DockerCliRuntimeDriver(runner, isolation_plans=_provider(plan))

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.provision(_spec(tmp_path))

    assert exc_info.value.reason_code == "HOST_NETWORK_ISOLATION_UNSUPPORTED"
    assert all(call[:2] != ("docker", "create") for call in runner.calls)


def test_missing_image_cleans_prepared_generation_network(tmp_path: Path) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    runner = _Runner(
        CommandResult(1, stderr="Error: No such object: runtime-1"),
        CommandResult(1, stderr="No such image"),
        CommandResult(1, stderr="Error: No such object: runtime-1"),
    )
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.provision(spec)

    assert exc_info.value.reason_code == "IMAGE_NOT_PRESENT"
    assert runner.calls[-1] == ("docker", "rm", "-f", "runtime-1")
    assert attestor.cleaned == [_network()]


def test_structural_failure_removes_quarantined_container(tmp_path: Path) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    unsafe = _inspect(spec, plan)
    unsafe_host = unsafe["HostConfig"]
    assert isinstance(unsafe_host, dict)
    unsafe_host["Privileged"] = True
    results = _provision_results(spec, plan)[:4]
    results[3] = CommandResult(0, stdout=json.dumps([unsafe]))
    results.append(CommandResult(0))
    runner = _Runner(*results)
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.provision(spec)

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"
    assert runner.calls[-1] == ("docker", "rm", "-f", "runtime-1")
    assert attestor.cleaned == [_network()]


@pytest.mark.parametrize("tampered_field", ["entrypoint", "identity", "dns"])
def test_structural_attestation_rejects_tampered_bootstrap_identity_or_dns(
    tmp_path: Path,
    tampered_field: str,
) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    unsafe = _inspect(spec, plan)
    unsafe_config = unsafe["Config"]
    unsafe_host = unsafe["HostConfig"]
    assert isinstance(unsafe_config, dict)
    assert isinstance(unsafe_host, dict)
    if tampered_field == "entrypoint":
        unsafe_config["Entrypoint"] = ["freqtrade"]
    elif tampered_field == "identity":
        labels = unsafe_config["Labels"]
        assert isinstance(labels, dict)
        labels["ai.portal.isolation_plan_digest"] = "f" * 64
    else:
        unsafe_host["Dns"] = ["8.8.8.8"]
    results = _provision_results(spec, plan)[:4]
    results[3] = CommandResult(0, stdout=json.dumps([unsafe]))
    results.append(CommandResult(0))
    runner = _Runner(*results)
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.provision(spec)

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"
    assert runner.calls[-1] == ("docker", "rm", "-f", "runtime-1")
    assert attestor.cleaned == [_network()]


def test_bounded_log_attestation_requires_rotation_and_retention_ceiling() -> None:
    plan = replace(_plan(), log_max_bytes=1024, log_rotation_count=1)
    success = _Runner(
        CommandResult(0),
        CommandResult(0, stdout=f"retained\n{DockerCliRuntimeDriver._LOG_PROBE_END}\n"),
    )
    DockerCliRuntimeDriver(success)._attest_bounded_logs("runtime-1", plan)

    stale = _Runner(
        CommandResult(0),
        CommandResult(
            0,
            stdout=(
                f"{DockerCliRuntimeDriver._LOG_PROBE_BEGIN}\n"
                f"{DockerCliRuntimeDriver._LOG_PROBE_END}\n"
            ),
        ),
    )
    with pytest.raises(RuntimeDriverError) as stale_error:
        DockerCliRuntimeDriver(stale)._attest_bounded_logs("runtime-1", plan)
    assert stale_error.value.reason_code == "ISOLATION_ATTESTATION_FAILED"

    oversized = _Runner(
        CommandResult(0),
        CommandResult(
            0,
            stdout=(
                "x" * (DockerCliRuntimeDriver._LOG_RETENTION_TOLERANCE_BYTES + 2048)
                + DockerCliRuntimeDriver._LOG_PROBE_END
            ),
        ),
    )
    with pytest.raises(RuntimeDriverError) as oversized_error:
        DockerCliRuntimeDriver(oversized)._attest_bounded_logs("runtime-1", plan)
    assert oversized_error.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


def test_released_runtime_is_starting_until_application_ready() -> None:
    runner = _Runner(
        CommandResult(0, stdout="running\n"),
        CommandResult(0),
        CommandResult(1),
    )
    assert DockerCliRuntimeDriver(runner).inspect("runtime-1") is DriverRuntimeState.STARTING


def test_running_generation_repeats_current_isolation_attestation(tmp_path: Path) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    runner = _Runner(
        CommandResult(0, stdout="running\n"),
        CommandResult(0),
        CommandResult(0),
        *_reattest_results(spec, plan),
    )
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )
    driver._attested.add(spec.runtime_id)
    driver._released.add(spec.runtime_id)
    driver._fingerprints[spec.runtime_id] = driver._fingerprint(spec, plan.digest())
    driver._networks[spec.runtime_id] = _network()
    driver._specs[spec.runtime_id] = spec
    driver._plan_digests[spec.runtime_id] = plan.digest()

    assert driver.start(spec.runtime_id) is DriverRuntimeState.RUNNING
    assert attestor.attested_networks == []
    assert attestor.attested_active_networks == [_network()]
    assert attestor.activated_networks == []


def test_running_generation_tamper_fails_closed_and_removes_runtime(tmp_path: Path) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    tampered = _inspect(spec, plan)
    host = tampered["HostConfig"]
    assert isinstance(host, dict)
    host["Privileged"] = True
    runner = _Runner(
        CommandResult(0, stdout="running\n"),
        CommandResult(0),
        CommandResult(0),
        CommandResult(0, stdout=json.dumps([tampered])),
        CommandResult(0),
    )
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )
    driver._attested.add(spec.runtime_id)
    driver._released.add(spec.runtime_id)
    driver._fingerprints[spec.runtime_id] = driver._fingerprint(spec, plan.digest())
    driver._networks[spec.runtime_id] = _network()
    driver._specs[spec.runtime_id] = spec
    driver._plan_digests[spec.runtime_id] = plan.digest()

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.start(spec.runtime_id)

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"
    assert attestor.cleaned == [_network()]
    assert runner.calls[-1] == ("docker", "rm", "-f", spec.runtime_id)


def test_paused_foreign_runtime_cannot_be_released() -> None:
    runner = _Runner(CommandResult(0, stdout="paused\n"))

    with pytest.raises(RuntimeDriverError) as exc_info:
        DockerCliRuntimeDriver(runner).start("runtime-1")

    assert exc_info.value.reason_code == "APPLICATION_RELEASE_FORBIDDEN"


def test_paused_released_runtime_requires_reprovision_before_resume() -> None:
    runner = _Runner(CommandResult(0, stdout="paused\n"))
    driver = DockerCliRuntimeDriver(runner)
    driver._released.add("runtime-1")

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.start("runtime-1")

    assert exc_info.value.reason_code == "APPLICATION_RELEASE_FORBIDDEN"
    assert ("docker", "unpause", "runtime-1") not in runner.calls


def test_paused_trusted_generation_is_freshly_reprovisioned(tmp_path: Path) -> None:
    plan = _plan()
    spec = _spec(tmp_path)
    runner = _Runner(
        CommandResult(0, stdout="paused\n"),
        CommandResult(0),
        *_provision_results(spec, plan)[1:],
    )
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
        gateway_attestor=attestor,
    )
    driver._attested.add(spec.runtime_id)
    driver._released.add(spec.runtime_id)
    driver._fingerprints[spec.runtime_id] = driver._fingerprint(spec, plan.digest())
    driver._networks[spec.runtime_id] = _network()
    driver._specs[spec.runtime_id] = spec
    driver._plan_digests[spec.runtime_id] = plan.digest()

    assert driver.provision(spec) is DriverRuntimeState.CREATED
    assert ("docker", "rm", "-f", spec.runtime_id) in runner.calls
    assert ("docker", "unpause", spec.runtime_id) not in runner.calls
    assert spec.runtime_id not in driver._released
    assert attestor.cleaned == [_network()]


def test_gateway_plan_fields_are_not_artifact_evidence(tmp_path: Path) -> None:
    plan = _plan()
    runner = _Runner()
    attestor = _Attestor()
    driver = DockerCliRuntimeDriver(
        runner,
        isolation_plans=_provider(plan),
        external_attestor=attestor,
    )

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver.provision(_spec(tmp_path))

    assert exc_info.value.reason_code == "GATEWAY_ARTIFACT_NOT_PRESENT"
    assert runner.calls == []


def test_pause_stop_and_unknown_state_are_fail_closed_or_idempotent() -> None:
    paused = _Runner(CommandResult(0, stdout="paused\n"))
    stopped = _Runner(CommandResult(0, stdout="exited\n"))
    unknown = _Runner(CommandResult(0, stdout="mystery\n"))

    assert DockerCliRuntimeDriver(paused).pause("runtime-1") is DriverRuntimeState.PAUSED
    assert DockerCliRuntimeDriver(stopped).stop("runtime-1") is DriverRuntimeState.STOPPED
    with pytest.raises(RuntimeDriverError) as exc_info:
        DockerCliRuntimeDriver(unknown).inspect("runtime-1")
    assert exc_info.value.reason_code == "DOCKER_STATE_UNKNOWN"


def test_host_probe_reports_cgroup_v2_and_approved_external_backends(
    tmp_path: Path,
) -> None:
    cgroup = tmp_path / "cgroup"
    cgroup.mkdir()
    (cgroup / "cgroup.controllers").write_text(
        "cpu cpuset memory pids\n",
        encoding="utf-8",
    )
    (cgroup / "memory.swap.max").write_text("max\n", encoding="utf-8")
    (cgroup / "cpuset.cpus.effective").write_text("0-3\n", encoding="utf-8")
    boot_id = tmp_path / "boot-id"
    boot_id.write_text("boot-1\n", encoding="utf-8")
    runner = _Runner(
        CommandResult(0, stdout='["name=seccomp,profile=builtin"]'),
        CommandResult(0, stdout='["local","json-file"]'),
    )

    report = DockerHostCapabilityProbe(
        runner,
        external_attestor=_Attestor(),
        cgroup_root=cgroup,
        boot_id_path=boot_id,
    ).probe(now=NOW)

    assert report.cgroup_mode == "v2"
    assert report.supports_cpu_cfs is True
    assert report.supports_memory_hard_limit is True
    assert report.supports_swap_bound_or_disable is True
    assert report.supports_pid_hard_limit is True
    assert report.cpuset_cpus == (0, 1, 2, 3)
    assert report.storage_backend is StorageIsolationBackend.BOUNDED_VOLUME
    assert report.network_backend is NetworkIsolationBackend.CONSTRAINED_PROXY
    assert report.log_backend is LogIsolationBackend.DOCKER_LOCAL


def test_host_probe_accepts_no_active_swap_without_swap_controller(tmp_path: Path) -> None:
    cgroup = tmp_path / "cgroup"
    cgroup.mkdir()
    (cgroup / "cgroup.controllers").write_text("cpu memory pids\n", encoding="utf-8")
    boot_id = tmp_path / "boot-id"
    boot_id.write_text("boot-1\n", encoding="utf-8")
    proc_swaps = tmp_path / "swaps"
    proc_swaps.write_text("Filename Type Size Used Priority\n", encoding="utf-8")
    runner = _Runner(
        CommandResult(0, stdout='["name=seccomp,profile=builtin"]'),
        CommandResult(0, stdout='["local"]'),
    )

    report = DockerHostCapabilityProbe(
        runner,
        external_attestor=_Attestor(),
        cgroup_root=cgroup,
        boot_id_path=boot_id,
        proc_swaps_path=proc_swaps,
    ).probe(now=NOW)

    assert report.supports_swap_bound_or_disable is True


def test_host_probe_rejects_active_swap_without_swap_controller(tmp_path: Path) -> None:
    cgroup = tmp_path / "cgroup"
    cgroup.mkdir()
    (cgroup / "cgroup.controllers").write_text("cpu memory pids\n", encoding="utf-8")
    boot_id = tmp_path / "boot-id"
    boot_id.write_text("boot-1\n", encoding="utf-8")
    proc_swaps = tmp_path / "swaps"
    proc_swaps.write_text(
        "Filename Type Size Used Priority\n/swapfile file 1024 0 -2\n",
        encoding="utf-8",
    )
    runner = _Runner(
        CommandResult(0, stdout='["name=seccomp,profile=builtin"]'),
        CommandResult(0, stdout='["local"]'),
    )

    report = DockerHostCapabilityProbe(
        runner,
        external_attestor=_Attestor(),
        cgroup_root=cgroup,
        boot_id_path=boot_id,
        proc_swaps_path=proc_swaps,
    ).probe(now=NOW)

    assert report.supports_swap_bound_or_disable is False


def test_effective_cgroup_accepts_host_disabled_swap_only_for_zero_swap_plan() -> None:
    plan = _plan()
    driver = DockerCliRuntimeDriver()
    evidence = (
        f"memory={plan.memory_limit_bytes}\n"
        "swap=host-disabled\n"
        f"pids={plan.pids_limit}\n"
        "cpu=100000 100000\n"
        "cpuset=\n"
    )

    driver._attest_cgroup(evidence, plan)

    with pytest.raises(RuntimeDriverError) as exc_info:
        driver._attest_cgroup(
            evidence,
            replace(plan, memory_swap_limit_bytes=plan.memory_limit_bytes + 1024),
        )

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"


def test_effective_rootfs_attestation_requires_readonly_mount() -> None:
    DockerCliRuntimeDriver._attest_readonly_root("overlay / overlay ro,relatime 0 0\n")

    with pytest.raises(RuntimeDriverError) as exc_info:
        DockerCliRuntimeDriver._attest_readonly_root("overlay / overlay rw,relatime 0 0\n")

    assert exc_info.value.reason_code == "ISOLATION_ATTESTATION_FAILED"
