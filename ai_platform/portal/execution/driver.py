# ruff: noqa: S108 -- /tmp is a fixed in-container tmpfs security boundary.

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.isolation import (
    CpuIsolationMode,
    LogIsolationBackend,
    MissingRuntimeIsolationPlanProvider,
    NetworkIsolationBackend,
    RuntimeHostCapabilityReport,
    RuntimeIsolationPlan,
    RuntimeIsolationPlanProvider,
    StorageIsolationBackend,
)
from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner(Protocol):
    def run(self, args: Sequence[str]) -> CommandResult: ...


class SubprocessCommandRunner:
    def run(self, args: Sequence[str]) -> CommandResult:
        completed = subprocess.run(
            list(args),
            check=False,
            capture_output=True,
            text=True,
        )
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


@dataclass(frozen=True)
class ExternalIsolationCapabilities:
    storage_backend: StorageIsolationBackend | None = None
    network_backend: NetworkIsolationBackend | None = None


class ExternalIsolationAttestor(Protocol):
    """Approved host-specific hard storage/network enforcement boundary."""

    def capabilities(self) -> ExternalIsolationCapabilities: ...

    def prepare_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None: ...

    def prepare_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None: ...

    def attest_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None: ...

    def attest_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None: ...

    def cleanup_network(self, network_name: str, runtime_id: str) -> None: ...


class FailClosedExternalIsolationAttestor:
    def capabilities(self) -> ExternalIsolationCapabilities:
        return ExternalIsolationCapabilities()

    def prepare_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None:
        del plan, state_path
        raise RuntimeDriverError(
            "HOST_STORAGE_ISOLATION_UNSUPPORTED",
            "no approved durable-state hard-bound backend is configured",
        )

    def prepare_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        del plan, network_name, runtime_id
        raise RuntimeDriverError(
            "HOST_NETWORK_ISOLATION_UNSUPPORTED",
            "no approved market-data egress enforcement backend is configured",
        )

    def attest_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None:
        del plan, state_path
        raise RuntimeDriverError(
            "HOST_STORAGE_ISOLATION_UNSUPPORTED",
            "durable-state hard-bound enforcement cannot be attested",
        )

    def attest_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        del plan, network_name, runtime_id
        raise RuntimeDriverError(
            "HOST_NETWORK_ISOLATION_UNSUPPORTED",
            "market-data egress enforcement cannot be attested",
        )

    def cleanup_network(self, network_name: str, runtime_id: str) -> None:
        del network_name, runtime_id


