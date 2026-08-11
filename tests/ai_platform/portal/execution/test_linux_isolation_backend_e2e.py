from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import pytest

from ai_platform.portal.execution.driver import (
    DockerCliRuntimeDriver,
    SubprocessCommandRunner,
)
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.host_isolation import (
    LinuxNftablesBtrfsIsolationAttestor,
    MappingMarketDataEgressPolicyProvider,
    MarketDataEgressPolicy,
)
from ai_platform.portal.execution.isolation import (
    CpuIsolationMode,
    LogIsolationBackend,
    MappingRuntimeIsolationPlanProvider,
    NetworkIsolationBackend,
    RuntimeIsolationPlan,
    RuntimeIsolationPlanBinding,
    StorageIsolationBackend,
)
from ai_platform.portal.execution.runtime import DriverRuntimeState, RuntimeContainerSpec


ALPINE_IMAGE = "alpine:3.20"
DNS_RESOLVER = "1.1.1.1"
MARKET_DATA_PROBE_HOSTS = ("api.kraken.com", "api.coinbase.com")
UNRELATED_PROBE_HOSTS = ("example.com", "www.cloudflare.com")


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


def _reachable_ipv4(hostnames: tuple[str, ...], *, exclude: frozenset[str] = frozenset()) -> str:
    failures: list[str] = []
    for hostname in hostnames:
        try:
            addresses = sorted(
                {
                    info[4][0]
                    for info in socket.getaddrinfo(
                        hostname,
                        443,
                        family=socket.AF_INET,
                        type=socket.SOCK_STREAM,
                    )
                    if info[4][0] not in exclude
                }
            )
        except socket.gaierror as exc:
            failures.append(f"{hostname}: DNS failed: {exc}")
            continue
        for address in addresses:
            try:
                with socket.create_connection((address, 443), timeout=5):
                    pass
            except OSError as exc:
                failures.append(f"{hostname}/{address}: TCP 443 failed: {exc}")
                continue
            return address
    pytest.fail("no reachable public IPv4 E2E probe target: " + "; ".join(failures))


def _policy(allowed_ipv4: str) -> MarketDataEgressPolicy:
    return MarketDataEgressPolicy(
        policy_version="linux-e2e-v3",
        allowed_ipv4_cidrs=(f"{allowed_ipv4}/32",),
        dns_resolver_ipv4_addresses=(DNS_RESOLVER,),
        allowed_tcp_ports=(443,),
    )


def _plan(
    policy: MarketDataEgressPolicy,
    *,
    runtime_image_digest: str = "1" * 64,
) -> RuntimeIsolationPlan:
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
        runtime_image_digest=runtime_image_digest,
        gateway_artifact_digest="2" * 64,
        gateway_contract_version="linux-backend-e2e/v1",
        gateway_contract_digest="3" * 64,
    )


def _tcp_probe(
    container: str,
    address: str,
    port: int = 443,
) -> subprocess.CompletedProcess[str]:
    return _run(
        "docker",
        "exec",
        container,
        "nc",
        "-z",
        "-w",
        "5",
        address,
        str(port),
        timeout=15,
    )


def _dns_probe(container: str) -> subprocess.CompletedProcess[str]:
    return _run(
        "docker",
        "exec",
        container,
        "nslookup",
        "example.com",
        timeout=15,
    )


