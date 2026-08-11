from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta

import pytest

from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.isolation import (
    LogIsolationBackend,
    NetworkIsolationBackend,
    RuntimeHostCapabilityReport,
    RuntimeIsolationPlanBinding,
    RuntimeIsolationResolver,
    StorageIsolationBackend,
    baseline_portal_isolation_profile,
)


NOW = datetime(2026, 8, 9, 20, 0, tzinfo=UTC)


def _report(**updates: object) -> RuntimeHostCapabilityReport:
    values: dict[str, object] = {
        "generated_at": NOW,
        "host_boot_id": "boot-1",
        "cgroup_mode": "v2",
        "cgroup_controllers": ("cpu", "cpuset", "memory", "pids"),
        "supports_readonly_root": True,
        "supports_tmpfs": True,
        "supports_no_new_privileges": True,
        "supports_capability_drop": True,
        "supports_required_seccomp": True,
        "supports_memory_hard_limit": True,
        "supports_swap_bound_or_disable": True,
        "supports_pid_hard_limit": True,
        "supports_cpu_cfs": True,
        "cpuset_cpus": (0, 1),
        "storage_backend": StorageIsolationBackend.BOUNDED_VOLUME,
        "network_backend": NetworkIsolationBackend.CONSTRAINED_PROXY,
        "log_backend": LogIsolationBackend.DOCKER_LOCAL,
    }
    values.update(updates)
    return RuntimeHostCapabilityReport(**values)


def _plan():
    profile = baseline_portal_isolation_profile()
    return RuntimeIsolationResolver().resolve(
        profile=profile,
        expected_profile_digest=profile.digest(),
        report=_report(),
        runtime_image_digest="1" * 64,
        gateway_artifact_digest="2" * 64,
        gateway_contract_version="v1",
        gateway_contract_digest="3" * 64,
        market_data_egress_policy_version="public-data-v1",
        market_data_egress_policy_digest="4" * 64,
        now=NOW,
    )


def test_profile_and_plan_are_immutable_and_digest_stable() -> None:
    profile = baseline_portal_isolation_profile()
    plan = _plan()

    assert profile.digest() == baseline_portal_isolation_profile().digest()
    assert plan.digest() == _plan().digest()
    with pytest.raises(FrozenInstanceError):
        plan.pids_limit = 999


@pytest.mark.parametrize(
    "runtime_user", ["0:1000", "1000:0", "root:1000", "1000:root", "1000", "1000:"]
)
def test_profile_rejects_root_or_non_numeric_runtime_identity(runtime_user: str) -> None:
    with pytest.raises(ValueError, match="non-root numeric uid:gid"):
        replace(baseline_portal_isolation_profile(), runtime_user=runtime_user)


def test_plan_binding_rejects_digest_mismatch() -> None:
    with pytest.raises(ValueError, match="digest"):
        RuntimeIsolationPlanBinding(isolation_plan_digest="f" * 64, plan=_plan())


@pytest.mark.parametrize(
    ("report_updates", "reason_code"),
    [
        ({"supports_pid_hard_limit": False}, "HOST_PID_ISOLATION_UNSUPPORTED"),
        ({"supports_cpu_cfs": False, "cpuset_cpus": ()}, "HOST_CPU_ISOLATION_UNSUPPORTED"),
        ({"storage_backend": None}, "HOST_STORAGE_ISOLATION_UNSUPPORTED"),
        ({"network_backend": None}, "HOST_NETWORK_ISOLATION_UNSUPPORTED"),
        ({"log_backend": None}, "HOST_LOG_ISOLATION_UNSUPPORTED"),
        ({"supports_no_new_privileges": False}, "HOST_INCOMPATIBLE"),
        ({"supports_required_seccomp": False}, "HOST_INCOMPATIBLE"),
    ],
)
def test_resolver_fails_closed_when_required_enforcement_is_unavailable(
    report_updates: dict[str, object],
    reason_code: str,
) -> None:
    profile = baseline_portal_isolation_profile()

    with pytest.raises(RuntimeDriverError) as exc_info:
        RuntimeIsolationResolver().resolve(
            profile=profile,
            expected_profile_digest=profile.digest(),
            report=_report(**report_updates),
            runtime_image_digest="1" * 64,
            gateway_artifact_digest="2" * 64,
            gateway_contract_version="v1",
            gateway_contract_digest="3" * 64,
            market_data_egress_policy_version="public-data-v1",
            market_data_egress_policy_digest="4" * 64,
            now=NOW,
        )

    assert exc_info.value.reason_code == reason_code


def test_resolver_rejects_stale_capability_report() -> None:
    profile = baseline_portal_isolation_profile()
    stale = _report(generated_at=NOW - timedelta(minutes=10))

    with pytest.raises(RuntimeDriverError) as exc_info:
        RuntimeIsolationResolver().resolve(
            profile=profile,
            expected_profile_digest=profile.digest(),
            report=stale,
            runtime_image_digest="1" * 64,
            gateway_artifact_digest="2" * 64,
            gateway_contract_version="v1",
            gateway_contract_digest="3" * 64,
            market_data_egress_policy_version="public-data-v1",
            market_data_egress_policy_digest="4" * 64,
            now=NOW,
        )

    assert exc_info.value.reason_code == "HOST_CAPABILITY_REPORT_STALE"


def test_resolver_rejects_profile_digest_substitution() -> None:
    profile = baseline_portal_isolation_profile()

    with pytest.raises(RuntimeDriverError) as exc_info:
        RuntimeIsolationResolver().resolve(
            profile=profile,
            expected_profile_digest="f" * 64,
            report=_report(),
            runtime_image_digest="1" * 64,
            gateway_artifact_digest="2" * 64,
            gateway_contract_version="v1",
            gateway_contract_digest="3" * 64,
            market_data_egress_policy_version="public-data-v1",
            market_data_egress_policy_digest="4" * 64,
            now=NOW,
        )

    assert exc_info.value.reason_code == "ISOLATION_PLAN_MISMATCH"


def test_cpuset_is_only_used_as_a_profile_approved_hard_fallback() -> None:
    profile = baseline_portal_isolation_profile()
    plan = RuntimeIsolationResolver().resolve(
        profile=profile,
        expected_profile_digest=profile.digest(),
        report=_report(supports_cpu_cfs=False, cpuset_cpus=(2, 3)),
        runtime_image_digest="1" * 64,
        gateway_artifact_digest="2" * 64,
        gateway_contract_version="v1",
        gateway_contract_digest="3" * 64,
        market_data_egress_policy_version="public-data-v1",
        market_data_egress_policy_digest="4" * 64,
        now=NOW,
    )

    assert plan.cpu_mode.value == "CPUSET"
    assert plan.cpuset_cpus == (2,)