class DockerHostCapabilityProbe:
    """Collect generic Docker/cgroup evidence without inventing external enforcement."""

    def __init__(
        self,
        runner: CommandRunner | None = None,
        *,
        external_attestor: ExternalIsolationAttestor | None = None,
        cgroup_root: Path = Path("/sys/fs/cgroup"),
        boot_id_path: Path = Path("/proc/sys/kernel/random/boot_id"),
        proc_swaps_path: Path = Path("/proc/swaps"),
    ) -> None:
        self._runner = runner or SubprocessCommandRunner()
        self._external = external_attestor or FailClosedExternalIsolationAttestor()
        self._cgroup_root = cgroup_root
        self._boot_id_path = boot_id_path
        self._proc_swaps_path = proc_swaps_path

    def probe(self, *, now: datetime | None = None) -> RuntimeHostCapabilityReport:
        security = self._docker_json("{{json .SecurityOptions}}")
        log_plugins = self._docker_json("{{json .Plugins.Log}}")
        if not isinstance(security, list) or not isinstance(log_plugins, list):
            raise RuntimeDriverError(
                "HOST_INCOMPATIBLE",
                "Docker capability evidence has an unexpected shape",
            )
        mode, controllers = self._cgroup_capabilities()
        external = self._external.capabilities()
        cpuset = self._cpuset_cpus(mode)
        security_options = {str(option).lower() for option in security}
        return RuntimeHostCapabilityReport(
            generated_at=now or datetime.now(UTC),
            host_boot_id=self._boot_id(),
            cgroup_mode=mode,
            cgroup_controllers=tuple(sorted(controllers)),
            supports_readonly_root=True,
            supports_tmpfs=True,
            supports_no_new_privileges=True,
            supports_capability_drop=True,
            supports_required_seccomp=any(
                "name=seccomp" in option and "profile=builtin" in option
                for option in security_options
            ),
            supports_memory_hard_limit="memory" in controllers,
            supports_swap_bound_or_disable=self._swap_control_available(mode),
            supports_pid_hard_limit="pids" in controllers,
            supports_cpu_cfs="cpu" in controllers,
            cpuset_cpus=cpuset if "cpuset" in controllers else (),
            storage_backend=external.storage_backend,
            network_backend=external.network_backend,
            log_backend=(
                LogIsolationBackend.DOCKER_LOCAL
                if "local" in {str(plugin) for plugin in log_plugins}
                else None
            ),
        )

    def _docker_json(self, template: str) -> object:
        result = self._runner.run(("docker", "info", "--format", template))
        if result.returncode != 0:
            raise RuntimeDriverError(
                "HOST_INCOMPATIBLE",
                result.stderr.strip() or "Docker capability discovery failed",
            )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeDriverError(
                "HOST_INCOMPATIBLE",
                "Docker capability discovery returned invalid JSON",
            ) from exc

    def _cgroup_capabilities(self) -> tuple[str, set[str]]:
        v2 = self._cgroup_root / "cgroup.controllers"
        if v2.exists():
            return "v2", set(v2.read_text(encoding="utf-8").split())
        controllers = {
            name
            for name in ("cpu", "cpuset", "memory", "pids")
            if (self._cgroup_root / name).exists()
        }
        return "v1", controllers

    def _swap_control_available(self, mode: str) -> bool:
        if mode == "v2":
            if (self._cgroup_root / "memory.swap.max").exists():
                return True
        elif (self._cgroup_root / "memory" / "memory.memsw.limit_in_bytes").exists():
            return True
        return self._host_swap_disabled()

    def _host_swap_disabled(self) -> bool:
        try:
            lines = [
                line.strip()
                for line in self._proc_swaps_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except OSError:
            return False
        if not lines:
            return True
        header = lines[0].lower()
        if not header.startswith("filename") or "type" not in header or "size" not in header:
            return False
        return len(lines) == 1

    def _cpuset_cpus(self, mode: str) -> tuple[int, ...]:
        path = (
            self._cgroup_root / "cpuset.cpus.effective"
            if mode == "v2"
            else self._cgroup_root / "cpuset" / "cpuset.cpus"
        )
        if not path.exists():
            return ()
        return self._parse_cpu_set(path.read_text(encoding="utf-8").strip())

    def _boot_id(self) -> str:
        try:
            value = self._boot_id_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeDriverError(
                "HOST_INCOMPATIBLE",
                "host reboot identity is unavailable",
            ) from exc
        if not value:
            raise RuntimeDriverError("HOST_INCOMPATIBLE", "host reboot identity is empty")
        return value

    @staticmethod
    def _parse_cpu_set(value: str) -> tuple[int, ...]:
        cpus: list[int] = []
        for fragment in filter(None, value.split(",")):
            if "-" in fragment:
                start, end = fragment.split("-", 1)
                cpus.extend(range(int(start), int(end) + 1))
            else:
                cpus.append(int(fragment))
        return tuple(sorted(set(cpus)))


class DockerCliRuntimeDriver:
    """Transitional #1354 engine with a fixed pre-application quarantine."""

    _RELEASE_DIR = "/run/portal-release"
    _RELEASE_FILE = f"{_RELEASE_DIR}/release"
    _QUARANTINE = (
        "set -eu; "
        f"mkdir -p {_RELEASE_DIR}; "
        f"while [ ! -f {_RELEASE_FILE} ]; do sleep 0.05; done; "
        'exec "$@"'
    )
    _RELEASE = f"set -eu; umask 077; : > {_RELEASE_FILE}"

    def __init__(
        self,
        runner: CommandRunner | None = None,
        *,
        isolation_plans: RuntimeIsolationPlanProvider | None = None,
        external_attestor: ExternalIsolationAttestor | None = None,
    ) -> None:
        self._runner = runner or SubprocessCommandRunner()
        self._plans = isolation_plans or MissingRuntimeIsolationPlanProvider()
        self._external = external_attestor or FailClosedExternalIsolationAttestor()
        self._attested: set[str] = set()
        self._released: set[str] = set()
        self._fingerprints: dict[str, str] = {}
        self._networks: dict[str, str] = {}

    def provision(self, spec: RuntimeContainerSpec) -> DriverRuntimeState:
        binding = self._plans.resolve(spec.runtime_id)
        plan = binding.plan
        self._require_plan_matches_spec(plan, spec)
        fingerprint = self._fingerprint(spec, binding.isolation_plan_digest)
        current = self.inspect(spec.runtime_id)
        if current is not DriverRuntimeState.MISSING:
            if self._fingerprints.get(spec.runtime_id) != fingerprint:
                raise RuntimeDriverError(
                    "GENERATION_SPEC_CONFLICT",
                    "existing runtime does not match the trusted generation spec",
                )
            return current

        network = self._network_name(spec.runtime_id)
        self._external.prepare_storage(plan, spec.state_path)
        self._external.prepare_network(plan, network, spec.runtime_id)
        try:
            self._require_image_present(spec.image, plan.runtime_image_digest)
            self._require_success(self._create_args(spec, plan, network), "DOCKER_CREATE_FAILED")
            self._attest_structural(spec, plan, network)
            self._require_success(("docker", "start", spec.runtime_id), "DOCKER_START_FAILED")
            self._attest_effective(spec, plan, network)
        except Exception:
            self._cleanup_failed_runtime(spec.runtime_id, network)
            raise

        self._attested.add(spec.runtime_id)
        self._fingerprints[spec.runtime_id] = fingerprint
        self._networks[spec.runtime_id] = network
        return DriverRuntimeState.CREATED

    def start(self, runtime_id: str) -> DriverRuntimeState:
        current = self.inspect(runtime_id)
        if current is DriverRuntimeState.RUNNING:
            if runtime_id not in self._released:
                self._release_forbidden("running runtime has no current release evidence")
            return current
        if current is DriverRuntimeState.PAUSED:
            if runtime_id not in self._released:
                self._release_forbidden("paused runtime has no current release evidence")
            self._require_success(("docker", "unpause", runtime_id), "DOCKER_UNPAUSE_FAILED")
            return DriverRuntimeState.RUNNING
        if current is DriverRuntimeState.CREATED:
            if runtime_id not in self._attested:
                self._release_forbidden("runtime has no successful isolation attestation")
            self._release(runtime_id)
            return DriverRuntimeState.RUNNING
        if current is DriverRuntimeState.STOPPED:
            self._release_forbidden(
                "stopped runtime requires #1355 durable Supervisor reconciliation"
            )
        if current is DriverRuntimeState.MISSING:
            raise RuntimeDriverError("RUNTIME_MISSING", "runtime container does not exist")
        return current

    def pause(self, runtime_id: str) -> DriverRuntimeState:
        current = self.inspect(runtime_id)
        if current is DriverRuntimeState.PAUSED:
            return current
        if current is DriverRuntimeState.RUNNING:
            self._require_success(("docker", "pause", runtime_id), "DOCKER_PAUSE_FAILED")
            return DriverRuntimeState.PAUSED
        if current is DriverRuntimeState.MISSING:
            raise RuntimeDriverError("RUNTIME_MISSING", "runtime container does not exist")
        return current

    def stop(self, runtime_id: str) -> DriverRuntimeState:
        current = self.inspect(runtime_id)
        if current is DriverRuntimeState.STOPPED:
            return current
        if current in {
            DriverRuntimeState.CREATED,
            DriverRuntimeState.RUNNING,
            DriverRuntimeState.PAUSED,
        }:
            self._require_success(("docker", "stop", runtime_id), "DOCKER_STOP_FAILED")
            self._released.discard(runtime_id)
            self._attested.discard(runtime_id)
            return DriverRuntimeState.STOPPED
        if current is DriverRuntimeState.MISSING:
            raise RuntimeDriverError("RUNTIME_MISSING", "runtime container does not exist")
        return current

    def inspect(self, runtime_id: str) -> DriverRuntimeState:
        result = self._runner.run(
            ("docker", "inspect", "--format", "{{.State.Status}}", runtime_id)
        )
        if result.returncode != 0:
            if "no such object" in result.stderr.lower():
                return DriverRuntimeState.MISSING
            raise RuntimeDriverError(
                "DOCKER_INSPECT_FAILED",
                result.stderr.strip() or "docker inspect failed",
            )
        state = result.stdout.strip().lower()
        if state == "running":
            gate = self._runner.run(
                ("docker", "exec", runtime_id, "test", "-f", self._RELEASE_FILE)
            )
            if gate.returncode == 0:
                return DriverRuntimeState.RUNNING
            if gate.returncode == 1:
                return DriverRuntimeState.CREATED
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                gate.stderr.strip() or "quarantine state is unreadable",
            )
        states = {
            "created": DriverRuntimeState.CREATED,
            "restarting": DriverRuntimeState.STARTING,
            "paused": DriverRuntimeState.PAUSED,
            "exited": DriverRuntimeState.STOPPED,
            "dead": DriverRuntimeState.STOPPED,
        }
        try:
            return states[state]
        except KeyError as exc:
            raise RuntimeDriverError(
                "DOCKER_STATE_UNKNOWN",
                f"unsupported docker runtime state: {state or '<empty>'}",
            ) from exc

    def _create_args(
        self,
        spec: RuntimeContainerSpec,
        plan: RuntimeIsolationPlan,
        network: str,
    ) -> tuple[str, ...]:
        args = [
            "docker",
            "create",
            "--name",
            spec.runtime_id,
            "--restart",
            "no",
            "--user",
            plan.runtime_user,
            "--read-only",
            "--security-opt",
            "no-new-privileges=true",
            "--cap-drop",
            "ALL",
            "--pids-limit",
            str(plan.pids_limit),
            "--memory",
            str(plan.memory_limit_bytes),
            "--memory-swap",
            str(plan.memory_swap_limit_bytes),
        ]
        if plan.cpu_mode is CpuIsolationMode.CFS:
            args.extend(("--cpus", self._cpu_value(plan.cpu_millis)))
        else:
            cpus = ",".join(str(cpu) for cpu in plan.cpuset_cpus)
            args.extend(("--cpuset-cpus", cpus))
        args.extend(
            (
                "--tmpfs",
                f"/tmp:rw,noexec,nosuid,nodev,size={plan.tmpfs_max_bytes},mode=1777",
                "--tmpfs",
                f"/run:rw,noexec,nosuid,nodev,size={plan.run_tmpfs_max_bytes},mode=1777",
                "--log-driver",
                "local",
                "--log-opt",
                f"max-size={plan.log_max_bytes}",
                "--log-opt",
                f"max-file={plan.log_rotation_count}",
                "--network",
                network,
            )
        )
        for key, value in sorted(spec.labels.items()):
            args.extend(("--label", f"{key}={value}"))
        args.extend(
            (
                "--label",
                f"ai.portal.isolation_plan_digest={plan.digest()}",
                "--mount",
                f"type=bind,source={spec.config_path.parent},target=/runtime/config,readonly",
                "--mount",
                f"type=bind,source={spec.state_path},target=/runtime/state",
                "--entrypoint",
                "/bin/sh",
                spec.image,
                "-ec",
                self._QUARANTINE,
                "portal-quarantine",
                "freqtrade",
                "trade",
                "--config",
                "/runtime/config/config.json",
                "--strategy",
                spec.strategy_name,
            )
        )
        return tuple(args)

    def _attest_structural(
        self,
        spec: RuntimeContainerSpec,
        plan: RuntimeIsolationPlan,
        network: str,
    ) -> None:
        info = self._inspect_json(spec.runtime_id)
        config = info.get("Config") or {}
        host = info.get("HostConfig") or {}
        errors: list[str] = []

        def check(condition: bool, marker: str) -> None:
            if not condition:
                errors.append(marker)

        security = {str(value).lower() for value in host.get("SecurityOpt") or []}
        labels_raw = config.get("Labels")
        labels = labels_raw if isinstance(labels_raw, dict) else {}
        expected_command = [
            "-ec",
            self._QUARANTINE,
            "portal-quarantine",
            "freqtrade",
            "trade",
            "--config",
            "/runtime/config/config.json",
            "--strategy",
            spec.strategy_name,
        ]
        check(config.get("User") == plan.runtime_user, "non-root-user")
        check(config.get("Image") == spec.image, "exact-image")
        check(config.get("Entrypoint") == ["/bin/sh"], "quarantine-entrypoint")
        check(config.get("Cmd") == expected_command, "quarantine-command")
        check(isinstance(labels_raw, dict), "labels")
        for key, value in sorted(spec.labels.items()):
            check(labels.get(key) == value, f"label:{key}")
        check(
            labels.get("ai.portal.isolation_plan_digest") == plan.digest(),
            "isolation-plan-label",
        )
        check(host.get("Privileged") is False, "privileged=false")
        check(host.get("ReadonlyRootfs") is True, "read-only-root")
        check(any("no-new-privileges" in item for item in security), "no-new-privileges")
        check(not any("seccomp=unconfined" in item for item in security), "seccomp")
        check("ALL" in {str(value).upper() for value in host.get("CapDrop") or []}, "caps")
        check(not host.get("CapAdd"), "cap-add-none")
        check(host.get("PidMode") != "host", "private-pid")
        check(host.get("IpcMode") != "host", "private-ipc")
        check(host.get("UTSMode") != "host", "private-uts")
        check(host.get("NetworkMode") == network, "generation-network")
        check(not host.get("Devices"), "no-devices")
        check(not host.get("PortBindings"), "no-published-ports")
        check((host.get("RestartPolicy") or {}).get("Name") in {"", "no"}, "restart=no")
        check(host.get("Memory") == plan.memory_limit_bytes, "memory")
        check(host.get("MemorySwap") == plan.memory_swap_limit_bytes, "swap")
        check(host.get("PidsLimit") == plan.pids_limit, "pids")
        if plan.cpu_mode is CpuIsolationMode.CFS:
            check(host.get("NanoCpus") == plan.cpu_millis * 1_000_000, "cpu")
        else:
            expected = ",".join(str(cpu) for cpu in plan.cpuset_cpus)
            check(host.get("CpusetCpus") == expected, "cpuset")
        logs = host.get("LogConfig") or {}
        log_options = logs.get("Config") or {}
        check(logs.get("Type") == "local", "log-driver")
        check(str(log_options.get("max-size")) == str(plan.log_max_bytes), "log-size")
        check(
            str(log_options.get("max-file")) == str(plan.log_rotation_count),
            "log-rotation",
        )
        tmpfs = host.get("Tmpfs") or {}
        check(self._tmpfs_matches(tmpfs.get("/tmp"), plan.tmpfs_max_bytes), "tmpfs-/tmp")
        check(self._tmpfs_matches(tmpfs.get("/run"), plan.run_tmpfs_max_bytes), "tmpfs-/run")
        self._attest_mounts(info, spec, errors)
        if errors:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "structural isolation attestation failed: " + ",".join(sorted(errors)),
            )

    def _attest_mounts(
        self,
        info: dict[str, Any],
        spec: RuntimeContainerSpec,
        errors: list[str],
    ) -> None:
        expected = {
            "/runtime/config": (str(spec.config_path.parent.resolve()), False),
            "/runtime/state": (str(spec.state_path.resolve()), True),
        }
        observed: dict[str, tuple[str, bool]] = {}
        for raw in info.get("Mounts", []):
            if not isinstance(raw, dict):
                continue
            destination = str(raw.get("Destination", ""))
            if str(raw.get("Type", "")) == "tmpfs" and destination in {"/tmp", "/run"}:
                continue
            source = str(raw.get("Source", ""))
            observed[destination] = (source, bool(raw.get("RW", False)))
            if "docker.sock" in source:
                errors.append("container-engine-socket")
        for destination, expected_mount in expected.items():
            if observed.get(destination) != expected_mount:
                errors.append(f"mount:{destination}")
        if set(observed) - set(expected):
            errors.append("arbitrary-mount")

    def _attest_effective(
        self,
        spec: RuntimeContainerSpec,
        plan: RuntimeIsolationPlan,
        network: str,
    ) -> None:
        process = self._runner.run(
            (
                "docker",
                "exec",
                spec.runtime_id,
                "/bin/sh",
                "-ec",
                (
                    'test "$(id -u)" != 0; '
                    "grep -Eq '^NoNewPrivs:[[:space:]]*1$' /proc/1/status; "
                    "grep -Eq '^Seccomp:[[:space:]]*2$' /proc/1/status; "
                    "grep -Eq '^CapEff:[[:space:]]*0+$' /proc/1/status; "
                    "! touch /portal-root-write-probe 2>/dev/null"
                ),
            )
        )
        self._require_probe(process, "process/root")
        cgroup = self._runner.run(
            (
                "docker",
                "exec",
                spec.runtime_id,
                "/bin/sh",
                "-ec",
                (
                    'printf "memory="; cat /sys/fs/cgroup/memory.max; '
                    'printf "swap="; '
                    "if [ -f /sys/fs/cgroup/memory.swap.max ]; then "
                    "cat /sys/fs/cgroup/memory.swap.max; "
                    'elif [ "$(wc -l < /proc/swaps)" -le 1 ]; then '
                    'printf "host-disabled\\n"; '
                    "else exit 72; fi; "
                    'printf "pids="; cat /sys/fs/cgroup/pids.max; '
                    'printf "cpu="; cat /sys/fs/cgroup/cpu.max; '
                    'printf "cpuset="; cat /sys/fs/cgroup/cpuset.cpus 2>/dev/null || true'
                ),
            )
        )
        self._require_probe(cgroup, "cgroup")
        self._attest_cgroup(cgroup.stdout, plan)
        mounts = self._runner.run(
            ("docker", "exec", spec.runtime_id, "/bin/sh", "-ec", "cat /proc/mounts")
        )
        self._require_probe(mounts, "mounts")
        self._attest_readonly_root(mounts.stdout)
        self._attest_tmpfs(mounts.stdout, plan)
        self._external.attest_storage(plan, spec.state_path)
        self._external.attest_network(plan, network, spec.runtime_id)

    def _attest_cgroup(self, output: str, plan: RuntimeIsolationPlan) -> None:
        values = dict(line.split("=", 1) for line in output.splitlines() if "=" in line)
        try:
            memory = int(values["memory"])
            swap_raw = values["swap"]
            swap = 0 if swap_raw == "host-disabled" else int(swap_raw)
            pids = int(values["pids"])
        except (KeyError, ValueError) as exc:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "effective cgroup evidence is incomplete",
            ) from exc
        expected_swap = plan.memory_swap_limit_bytes - plan.memory_limit_bytes
        if (memory, swap, pids) != (
            plan.memory_limit_bytes,
            expected_swap,
            plan.pids_limit,
        ):
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "effective memory/swap/PID bounds do not match isolation plan",
            )
        if plan.cpu_mode is CpuIsolationMode.CFS:
            fields = values.get("cpu", "").split()
            try:
                quota, period = int(fields[0]), int(fields[1])
            except (IndexError, ValueError) as exc:
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    "effective CPU evidence is incomplete",
                ) from exc
            if quota * 1000 != plan.cpu_millis * period:
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    "effective CPU bound does not match isolation plan",
                )
        elif self._parse_cpu_set(values.get("cpuset", "")) != plan.cpuset_cpus:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "effective CPUSET bound does not match isolation plan",
            )

    @staticmethod
    def _attest_readonly_root(mounts: str) -> None:
        for line in mounts.splitlines():
            fields = line.split()
            if len(fields) >= 4 and fields[1] == "/":
                options = set(fields[3].split(","))
                if "ro" in options and "rw" not in options:
                    return
                break
        raise RuntimeDriverError(
            "ISOLATION_ATTESTATION_FAILED",
            "effective root filesystem is not read-only",
        )

    def _attest_tmpfs(self, mounts: str, plan: RuntimeIsolationPlan) -> None:
        for destination, maximum in (
            ("/tmp", plan.tmpfs_max_bytes),
            ("/run", plan.run_tmpfs_max_bytes),
        ):
            options = self._mount_options(mounts, destination)
            if options is None or not {"rw", "noexec", "nosuid", "nodev"}.issubset(options):
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    f"{destination} tmpfs security options are not effective",
                )
            size = self._size_option_bytes(options)
            if size is None or size > maximum:
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    f"{destination} tmpfs hard size bound is not effective",
                )

    def _require_plan_matches_spec(
        self,
        plan: RuntimeIsolationPlan,
        spec: RuntimeContainerSpec,
    ) -> None:
        if not spec.image.endswith(f"@sha256:{plan.runtime_image_digest}"):
            raise RuntimeDriverError(
                "ISOLATION_PLAN_MISMATCH",
                "runtime image does not match generation-bound isolation plan",
            )
        if plan.log_backend is not LogIsolationBackend.DOCKER_LOCAL:
            raise RuntimeDriverError(
                "HOST_LOG_ISOLATION_UNSUPPORTED",
                "Docker CLI driver supports only bounded local logging",
            )

    def _require_image_present(self, image: str, digest: str) -> None:
        result = self._runner.run(
            ("docker", "image", "inspect", "--format", "{{json .RepoDigests}}", image)
        )
        if result.returncode != 0:
            raise RuntimeDriverError(
                "IMAGE_NOT_PRESENT",
                result.stderr.strip() or "exact runtime image is not present",
            )
        try:
            repo_digests = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "runtime image identity evidence is invalid JSON",
            ) from exc
        suffix = f"@sha256:{digest}"
        if not isinstance(repo_digests, list) or not any(
            str(value).endswith(suffix) for value in repo_digests
        ):
            raise RuntimeDriverError(
                "ISOLATION_PLAN_MISMATCH",
                "present runtime image content does not match trusted digest",
            )

    def _inspect_json(self, runtime_id: str) -> dict[str, Any]:
        result = self._runner.run(("docker", "inspect", runtime_id))
        if result.returncode != 0:
            raise RuntimeDriverError(
                "DOCKER_INSPECT_FAILED",
                result.stderr.strip() or "docker inspect failed",
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "Docker structural evidence is invalid JSON",
            ) from exc
        if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "Docker structural evidence has an unexpected shape",
            )
        return payload[0]

    def _release(self, runtime_id: str) -> None:
        self._require_success(
            ("docker", "exec", runtime_id, "/bin/sh", "-ec", self._RELEASE),
            "APPLICATION_RELEASE_FORBIDDEN",
        )
        self._released.add(runtime_id)

    def _cleanup_failed_runtime(self, runtime_id: str, network: str) -> None:
        errors: list[str] = []
        try:
            remove = self._runner.run(("docker", "rm", "-f", runtime_id))
            if remove.returncode != 0 and "no such" not in remove.stderr.lower():
                errors.append(remove.stderr.strip() or "docker container cleanup failed")
        except Exception as exc:  # pragma: no cover - defensive adapter boundary
            errors.append(f"docker container cleanup raised {type(exc).__name__}: {exc}")
        try:
            self._external.cleanup_network(network, runtime_id)
        except Exception as exc:  # pragma: no cover - concrete backends are unit-tested
            errors.append(f"network cleanup raised {type(exc).__name__}: {exc}")
        finally:
            self._attested.discard(runtime_id)
            self._released.discard(runtime_id)
            self._fingerprints.pop(runtime_id, None)
            self._networks.pop(runtime_id, None)
        if errors:
            raise RuntimeDriverError(
                "RUNTIME_CLEANUP_FAILED",
                "runtime cleanup was incomplete: " + "; ".join(errors),
            )

    def _require_success(self, args: Sequence[str], reason_code: str) -> None:
        result = self._runner.run(args)
        if result.returncode != 0:
            raise RuntimeDriverError(
                reason_code,
                result.stderr.strip() or f"command failed: {args[1]}",
            )

    @staticmethod
    def _require_probe(result: CommandResult, area: str) -> None:
        if result.returncode != 0:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                result.stderr.strip() or f"effective {area} attestation failed",
            )

    @staticmethod
    def _release_forbidden(message: str) -> None:
        raise RuntimeDriverError("APPLICATION_RELEASE_FORBIDDEN", message)

    @staticmethod
    def _fingerprint(spec: RuntimeContainerSpec, plan_digest: str) -> str:
        payload = "\0".join(
            (
                spec.runtime_id,
                spec.image,
                str(spec.config_path.resolve()),
                str(spec.state_path.resolve()),
                spec.strategy_name,
                plan_digest,
            )
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _network_name(runtime_id: str) -> str:
        digest = hashlib.sha256(f"network\0{runtime_id}".encode()).hexdigest()[:24]
        return f"portal-net-{digest}"

    @staticmethod
    def _cpu_value(cpu_millis: int) -> str:
        whole, fraction = divmod(cpu_millis, 1000)
        if fraction == 0:
            return str(whole)
        return f"{whole}.{fraction:03d}".rstrip("0")

    @staticmethod
    def _tmpfs_matches(value: object, maximum: int) -> bool:
        if not isinstance(value, str):
            return False
        options = {item.strip() for item in value.split(",")}
        required = {"rw", "noexec", "nosuid", "nodev", f"size={maximum}"}
        return required.issubset(options)

    @staticmethod
    def _mount_options(mounts: str, destination: str) -> set[str] | None:
        for line in mounts.splitlines():
            fields = line.split()
            if len(fields) >= 4 and fields[1] == destination and fields[2] == "tmpfs":
                return set(fields[3].split(","))
        return None

    @staticmethod
    def _size_option_bytes(options: set[str]) -> int | None:
        for option in options:
            if not option.startswith("size="):
                continue
            value = option.removeprefix("size=").lower()
            multiplier = 1
            if value.endswith("k"):
                multiplier, value = 1024, value[:-1]
            elif value.endswith("m"):
                multiplier, value = 1024 * 1024, value[:-1]
            elif value.endswith("g"):
                multiplier, value = 1024 * 1024 * 1024, value[:-1]
            try:
                return int(value) * multiplier
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_cpu_set(value: str) -> tuple[int, ...]:
        return DockerHostCapabilityProbe._parse_cpu_set(value)
