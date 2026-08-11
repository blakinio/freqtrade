from __future__ import annotations

import hashlib
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
    FilesystemGatewayArtifactAttestor,
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
PAPER_E2E_EXCHANGE = "kraken"
PAPER_E2E_MARKET_DATA_HOST = "api.kraken.com"
PAPER_E2E_PAIR = "BTC/USD"


def _persist_task_table(table: str) -> None:
    inventory = os.environ.get("PORTAL_NFTABLES_TABLE_INVENTORY", "").strip()
    if inventory:
        with Path(inventory).open("a", encoding="utf-8") as handle:
            handle.write(f"{table}\n")


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


def _resolved_ipv4(hostname: str) -> tuple[str, ...]:
    try:
        return tuple(
            sorted(
                {
                    str(info[4][0])
                    for info in socket.getaddrinfo(
                        hostname,
                        443,
                        family=socket.AF_INET,
                        type=socket.SOCK_STREAM,
                    )
                }
            )
        )
    except socket.gaierror as exc:
        pytest.fail(f"{hostname}: DNS failed: {exc}")
        raise AssertionError("unreachable") from exc


def _reachable_ipv4(hostnames: tuple[str, ...], *, exclude: frozenset[str] = frozenset()) -> str:
    failures: list[str] = []
    for hostname in hostnames:
        addresses = [address for address in _resolved_ipv4(hostname) if address not in exclude]
        for address in addresses:
            try:
                with socket.create_connection((address, 443), timeout=5):
                    pass
            except OSError as exc:
                failures.append(f"{hostname}/{address}: TCP 443 failed: {exc}")
                continue
            return address
    pytest.fail("no reachable public IPv4 E2E probe target: " + "; ".join(failures))
    raise AssertionError("unreachable")


def _reachable_market_data_ipv4(hostname: str) -> tuple[str, ...]:
    addresses = _resolved_ipv4(hostname)
    failures: list[str] = []
    for address in addresses:
        try:
            with socket.create_connection((address, 443), timeout=5):
                return addresses
        except OSError as exc:
            failures.append(f"{hostname}/{address}: TCP 443 failed: {exc}")
    pytest.fail("market-data endpoint has no reachable IPv4: " + "; ".join(failures))
    raise AssertionError("unreachable")


def _policy(*allowed_ipv4: str) -> MarketDataEgressPolicy:
    return MarketDataEgressPolicy(
        policy_version="linux-e2e-v3",
        allowed_ipv4_cidrs=tuple(f"{address}/32" for address in allowed_ipv4),
        dns_resolver_ipv4_addresses=(DNS_RESOLVER,),
        allowed_tcp_ports=(443,),
    )


