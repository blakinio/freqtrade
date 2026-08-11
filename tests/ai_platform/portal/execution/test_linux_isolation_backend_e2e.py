from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from ai_platform.portal.execution.driver import SubprocessCommandRunner
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.host_isolation import (
    LinuxNftablesBtrfsIsolationAttestor,
    MappingMarketDataEgressPolicyProvider,
    MarketDataEgressPolicy,
)
from ai_platform.portal.execution.isolation import (
    CpuIsolationMode,
    LogIsolationBackend,
    NetworkIsolationBackend,
    RuntimeIsolationPlan,
    StorageIsolationBackend,
)


ALPINE_IMAGE = "alpine:3.20"


def _run(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _require_host() -> Path:
    if os.environ.get("PORTAL_LINUX_ISOLATION_E2E") != "true":
        pytest.skip("production Linux isolation backend E2E is dedicated-workflow only")
    if os.name != "posix" or not hasattr(os, "geteuid") or os.geteuid() != 0:
        if os.environ.get("CI") == "true":
            pytest.fail("Linux isolation backend E2E must run as root on its ephemeral CI host")
        pytest.skip("Linux isolation backend E2E requires root")
    for command in ("docker", "nft", "btrfs"):
        if shutil.which(command) is None:
            pytest.fail(f"{command} is required for Linux isolation backend E2E")
    mount = Path(os.environ.get("PORTAL_BTRFS_E2E_ROOT", "")).resolve()
    if not mount.is_dir():
        pytest.fail("PORTAL_BTRFS_E2E_ROOT must be an existing ephemeral Btrfs mount")
    filesystem = _run("btrfs", "filesystem", "show", str(mount))
    assert filesystem.returncode == 0, filesystem.stderr
    docker = _run("docker", "info", "--format", "{{.ServerVersion}}")
    assert docker.returncode == 0, docker.stderr
    return mount


def _policy() -> MarketDataEgressPolicy:
    return MarketDataEgressPolicy(
        policy_version="linux-e2e-v2",
        allowed_ipv4_cidrs=("1.1.1.1/32",),
        dns_resolver_ipv4_addresses=("1.1.1.1",),
        allowed_tcp_ports=(443,),
    )


def _plan(policy: MarketDataEgressPolicy) -> RuntimeIsolationPlan:
    return RuntimeIsolationPlan(
        plan_schema_version="runtime-isolation-plan/v1",
        resolver_version="linux-backend-e2e/v1",
        isolation_profile_version="linux-backend-e2e/v1",
        isolation_profile_digest="0" * 64,
        cpu_mode=CpuIsolationMode.CFS,
        cpu_millis=500,
        cpuset_cpus=(),
        memory_limit_bytes=64 * 1024 * 1024,
        memory_swap_limit_bytes=64 * 1024 * 1024,
        pids_limit=32,
        durable_state_max_bytes=8 * 1024 * 1024,
        storage_backend=StorageIsolationBackend.BOUNDED_VOLUME,
        tmpfs_max_bytes=8 * 1024 * 1024,
        run_tmpfs_max_bytes=2 * 1024 * 1024,
        log_max_bytes=1024 * 1024,
        log_rotation_count=2,
        log_backend=LogIsolationBackend.DOCKER_LOCAL,
        network_backend=NetworkIsolationBackend.NFTABLES,
        market_data_egress_policy_version=policy.policy_version,
        market_data_egress_policy_digest=policy.digest(),
        seccomp_profile_identity="docker-default",
        runtime_user="65532:65532",
        runtime_image_digest="1" * 64,
        gateway_artifact_digest="2" * 64,
        gateway_contract_version="linux-backend-e2e/v1",
        gateway_contract_digest="3" * 64,
    )


def test_real_linux_nftables_btrfs_backend_enforces_and_detects_tamper() -> None:
    mount = _require_host()
    runtime_id = f"portal-linux-e2e-{uuid4().hex[:10]}"
    network = f"portal-linux-net-{uuid4().hex[:10]}"
    container = f"{runtime_id}-probe"
    state_root = mount / "portal-state"
    state_root.mkdir(exist_ok=True)
    state_path = state_root / runtime_id
    state_path.mkdir()
    policy = _policy()
    plan = _plan(policy)
    backend = LinuxNftablesBtrfsIsolationAttestor(
        SubprocessCommandRunner(),
        policy_provider=MappingMarketDataEgressPolicyProvider({policy.digest(): policy}),
        state_root=state_root,
        btrfs_mount=mount,
    )

    try:
        capabilities = backend.capabilities()
        assert capabilities.storage_backend is StorageIsolationBackend.BOUNDED_VOLUME
        assert capabilities.network_backend is NetworkIsolationBackend.NFTABLES
        assert backend.dns_resolvers(plan) == ("1.1.1.1",)

        backend.prepare_storage(plan, state_path)
        backend.attest_storage(plan, state_path)
        backend.prepare_network(plan, network, runtime_id)

        pulled = _run("docker", "pull", "--quiet", ALPINE_IMAGE, timeout=180)
        assert pulled.returncode == 0, pulled.stderr
        started = _run(
            "docker",
            "run",
            "-d",
            "--name",
            container,
            "--label",
            f"ai.portal.runtime_id={runtime_id}",
            "--network",
            network,
            ALPINE_IMAGE,
            "sleep",
            "300",
        )
        assert started.returncode == 0, started.stderr
        backend.attest_network(plan, network, runtime_id)

        allowed = _run(
            "docker",
            "exec",
            container,
            "wget",
            "--no-check-certificate",
            "-q",
            "-T",
            "5",
            "-O",
            "/dev/null",
            "https://1.1.1.1",
            timeout=15,
        )
        assert allowed.returncode == 0, allowed.stderr

        dns = _run(
            "docker",
            "exec",
            container,
            "nslookup",
            "example.com",
            "1.1.1.1",
            timeout=15,
        )
        assert dns.returncode == 0, dns.stderr

        forbidden = _run(
            "docker",
            "exec",
            container,
            "wget",
            "-q",
            "-T",
            "2",
            "-O",
            "/dev/null",
            "http://8.8.8.8",
            timeout=10,
        )
        assert forbidden.returncode != 0

        table = backend._table_name(network)
        bridge_info = json_network = _run(
            "docker",
            "network",
            "inspect",
            "--format",
            "{{.Id}}",
            network,
        )
        assert json_network.returncode == 0, json_network.stderr
        bridge = f"br-{bridge_info.stdout.strip()[:12]}"
        tamper = _run(
            "nft",
            "add",
            "rule",
            "inet",
            table,
            "forward",
            "iifname",
            bridge,
            "counter",
            "accept",
        )
        assert tamper.returncode == 0, tamper.stderr
        with pytest.raises(RuntimeDriverError) as network_error:
            backend.attest_network(plan, network, runtime_id)
        assert network_error.value.reason_code == "ISOLATION_ATTESTATION_FAILED"

        changed_limit = _run(
            "btrfs",
            "qgroup",
            "limit",
            str(plan.durable_state_max_bytes * 2),
            str(state_path),
        )
        assert changed_limit.returncode == 0, changed_limit.stderr
        with pytest.raises(RuntimeDriverError) as storage_error:
            backend.attest_storage(plan, state_path)
        assert storage_error.value.reason_code == "ISOLATION_ATTESTATION_FAILED"
    finally:
        _run("docker", "rm", "-f", container)
        try:
            backend.cleanup_network(network, runtime_id)
        except RuntimeDriverError:
            pass
        if state_path.exists():
            deleted = _run("btrfs", "subvolume", "delete", str(state_path))
            assert deleted.returncode == 0, deleted.stderr
        if state_root.exists():
            state_root.rmdir()
