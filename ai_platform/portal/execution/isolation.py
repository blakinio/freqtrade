from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from ai_platform.portal.execution.errors import RuntimeDriverError


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


class CpuIsolationMode(StrEnum):
    CFS = "CFS"
    CPUSET = "CPUSET"


class StorageIsolationBackend(StrEnum):
    PROJECT_QUOTA = "PROJECT_QUOTA"
    BOUNDED_VOLUME = "BOUNDED_VOLUME"


class NetworkIsolationBackend(StrEnum):
    NFTABLES = "NFTABLES"
    EBPF = "EBPF"
    CONSTRAINED_PROXY = "CONSTRAINED_PROXY"


class LogIsolationBackend(StrEnum):
    DOCKER_LOCAL = "DOCKER_LOCAL"


@dataclass(frozen=True)
class RuntimeIsolationProfile:
    """Immutable security semantics; contains no raw Docker/engine arguments."""

    profile_version: str
    cpu_millis: int
    memory_limit_bytes: int
    memory_swap_limit_bytes: int
    pids_limit: int
    durable_state_max_bytes: int
    tmpfs_max_bytes: int
    run_tmpfs_max_bytes: int
    log_max_bytes: int
    log_rotation_count: int
    runtime_user: str = "1000:1000"
    allow_cpuset_fallback: bool = True
    capability_report_max_age_seconds: int = 300

    def __post_init__(self) -> None:
        if not self.profile_version.strip():
            raise ValueError("profile_version must not be empty")
        for name, numeric_value in (
            ("cpu_millis", self.cpu_millis),
            ("memory_limit_bytes", self.memory_limit_bytes),
            ("memory_swap_limit_bytes", self.memory_swap_limit_bytes),
            ("pids_limit", self.pids_limit),
            ("durable_state_max_bytes", self.durable_state_max_bytes),
            ("tmpfs_max_bytes", self.tmpfs_max_bytes),
            ("run_tmpfs_max_bytes", self.run_tmpfs_max_bytes),
            ("log_max_bytes", self.log_max_bytes),
            ("log_rotation_count", self.log_rotation_count),
            ("capability_report_max_age_seconds", self.capability_report_max_age_seconds),
        ):
            if numeric_value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.memory_swap_limit_bytes < self.memory_limit_bytes:
            raise ValueError("memory_swap_limit_bytes cannot be lower than memory_limit_bytes")
        user, separator, group = self.runtime_user.partition(":")
        if (
            separator != ":"
            or not user.isdigit()
            or not group.isdigit()
            or int(user) == 0
            or int(group) == 0
        ):
            raise ValueError("runtime_user must be a non-root numeric uid:gid")

    def digest(self) -> str:
        return _sha256_payload({"schema": "runtime-isolation-profile/v1", **asdict(self)})


@dataclass(frozen=True)
class RuntimeHostCapabilityReport:
    """Point-in-time capability evidence used only for deterministic plan resolution."""

    generated_at: datetime
    host_boot_id: str
    cgroup_mode: str
    cgroup_controllers: tuple[str, ...]
    supports_readonly_root: bool
    supports_tmpfs: bool
    supports_no_new_privileges: bool
    supports_capability_drop: bool
    supports_required_seccomp: bool
    supports_memory_hard_limit: bool
    supports_swap_bound_or_disable: bool
    supports_pid_hard_limit: bool
    supports_cpu_cfs: bool
    cpuset_cpus: tuple[int, ...]
    storage_backend: StorageIsolationBackend | None
    network_backend: NetworkIsolationBackend | None
    log_backend: LogIsolationBackend | None

    def __post_init__(self) -> None:
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if not self.host_boot_id.strip():
            raise ValueError("host_boot_id must not be empty")
        if self.cgroup_mode not in {"v1", "v2"}:
            raise ValueError("cgroup_mode must be v1 or v2")
        if any(cpu < 0 for cpu in self.cpuset_cpus):
            raise ValueError("cpuset_cpus cannot contain negative CPU indexes")

    def digest(self) -> str:
        payload = asdict(self)
        payload["generated_at"] = self.generated_at.astimezone(UTC).isoformat()
        return _sha256_payload({"schema": "runtime-host-capability-report/v1", **payload})


