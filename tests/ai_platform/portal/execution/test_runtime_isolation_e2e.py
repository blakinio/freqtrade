# ruff: noqa: S108 -- /tmp is a fixed in-container tmpfs security boundary.

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from ai_platform.portal.execution.driver import (
    DockerCliRuntimeDriver,
    DockerHostCapabilityProbe,
    ExternalIsolationCapabilities,
)
from ai_platform.portal.execution.isolation import (
    MappingRuntimeIsolationPlanProvider,
    NetworkIsolationBackend,
    RuntimeIsolationPlan,
    RuntimeIsolationPlanBinding,
    RuntimeIsolationProfile,
    RuntimeIsolationResolver,
    StorageIsolationBackend,
)
from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec


IMAGE_TAG = "alpine:3.20"


def _run(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _require_e2e_host() -> None:
    if os.environ.get("PORTAL_RUNTIME_ISOLATION_E2E") != "true":
        pytest.skip("real Docker isolation E2E runs only in its dedicated workflow")
    if shutil.which("docker") is None:
        if os.environ.get("CI") == "true":
            pytest.fail("Docker is required for Portal runtime isolation E2E in CI")
        pytest.skip("Docker CLI is not available")
    docker = _run("docker", "info", "--format", "{{.ServerVersion}}", timeout=20)
    if docker.returncode != 0:
        if os.environ.get("CI") == "true":
            pytest.fail(f"Docker daemon is required for isolation E2E: {docker.stderr}")
        pytest.skip("Docker daemon is not available")
    if os.name != "posix" or shutil.which("sudo") is None:
        if os.environ.get("CI") == "true":
            pytest.fail("Linux sudo is required for the bounded-state E2E fixture")
        pytest.skip("bounded-state E2E fixture requires Linux sudo")
    sudo = _run("sudo", "-n", "true", timeout=10)
    if sudo.returncode != 0:
        if os.environ.get("CI") == "true":
            pytest.fail("passwordless sudo is required for the bounded-state E2E fixture")
        pytest.skip("passwordless sudo is unavailable")


def _exact_image() -> tuple[str, str]:
    pulled = _run("docker", "pull", "--quiet", IMAGE_TAG, timeout=180)
    assert pulled.returncode == 0, pulled.stderr
    inspected = _run(
        "docker",
        "image",
        "inspect",
        "--format",
        "{{json .RepoDigests}}",
        IMAGE_TAG,
    )
    assert inspected.returncode == 0, inspected.stderr
    digests = json.loads(inspected.stdout)
    exact = next(
        str(value)
        for value in digests
        if isinstance(value, str) and "@sha256:" in value
    )
    digest = exact.rsplit("@sha256:", 1)[1]
    assert len(digest) == 64
    return exact, digest


class _HardDenyE2EAttestor:
    """Ephemeral hard external controls for real-driver E2E on a CI Linux host.

    The network is intentionally stricter than the production market-data policy:
    a Docker internal network denies all public egress while the application stays
    in quarantine. Production nftables policy semantics are covered separately.
    """

    def __init__(self, state_root: Path) -> None:
        self._state_root = state_root.resolve()
        self._mounted_state: Path | None = None
        self._network: str | None = None

    def capabilities(self) -> ExternalIsolationCapabilities:
        return ExternalIsolationCapabilities(
            storage_backend=StorageIsolationBackend.BOUNDED_VOLUME,
            network_backend=NetworkIsolationBackend.CONSTRAINED_PROXY,
        )

    def prepare_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None:
        resolved = state_path.resolve()
        if resolved != self._state_root:
            raise AssertionError("E2E state path escaped its approved root")
        mounted = _run(
            "sudo",
            "-n",
            "mount",
            "-t",
            "tmpfs",
            "-o",
            f"size={plan.durable_state_max_bytes},nosuid,nodev,noexec",
            "tmpfs",
            str(resolved),
        )
        assert mounted.returncode == 0, mounted.stderr
        owned = _run("sudo", "-n", "chown", "65532:65532", str(resolved))
        assert owned.returncode == 0, owned.stderr
        self._mounted_state = resolved

    def prepare_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        del plan
        created = _run(
            "docker",
            "network",
            "create",
            "--driver",
            "bridge",
            "--internal",
            "--ipv6=false",
            "--label",
            f"ai.portal.runtime_id={runtime_id}",
            network_name,
        )
        assert created.returncode == 0, created.stderr
        self._network = network_name

    def attest_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None:
        mounted = _run("findmnt", "-bno", "FSTYPE,SIZE,OPTIONS", "--target", str(state_path))
        assert mounted.returncode == 0, mounted.stderr
        fields = mounted.stdout.strip().split(maxsplit=2)
        assert len(fields) == 3
        fs_type, size_text, options_text = fields
        assert fs_type == "tmpfs"
        assert int(size_text) <= plan.durable_state_max_bytes
        options = set(options_text.split(","))
        assert {"rw", "nosuid", "nodev", "noexec"}.issubset(options)

    def attest_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        del plan
        inspected = _run("docker", "network", "inspect", network_name)
        assert inspected.returncode == 0, inspected.stderr
        payload = json.loads(inspected.stdout)[0]
        assert payload["Internal"] is True
        assert payload["EnableIPv6"] is False
        assert payload["Labels"]["ai.portal.runtime_id"] == runtime_id
        containers = payload.get("Containers") or {}
        assert set(containers) == {self._container_id(runtime_id)}

    def cleanup_network(self, network_name: str, runtime_id: str) -> None:
        del runtime_id
        removed = _run("docker", "network", "rm", network_name)
        if removed.returncode == 0 or "not found" in removed.stderr.lower():
            self._network = None
            return
        raise AssertionError(removed.stderr)

    def cleanup(self, runtime_id: str) -> None:
        _run("docker", "rm", "-f", runtime_id)
        if self._network is not None:
            _run("docker", "network", "rm", self._network)
            self._network = None
        if self._mounted_state is not None:
            unmounted = _run("sudo", "-n", "umount", str(self._mounted_state))
            assert unmounted.returncode == 0, unmounted.stderr
            self._mounted_state = None

    @staticmethod
    def _container_id(runtime_id: str) -> str:
        inspected = _run("docker", "inspect", "--format", "{{.Id}}", runtime_id)
        assert inspected.returncode == 0, inspected.stderr
        return inspected.stdout.strip()


def _plan(
    image_digest: str,
    attestor: _HardDenyE2EAttestor,
) -> RuntimeIsolationPlan:
    profile = RuntimeIsolationProfile(
        profile_version="portal-e2e-v1",
        cpu_millis=500,
        memory_limit_bytes=64 * 1024 * 1024,
        memory_swap_limit_bytes=64 * 1024 * 1024,
        pids_limit=32,
        durable_state_max_bytes=8 * 1024 * 1024,
        tmpfs_max_bytes=8 * 1024 * 1024,
        run_tmpfs_max_bytes=2 * 1024 * 1024,
        log_max_bytes=1024 * 1024,
        log_rotation_count=2,
        runtime_user="65532:65532",
        allow_cpuset_fallback=False,
    )
    report = DockerHostCapabilityProbe(external_attestor=attestor).probe(
        now=datetime.now(UTC)
    )
    return RuntimeIsolationResolver().resolve(
        profile=profile,
        expected_profile_digest=profile.digest(),
        report=report,
        runtime_image_digest=image_digest,
        gateway_artifact_digest="2" * 64,
        gateway_contract_version="e2e-v1",
        gateway_contract_digest="3" * 64,
        market_data_egress_policy_version="e2e-hard-deny-v1",
        market_data_egress_policy_digest="4" * 64,
        now=report.generated_at,
    )


def test_real_docker_driver_provisions_attested_quarantine(tmp_path: Path) -> None:
    _require_e2e_host()
    exact_image, image_digest = _exact_image()
    runtime_id = f"portal-isolation-e2e-{uuid4().hex[:12]}"
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    config_path = inputs / "config.json"
    config_path.write_text("{}\n", encoding="utf-8")
    state_path = tmp_path / "state"
    state_path.mkdir()
    attestor = _HardDenyE2EAttestor(state_path)
    plan = _plan(image_digest, attestor)
    provider = MappingRuntimeIsolationPlanProvider(
        {
            runtime_id: RuntimeIsolationPlanBinding(
                isolation_plan_digest=plan.digest(),
                plan=plan,
            )
        }
    )
    spec = RuntimeContainerSpec(
        runtime_id=runtime_id,
        image=exact_image,
        config_path=config_path,
        state_path=state_path,
        strategy_name="PortalE2EStrategy",
        labels={"ai.portal.test": "runtime-isolation-e2e"},
    )
    driver = DockerCliRuntimeDriver(
        isolation_plans=provider,
        external_attestor=attestor,
    )

    try:
        assert driver.provision(spec) is DriverRuntimeState.CREATED
        assert driver.inspect(runtime_id) is DriverRuntimeState.CREATED

        release_gate = _run(
            "docker",
            "exec",
            runtime_id,
            "test",
            "-f",
            "/run/portal-release/release",
        )
        assert release_gate.returncode == 1

        config_write = _run(
            "docker",
            "exec",
            runtime_id,
            "/bin/sh",
            "-ec",
            "echo tamper > /runtime/config/config.json",
        )
        assert config_write.returncode != 0

        state_write = _run(
            "docker",
            "exec",
            runtime_id,
            "/bin/sh",
            "-ec",
            "printf ok > /runtime/state/write-probe",
        )
        assert state_write.returncode == 0, state_write.stderr
        state_overflow = _run(
            "docker",
            "exec",
            runtime_id,
            "/bin/sh",
            "-ec",
            "dd if=/dev/zero of=/runtime/state/quota-probe bs=1048576 count=12",
        )
        assert state_overflow.returncode != 0
        assert "No space left on device" in state_overflow.stderr

        wget_available = _run(
            "docker",
            "exec",
            runtime_id,
            "/bin/sh",
            "-ec",
            "command -v wget",
        )
        assert wget_available.returncode == 0, wget_available.stderr
        public_egress = _run(
            "docker",
            "exec",
            runtime_id,
            "/bin/sh",
            "-ec",
            "wget -q -T 2 -O /dev/null http://1.1.1.1",
            timeout=10,
        )
        assert public_egress.returncode != 0
    finally:
        attestor.cleanup(runtime_id)