def _plan(
    policy: MarketDataEgressPolicy,
    *,
    runtime_image_digest: str = "1" * 64,
    gateway_artifact_digest: str = "2" * 64,
    gateway_contract_digest: str = "3" * 64,
) -> RuntimeIsolationPlan:
    return RuntimeIsolationPlan(
        plan_schema_version="runtime-isolation-plan/v1",
        resolver_version="linux-backend-e2e/v1",
        isolation_profile_version="linux-backend-e2e/v1",
        isolation_profile_digest="0" * 64,
        cpu_mode=CpuIsolationMode.CFS,
        cpu_millis=500,
        cpuset_cpus=(),
        memory_limit_bytes=512 * 1024 * 1024,
        memory_swap_limit_bytes=512 * 1024 * 1024,
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
        runtime_user="1000:1000",
        runtime_image_digest=runtime_image_digest,
        gateway_artifact_digest=gateway_artifact_digest,
        gateway_contract_version="linux-backend-e2e/v1",
        gateway_contract_digest=gateway_contract_digest,
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


def _write_paper_runtime_inputs(inputs: Path, state_path: Path) -> Path:
    strategy = inputs / "PortalE2EStrategy.py"
    strategy.write_text(
        "from pandas import DataFrame\n"
        "from freqtrade.strategy import IStrategy\n\n"
        "class PortalE2EStrategy(IStrategy):\n"
        "    INTERFACE_VERSION = 3\n"
        "    timeframe = '5m'\n"
        "    minimal_roi = {'0': 100.0}\n"
        "    stoploss = -0.99\n\n"
        "    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:\n"
        "        return dataframe\n\n"
        "    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:\n"
        "        dataframe['enter_long'] = 0\n"
        "        return dataframe\n\n"
        "    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:\n"
        "        dataframe['exit_long'] = 0\n"
        "        return dataframe\n",
        encoding="utf-8",
    )
    strategy.chmod(0o644)

    config_path = inputs / "config.json"
    config = {
        "max_open_trades": 1,
        "stake_currency": "USD",
        "stake_amount": 100,
        "tradable_balance_ratio": 0.99,
        "fiat_display_currency": "USD",
        "dry_run": True,
        "dry_run_wallet": 1000,
        "cancel_open_orders_on_exit": False,
        "timeframe": "5m",
        "trading_mode": "spot",
        "margin_mode": "",
        "entry_pricing": {
            "price_side": "same",
            "use_order_book": True,
            "order_book_top": 1,
        },
        "exit_pricing": {
            "price_side": "same",
            "use_order_book": True,
            "order_book_top": 1,
        },
        "exchange": {
            "name": PAPER_E2E_EXCHANGE,
            "key": "",
            "secret": "",
            "ccxt_config": {"enableRateLimit": True},
            "ccxt_async_config": {"enableRateLimit": True},
            "pair_whitelist": [PAPER_E2E_PAIR],
            "pair_blacklist": [],
        },
        "pairlists": [{"method": "StaticPairList"}],
        "strategy": "PortalE2EStrategy",
        "strategy_path": "/runtime/config",
        "user_data_dir": "/runtime/state",
        "db_url": "sqlite:////runtime/state/tradesv3.sqlite",
    }
    config_path.write_text(json.dumps(config, sort_keys=True) + "\n", encoding="utf-8")
    config_path.chmod(0o644)
    assert state_path.is_dir()
    return config_path


def _positive_market_data_tcp_counter(  # noqa: C901
    payload: dict[str, object],
) -> bool:
    raw_nftables = payload.get("nftables")
    if not isinstance(raw_nftables, list):
        return False
    for item in raw_nftables:
        if not isinstance(item, dict):
            continue
        rule = item.get("rule")
        if not isinstance(rule, dict) or rule.get("chain") != "egress":
            continue
        tcp_443 = False
        packets = 0
        expressions = rule.get("expr")
        if not isinstance(expressions, list):
            continue
        for expression in expressions:
            if not isinstance(expression, dict):
                continue
            match = expression.get("match")
            if isinstance(match, dict):
                left = match.get("left")
                if (
                    isinstance(left, dict)
                    and left.get("payload") == {"protocol": "tcp", "field": "dport"}
                    and match.get("right") == 443
                ):
                    tcp_443 = True
            counter = expression.get("counter")
            if isinstance(counter, dict):
                observed = counter.get("packets")
                if isinstance(observed, int):
                    packets = observed
        if tcp_443 and packets > 0:
            return True
    return False


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
    _persist_task_table(table)

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
            "ai.portal.test=runtime-isolation-e2e",
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
    config_path = _write_paper_runtime_inputs(inputs, state_path)
    gateway_artifact = inputs / "gateway-artifact.json"
    gateway_contract = inputs / "gateway-contract.json"
    gateway_artifact.write_text('{"kind":"paper-market-data-gateway"}\n', encoding="utf-8")
    gateway_contract.write_text('{"version":"linux-backend-e2e/v1"}\n', encoding="utf-8")
    gateway_artifact.chmod(0o444)
    gateway_contract.chmod(0o444)

    market_data_ipv4 = _reachable_market_data_ipv4(PAPER_E2E_MARKET_DATA_HOST)
    policy = _policy(*market_data_ipv4)
    plan = _plan(
        policy,
        runtime_image_digest=image_digest,
        gateway_artifact_digest=hashlib.sha256(gateway_artifact.read_bytes()).hexdigest(),
        gateway_contract_digest=hashlib.sha256(gateway_contract.read_bytes()).hexdigest(),
    )
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
        gateway_attestor=FilesystemGatewayArtifactAttestor(gateway_artifact, gateway_contract),
    )
    table = backend._table_name(network)
    _persist_task_table(table)

    try:
        assert driver.provision(spec) is DriverRuntimeState.CREATED
        assert driver.inspect(runtime_id) is DriverRuntimeState.CREATED

        assert driver.start(runtime_id) is DriverRuntimeState.STARTING

        public_data = _run(
            "docker",
            "exec",
            runtime_id,
            "freqtrade",
            "list-pairs",
            "--config",
            "/runtime/config/config.json",
            "--exchange",
            PAPER_E2E_EXCHANGE,
            "--quote",
            "USD",
            "--print-json",
            timeout=120,
        )
        assert public_data.returncode == 0, public_data.stdout + public_data.stderr
        assert PAPER_E2E_PAIR in public_data.stdout

        for _ in range(40):
            state = driver.inspect(runtime_id)
            if state is DriverRuntimeState.RUNNING:
                break
            assert state is DriverRuntimeState.STARTING
            time.sleep(0.25)
        else:
            pytest.fail("released PAPER runtime did not reach application readiness")
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
        market_data_observed = False
        for _ in range(120):
            state = _run(
                "docker",
                "inspect",
                "--format",
                "{{.State.Running}} {{.State.ExitCode}}",
                runtime_id,
            )
            assert state.returncode == 0, state.stderr
            if not state.stdout.strip().startswith("true "):
                observed = _run("docker", "logs", runtime_id)
                pytest.fail(
                    "released PAPER runtime exited during boot: "
                    f"state={state.stdout.strip()} "
                    f"logs={(observed.stdout + observed.stderr)[-4000:]}"
                )

            observed = _run("docker", "logs", runtime_id)
            assert observed.returncode == 0, observed.stderr
            logs = observed.stdout + observed.stderr
            counters = _run("nft", "-j", "list", "table", "inet", table)
            assert counters.returncode == 0, counters.stderr
            market_data_observed = _positive_market_data_tcp_counter(json.loads(counters.stdout))
            if market_data_observed:
                break
            time.sleep(0.5)

        assert market_data_observed, "no approved TCP/443 market-data egress was observed"
        sustained_until = time.monotonic() + 10
        while time.monotonic() < sustained_until:
            assert driver.inspect(runtime_id) is DriverRuntimeState.RUNNING, logs[-4000:]
            time.sleep(0.5)
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