@dataclass(frozen=True)
class RuntimeIsolationPlan:
    plan_schema_version: str
    resolver_version: str
    isolation_profile_version: str
    isolation_profile_digest: str
    cpu_mode: CpuIsolationMode
    cpu_millis: int
    cpuset_cpus: tuple[int, ...]
    memory_limit_bytes: int
    memory_swap_limit_bytes: int
    pids_limit: int
    durable_state_max_bytes: int
    storage_backend: StorageIsolationBackend
    tmpfs_max_bytes: int
    run_tmpfs_max_bytes: int
    log_max_bytes: int
    log_rotation_count: int
    log_backend: LogIsolationBackend
    network_backend: NetworkIsolationBackend
    market_data_egress_policy_version: str
    market_data_egress_policy_digest: str
    seccomp_profile_identity: str
    runtime_user: str
    runtime_image_digest: str
    gateway_artifact_digest: str
    gateway_contract_version: str
    gateway_contract_digest: str

    def __post_init__(self) -> None:
        for name, text_value in (
            ("plan_schema_version", self.plan_schema_version),
            ("resolver_version", self.resolver_version),
            ("isolation_profile_version", self.isolation_profile_version),
            ("market_data_egress_policy_version", self.market_data_egress_policy_version),
            ("seccomp_profile_identity", self.seccomp_profile_identity),
            ("runtime_user", self.runtime_user),
            ("gateway_contract_version", self.gateway_contract_version),
        ):
            if not text_value.strip():
                raise ValueError(f"{name} must not be empty")
        for name, digest in (
            ("isolation_profile_digest", self.isolation_profile_digest),
            ("market_data_egress_policy_digest", self.market_data_egress_policy_digest),
            ("runtime_image_digest", self.runtime_image_digest),
            ("gateway_artifact_digest", self.gateway_artifact_digest),
            ("gateway_contract_digest", self.gateway_contract_digest),
        ):
            _require_sha256(digest, name)
        if self.cpu_millis <= 0:
            raise ValueError("cpu_millis must be positive")
        if self.cpu_mode is CpuIsolationMode.CPUSET and not self.cpuset_cpus:
            raise ValueError("CPUSET mode requires at least one CPU")
        if self.cpu_mode is CpuIsolationMode.CFS and self.cpuset_cpus:
            raise ValueError("CFS mode must not carry cpuset CPU indexes")
        for name, numeric_value in (
            ("memory_limit_bytes", self.memory_limit_bytes),
            ("memory_swap_limit_bytes", self.memory_swap_limit_bytes),
            ("pids_limit", self.pids_limit),
            ("durable_state_max_bytes", self.durable_state_max_bytes),
            ("tmpfs_max_bytes", self.tmpfs_max_bytes),
            ("run_tmpfs_max_bytes", self.run_tmpfs_max_bytes),
            ("log_max_bytes", self.log_max_bytes),
            ("log_rotation_count", self.log_rotation_count),
        ):
            if numeric_value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.memory_swap_limit_bytes < self.memory_limit_bytes:
            raise ValueError("memory_swap_limit_bytes cannot be lower than memory_limit_bytes")

    def digest(self) -> str:
        payload = asdict(self)
        return _sha256_payload({"schema": "runtime-isolation-plan/v1", **payload})