def test_real_linux_nftables_btrfs_backend_enforces_and_detects_tamper() -> None:
    mount = _require_host()
    allowed_ipv4 = _reachable_ipv4(MARKET_DATA_PROBE_HOSTS)
    forbidden_ipv4 = _reachable_ipv4(
        UNRELATED_PROBE_HOSTS,
        exclude=frozenset({allowed_ipv4}),
    )
    runtime_id = f"portal-linux-e2e-{uuid4().hex[:10]}"
    network = f"portal-linux-net-{uuid4().hex[:10]}"
    container = runtime_id
    state_root = mount / "portal-state"
    state_root.mkdir(exist_ok=True)
    state_path = state_root / runtime_id
    state_path.mkdir()
    policy = _policy(allowed_ipv4)
    plan = _plan(policy)
    backend = LinuxNftablesBtrfsIsolationAttestor(
        SubprocessCommandRunner(),
        policy_provider=MappingMarketDataEgressPolicyProvider({policy.digest(): policy}),
        state_root=state_root,
        btrfs_mount=mount,
    )
    table = backend._table_name(network)

    try:
        capabilities = backend.capabilities()
        assert capabilities.storage_backend is StorageIsolationBackend.BOUNDED_VOLUME
        assert capabilities.network_backend is NetworkIsolationBackend.NFTABLES
        assert backend.dns_resolvers(plan) == (DNS_RESOLVER,)

        backend.prepare_storage(plan, state_path)
        backend.attest_storage(plan, state_path)

        quota_overrun = _run(
            "dd",
            "if=/dev/zero",
            f"of={state_path / 'quota-overrun-probe'}",
            "bs=1M",
            "count=12",
            "conv=fsync",
        )
        assert quota_overrun.returncode != 0
        quota_error = quota_overrun.stderr.lower()
        assert "disk quota exceeded" in quota_error or "no space left on device" in quota_error

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
            "--label",
            f"ai.portal.isolation_plan_digest={plan.digest()}",
            "--dns",
            DNS_RESOLVER,
            "--network",
            network,
            ALPINE_IMAGE,
            "sleep",
            "300",
        )
        assert started.returncode == 0, started.stderr
        backend.attest_network(plan, network, runtime_id)

        resolv_conf = _run("docker", "exec", container, "cat", "/etc/resolv.conf")
        assert resolv_conf.returncode == 0, resolv_conf.stderr
        assert "nameserver 127.0.0.11" in resolv_conf.stdout

        # Staged final policy is present but unreachable while normal Docker DNS and
        # public market-data egress remain denied during quarantine.
        assert _tcp_probe(container, allowed_ipv4).returncode != 0
        assert _dns_probe(container).returncode != 0

        backend.activate_network(plan, network, runtime_id)

        allowed = _tcp_probe(container, allowed_ipv4)
        assert allowed.returncode == 0, allowed.stderr
        dns = _dns_probe(container)
        assert dns.returncode == 0, dns.stderr

        forbidden = _tcp_probe(container, forbidden_ipv4)
        assert forbidden.returncode != 0

        bridge_info = _run(
            "docker",
            "network",
            "inspect",
            "--format",
            "{{.Id}}",
            network,
        )
        assert bridge_info.returncode == 0, bridge_info.stderr
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
        live = _run("nft", "-j", "list", "table", "inet", table)
        assert live.returncode == 0, live.stderr
        with pytest.raises(RuntimeDriverError) as network_error:
            backend._attest_canonical_nftables(
                json.loads(live.stdout),
                table,
                bridge,
                policy,
                active=True,
            )
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
        backend.cleanup_network(network, runtime_id)
        table_absent = _run("nft", "list", "table", "inet", table)
        assert table_absent.returncode != 0, table_absent.stdout
        if state_path.exists():
            deleted = _run("btrfs", "subvolume", "delete", str(state_path))
            assert deleted.returncode == 0, deleted.stderr
        if state_root.exists():
            state_root.rmdir()


def test_driver_release_runs_through_concrete_linux_isolation_backend() -> None:
    mount = _require_host()
    exact_image = os.environ.get("PORTAL_RUNTIME_IMAGE", "").strip()
    if "@sha256:" not in exact_image:
        pytest.fail("PORTAL_RUNTIME_IMAGE must be an exact hardened runtime image digest")
    image_digest = exact_image.rsplit("@sha256:", 1)[1]
    assert len(image_digest) == 64

    runtime_id = f"portal-isolation-e2e-linux-{uuid4().hex[:10]}"
    network = DockerCliRuntimeDriver._network_name(runtime_id)
    state_root = mount / "portal-driver-state"
    state_root.mkdir(exist_ok=True)
    state_path = state_root / runtime_id
    state_path.mkdir()
    inputs = Path.cwd() / f".{runtime_id}-inputs"
    inputs.mkdir(mode=0o755)
    config_path = inputs / "config.json"
    config_path.write_text("{}\n", encoding="utf-8")
    config_path.chmod(0o644)

    allowed_ipv4 = _reachable_ipv4(MARKET_DATA_PROBE_HOSTS)
    policy = _policy(allowed_ipv4)
    plan = _plan(policy, runtime_image_digest=image_digest)
    backend = LinuxNftablesBtrfsIsolationAttestor(
        SubprocessCommandRunner(),
        policy_provider=MappingMarketDataEgressPolicyProvider({policy.digest(): policy}),
        state_root=state_root,
        btrfs_mount=mount,
    )
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
        external_attestor=backend,
    )
    table = backend._table_name(network)

    try:
        assert driver.provision(spec) is DriverRuntimeState.CREATED
        assert driver.inspect(runtime_id) is DriverRuntimeState.CREATED

        assert driver.start(runtime_id) is DriverRuntimeState.RUNNING

        network_info = backend._network_info(network)
        live = _run("nft", "-j", "list", "table", "inet", table)
        assert live.returncode == 0, live.stderr
        backend._attest_canonical_nftables(
            json.loads(live.stdout),
            table,
            backend._bridge_name(network_info),
            policy,
            active=True,
        )

        logs = ""
        for _ in range(100):
            observed = _run("docker", "logs", runtime_id)
            assert observed.returncode == 0, observed.stderr
            logs = observed.stdout + observed.stderr
            if "freqtrade" in logs.lower():
                break
            time.sleep(0.1)
        assert "freqtrade" in logs.lower(), logs[-4000:]
    finally:
        _run("docker", "rm", "-f", runtime_id)
        backend.cleanup_network(network, runtime_id)
        table_absent = _run("nft", "list", "table", "inet", table)
        assert table_absent.returncode != 0, table_absent.stdout
        if state_path.exists():
            deleted = _run("btrfs", "subvolume", "delete", str(state_path))
            assert deleted.returncode == 0, deleted.stderr
        if state_root.exists():
            state_root.rmdir()
        shutil.rmtree(inputs, ignore_errors=True)
