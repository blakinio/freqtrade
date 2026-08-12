from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from ai_platform.portal.execution.driver import SubprocessCommandRunner
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
RUNTIME_USER = "65532:65532"


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
        pytest.skip("state ownership E2E is dedicated-workflow only")
    if os.name != "posix" or not hasattr(os, "geteuid") or os.geteuid() != 0:
        if os.environ.get("CI") == "true":
            pytest.fail("state ownership E2E must run as root on its ephemeral CI host")
        pytest.skip("state ownership E2E requires root")
    for command in ("docker", "btrfs", "chown", "chmod", "stat"):
        if shutil.which(command) is None:
            pytest.fail(f"{command} is required for state ownership E2E")
    mount = Path(os.environ.get("PORTAL_BTRFS_E2E_ROOT", "")).resolve()
    if not mount.is_dir():
        pytest.fail("PORTAL_BTRFS_E2E_ROOT must be an existing ephemeral Btrfs mount")
    return mount


def _policy() -> MarketDataEgressPolicy:
    return MarketDataEgressPolicy(
        policy_version="state-owner-e2e-v2",
        allowed_ipv4_cidrs=("1.1.1.1/32",),
        dns_resolver_ipv4_addresses=("1.1.1.1",),
        allowed_tcp_ports=(443,),
    )


def _plan(policy: MarketDataEgressPolicy) -> RuntimeIsolationPlan:
    return RuntimeIsolationPlan(
        plan_schema_version="runtime-isolation-plan/v1",
        resolver_version="state-owner-e2e/v1",
        isolation_profile_version="state-owner-e2e/v1",
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
        runtime_user=RUNTIME_USER,
        runtime_image_digest="1" * 64,
        gateway_artifact_digest="2" * 64,
        gateway_contract_version="state-owner-e2e/v1",
        gateway_contract_digest="3" * 64,
    )


def test_bounded_state_is_owned_and_writable_by_exact_nonroot_runtime_user() -> None:
    mount = _require_host()
    runtime_id = f"portal-state-owner-e2e-{uuid4().hex[:10]}"
    state_root = mount / "portal-state-owner"
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
        pulled = _run("docker", "pull", "--quiet", ALPINE_IMAGE, timeout=180)
        assert pulled.returncode == 0, pulled.stderr

        backend.prepare_storage(plan, state_path)
        backend.attest_storage(plan, state_path)

        metadata = state_path.stat()
        assert metadata.st_uid == 65532
        assert metadata.st_gid == 65532
        assert stat.S_IMODE(metadata.st_mode) == 0o700

        writer = _run(
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--user",
            RUNTIME_USER,
            "--mount",
            f"type=bind,source={state_path},target=/runtime/state",
            ALPINE_IMAGE,
            "/bin/sh",
            "-ec",
            (
                'test "$(id -u)" = 65532; test "$(id -g)" = 65532; '
                'umask 077; printf "runtime-owned\\n" > /runtime/state/nonroot-write-probe'
            ),
        )
        assert writer.returncode == 0, writer.stderr
        assert (state_path / "nonroot-write-probe").read_text(encoding="utf-8") == (
            "runtime-owned\n"
        )
    finally:
        if state_path.exists():
            deleted = _run("btrfs", "subvolume", "delete", str(state_path))
            assert deleted.returncode == 0, deleted.stderr
        if state_root.exists():
            state_root.rmdir()