class RuntimeIsolationResolver:
    """Resolve one immutable plan from profile semantics and host capability evidence."""

    resolver_version = "portal-isolation-resolver/v1"
    plan_schema_version = "runtime-isolation-plan/v1"

    def resolve(
        self,
        *,
        profile: RuntimeIsolationProfile,
        expected_profile_digest: str,
        report: RuntimeHostCapabilityReport,
        runtime_image_digest: str,
        gateway_artifact_digest: str,
        gateway_contract_version: str,
        gateway_contract_digest: str,
        market_data_egress_policy_version: str,
        market_data_egress_policy_digest: str,
        now: datetime | None = None,
    ) -> RuntimeIsolationPlan:
        if profile.digest() != expected_profile_digest:
            raise RuntimeDriverError(
                "ISOLATION_PLAN_MISMATCH",
                "runtime isolation profile digest does not match trusted generation binding",
            )

        observed_at = now or datetime.now(UTC)
        max_age = timedelta(seconds=profile.capability_report_max_age_seconds)
        report_age = observed_at - report.generated_at
        report_future_skew = report.generated_at - observed_at
        if report_age > max_age or report_future_skew > timedelta(seconds=5):
            raise RuntimeDriverError(
                "HOST_CAPABILITY_REPORT_STALE",
                "runtime host capability report is stale or from the future",
            )

        if report.cgroup_mode != "v2":
            raise RuntimeDriverError(
                "HOST_INCOMPATIBLE",
                "current effective isolation attestor requires cgroup v2",
            )

        required_flags = (
            report.supports_readonly_root,
            report.supports_tmpfs,
            report.supports_no_new_privileges,
            report.supports_capability_drop,
            report.supports_required_seccomp,
            report.supports_memory_hard_limit,
            report.supports_swap_bound_or_disable,
        )
        if not all(required_flags):
            raise RuntimeDriverError(
                "HOST_INCOMPATIBLE",
                "host cannot enforce mandatory runtime security invariants",
            )
        if not report.supports_pid_hard_limit:
            raise RuntimeDriverError(
                "HOST_PID_ISOLATION_UNSUPPORTED",
                "host cannot enforce the required PID hard bound",
            )

        if report.supports_cpu_cfs:
            cpu_mode = CpuIsolationMode.CFS
            cpuset_cpus: tuple[int, ...] = ()
        elif (
            profile.allow_cpuset_fallback
            and profile.cpu_millis % 1000 == 0
            and len(report.cpuset_cpus) >= profile.cpu_millis // 1000
        ):
            cpu_mode = CpuIsolationMode.CPUSET
            cpuset_cpus = tuple(report.cpuset_cpus[: profile.cpu_millis // 1000])
        else:
            raise RuntimeDriverError(
                "HOST_CPU_ISOLATION_UNSUPPORTED",
                "host cannot enforce the required CPU hard bound",
            )

        if report.storage_backend is None:
            raise RuntimeDriverError(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                "host has no approved durable-state hard-bound backend",
            )
        if report.network_backend is None:
            raise RuntimeDriverError(
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
                "host has no approved market-data egress enforcement backend",
            )
        if report.log_backend is None:
            raise RuntimeDriverError(
                "HOST_LOG_ISOLATION_UNSUPPORTED",
                "host has no approved bounded logging backend",
            )

        return RuntimeIsolationPlan(
            plan_schema_version=self.plan_schema_version,
            resolver_version=self.resolver_version,
            isolation_profile_version=profile.profile_version,
            isolation_profile_digest=expected_profile_digest,
            cpu_mode=cpu_mode,
            cpu_millis=profile.cpu_millis,
            cpuset_cpus=cpuset_cpus,
            memory_limit_bytes=profile.memory_limit_bytes,
            memory_swap_limit_bytes=profile.memory_swap_limit_bytes,
            pids_limit=profile.pids_limit,
            durable_state_max_bytes=profile.durable_state_max_bytes,
            storage_backend=report.storage_backend,
            tmpfs_max_bytes=profile.tmpfs_max_bytes,
            run_tmpfs_max_bytes=profile.run_tmpfs_max_bytes,
            log_max_bytes=profile.log_max_bytes,
            log_rotation_count=profile.log_rotation_count,
            log_backend=report.log_backend,
            network_backend=report.network_backend,
            market_data_egress_policy_version=market_data_egress_policy_version,
            market_data_egress_policy_digest=market_data_egress_policy_digest,
            seccomp_profile_identity="docker-default",
            runtime_user=profile.runtime_user,
            runtime_image_digest=runtime_image_digest,
            gateway_artifact_digest=gateway_artifact_digest,
            gateway_contract_version=gateway_contract_version,
            gateway_contract_digest=gateway_contract_digest,
        )


def baseline_portal_isolation_profile() -> RuntimeIsolationProfile:
    return RuntimeIsolationProfile(
        profile_version="portal-dry-run/v1",
        cpu_millis=1000,
        memory_limit_bytes=512 * 1024 * 1024,
        memory_swap_limit_bytes=512 * 1024 * 1024,
        pids_limit=128,
        durable_state_max_bytes=2 * 1024 * 1024 * 1024,
        tmpfs_max_bytes=64 * 1024 * 1024,
        run_tmpfs_max_bytes=4 * 1024 * 1024,
        log_max_bytes=10 * 1024 * 1024,
        log_rotation_count=3,
    )


@dataclass(frozen=True)
class RuntimeIsolationPlanBinding:
    """Trusted generation binding presented to the engine layer."""

    isolation_plan_digest: str
    plan: RuntimeIsolationPlan

    def __post_init__(self) -> None:
        _require_sha256(self.isolation_plan_digest, "isolation_plan_digest")
        if self.plan.digest() != self.isolation_plan_digest:
            raise ValueError("trusted isolation-plan digest does not match resolved plan")


class RuntimeIsolationPlanProvider:
    """Narrow read-only boundary for generation-bound isolation plans."""

    def resolve(self, runtime_id: str) -> RuntimeIsolationPlanBinding:
        raise NotImplementedError


class MissingRuntimeIsolationPlanProvider(RuntimeIsolationPlanProvider):
    def resolve(self, runtime_id: str) -> RuntimeIsolationPlanBinding:
        del runtime_id
        raise RuntimeDriverError(
            "ISOLATION_PLAN_MISMATCH",
            "no trusted RuntimeIsolationPlan provider is configured",
        )


class MappingRuntimeIsolationPlanProvider(RuntimeIsolationPlanProvider):
    """Immutable mapping helper for composition/tests; callers cannot mutate the stored mapping."""

    def __init__(self, bindings: dict[str, RuntimeIsolationPlanBinding]) -> None:
        self._bindings = dict(bindings)

    def resolve(self, runtime_id: str) -> RuntimeIsolationPlanBinding:
        try:
            return self._bindings[runtime_id]
        except KeyError as exc:
            raise RuntimeDriverError(
                "ISOLATION_PLAN_MISMATCH",
                "runtime has no trusted generation-bound isolation plan",
            ) from exc
