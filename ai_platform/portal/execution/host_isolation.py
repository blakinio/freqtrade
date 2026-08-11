from __future__ import annotations

import hashlib
import ipaddress
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ai_platform.portal.execution.driver import (
    CommandResult,
    CommandRunner,
    ExternalIsolationCapabilities,
)
from ai_platform.portal.execution.errors import RuntimeDriverError
from ai_platform.portal.execution.isolation import (
    NetworkIsolationBackend,
    RuntimeIsolationPlan,
    StorageIsolationBackend,
)


_NON_PUBLIC_IPV4_NETWORKS = tuple(
    ipaddress.ip_network(cidr)
    for cidr in (
        "0.0.0.0/8",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.0.0.0/24",
        "192.0.2.0/24",
        "192.88.99.0/24",
        "192.168.0.0/16",
        "198.18.0.0/15",
        "198.51.100.0/24",
        "203.0.113.0/24",
        "224.0.0.0/4",
        "240.0.0.0/4",
    )
)


def _policy_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class MarketDataEgressPolicy:
    policy_version: str
    allowed_ipv4_cidrs: tuple[str, ...]
    allowed_tcp_ports: tuple[int, ...] = (443,)

    def __post_init__(self) -> None:
        if not self.policy_version.strip():
            raise ValueError("policy_version must not be empty")
        if not self.allowed_ipv4_cidrs:
            raise ValueError("at least one public market-data CIDR is required")
        for cidr in self.allowed_ipv4_cidrs:
            network = ipaddress.ip_network(cidr, strict=True)
            if (
                network.version != 4
                or not network.is_global
                or any(network.overlaps(blocked) for blocked in _NON_PUBLIC_IPV4_NETWORKS)
            ):
                raise ValueError(
                    "market-data CIDRs must be exclusively public globally routable IPv4 networks"
                )
        if not self.allowed_tcp_ports:
            raise ValueError("at least one market-data TCP port is required")
        if any(port <= 0 or port > 65535 for port in self.allowed_tcp_ports):
            raise ValueError("market-data TCP ports must be in the range 1..65535")

    def digest(self) -> str:
        return _policy_digest({"schema": "market-data-egress-policy/v1", **asdict(self)})


class MarketDataEgressPolicyProvider:
    def resolve(self, policy_digest: str) -> MarketDataEgressPolicy:
        raise NotImplementedError


class MappingMarketDataEgressPolicyProvider(MarketDataEgressPolicyProvider):
    def __init__(self, policies: dict[str, MarketDataEgressPolicy]) -> None:
        self._policies = dict(policies)

    def resolve(self, policy_digest: str) -> MarketDataEgressPolicy:
        try:
            policy = self._policies[policy_digest]
        except KeyError as exc:
            raise RuntimeDriverError(
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
                "trusted market-data egress policy is unavailable",
            ) from exc
        if policy.digest() != policy_digest:
            raise RuntimeDriverError(
                "ISOLATION_PLAN_MISMATCH",
                "market-data egress policy digest does not match trusted policy",
            )
        return policy


class LinuxNftablesBtrfsIsolationAttestor:
    """Concrete compatible-host backend for #1354.

    Instantiating this class is safe. Calling prepare methods mutates an authorized Linux
    host's Docker network, nftables rules and Btrfs qgroup state, so protected deployment
    authorization remains mandatory outside repository validation.
    """

    def __init__(
        self,
        runner: CommandRunner,
        *,
        policy_provider: MarketDataEgressPolicyProvider,
        state_root: Path,
        btrfs_mount: Path,
    ) -> None:
        self._runner = runner
        self._policies = policy_provider
        self._state_root = state_root.resolve()
        self._btrfs_mount = btrfs_mount.resolve()

    def capabilities(self) -> ExternalIsolationCapabilities:
        storage = self._storage_capability()
        network = NetworkIsolationBackend.NFTABLES if self._command_available("nft") else None
        return ExternalIsolationCapabilities(
            storage_backend=storage,
            network_backend=network,
        )

    def prepare_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None:
        self._require_storage_backend(plan)
        state = self._approved_state_path(state_path)
        show = self._runner.run(("btrfs", "subvolume", "show", str(state)))
        if show.returncode != 0:
            if not state.exists() or not state.is_dir() or any(state.iterdir()):
                raise RuntimeDriverError(
                    "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                    "runtime state is not an empty directory or Btrfs subvolume",
                )
            state.rmdir()
            self._require_success(
                ("btrfs", "subvolume", "create", str(state)),
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
            )
        self._require_success(
            ("btrfs", "quota", "enable", str(self._btrfs_mount)),
            "HOST_STORAGE_ISOLATION_UNSUPPORTED",
            allow_already_enabled=True,
        )
        self._require_success(
            (
                "btrfs",
                "qgroup",
                "limit",
                str(plan.durable_state_max_bytes),
                str(state),
            ),
            "HOST_STORAGE_ISOLATION_UNSUPPORTED",
        )
        self.attest_storage(plan, state)

    def prepare_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        self._require_network_backend(plan)
        policy = self._policy_for(plan)
        self._require_success(
            (
                "docker",
                "network",
                "create",
                "--driver",
                "bridge",
                "--ipv6=false",
                "--label",
                f"ai.portal.runtime_id={runtime_id}",
                network_name,
            ),
            "HOST_NETWORK_ISOLATION_UNSUPPORTED",
        )
        try:
            network = self._network_info(network_name)
            bridge = self._bridge_name(network)
            table = self._table_name(network_name)
            self._delete_table_if_present(table)
            self._nft("add", "table", "inet", table)
            self._nft(
                "add",
                "chain",
                "inet",
                table,
                "input",
                "{",
                "type",
                "filter",
                "hook",
                "input",
                "priority",
                "-40;",
                "policy",
                "accept;",
                "}",
            )
            self._nft(
                "add",
                "chain",
                "inet",
                table,
                "forward",
                "{",
                "type",
                "filter",
                "hook",
                "forward",
                "priority",
                "-40;",
                "policy",
                "accept;",
                "}",
            )
            self._nft(
                "add",
                "rule",
                "inet",
                table,
                "input",
                "iifname",
                bridge,
                "counter",
                "drop",
            )
            self._nft(
                "add",
                "rule",
                "inet",
                table,
                "forward",
                "iifname",
                bridge,
                "oifname",
                bridge,
                "counter",
                "accept",
            )
            for cidr in policy.allowed_ipv4_cidrs:
                for port in policy.allowed_tcp_ports:
                    self._nft(
                        "add",
                        "rule",
                        "inet",
                        table,
                        "forward",
                        "iifname",
                        bridge,
                        "ip",
                        "daddr",
                        cidr,
                        "tcp",
                        "dport",
                        str(port),
                        "ct",
                        "state",
                        "new,established",
                        "counter",
                        "accept",
                    )
            self._nft(
                "add",
                "rule",
                "inet",
                table,
                "forward",
                "iifname",
                bridge,
                "counter",
                "drop",
            )
            self.attest_network(plan, network_name, runtime_id)
        except Exception as primary:
            try:
                self.cleanup_network(network_name, runtime_id)
            except Exception as cleanup_error:
                raise RuntimeDriverError(
                    "HOST_NETWORK_CLEANUP_FAILED",
                    "network isolation preparation failed and cleanup was incomplete: "
                    f"primary={primary}; cleanup={cleanup_error}",
                ) from cleanup_error
            raise

    def attest_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None:
        state = self._approved_state_path(state_path)
        quota_status = self._runner.run(("btrfs", "quota", "status", str(self._btrfs_mount)))
        if quota_status.returncode != 0:
            self._raise_command(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                quota_status,
                "Btrfs quota status is unavailable",
            )
        status = quota_status.stdout.lower()
        if (
            "enabled:" not in status
            or "enabled:                 yes" not in status
            or "inconsistent:            no" not in status
            or "override limits:         no" not in status
        ):
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "Btrfs qgroup accounting is not consistently enforcing limits",
            )

        subvolume_id = self._subvolume_id(state)
        result = self._runner.run(
            ("btrfs", "qgroup", "show", "--raw", "-r", "-F", str(self._btrfs_mount))
        )
        if result.returncode != 0:
            self._raise_command(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                result,
                "Btrfs qgroup evidence is unavailable",
            )
        maximum = self._qgroup_max_rfer(result.stdout, f"0/{subvolume_id}")
        if maximum != plan.durable_state_max_bytes:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "effective Btrfs durable-state bound does not match isolation plan",
            )

    def attest_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        policy = self._policy_for(plan)
        network = self._network_info(network_name)
        if bool(network.get("EnableIPv6", False)):
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "generation network unexpectedly enables IPv6",
            )
        labels = network.get("Labels") or {}
        if not isinstance(labels, dict) or labels.get("ai.portal.runtime_id") != runtime_id:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "generation network identity label does not match runtime",
            )
        self._attest_network_members(network, runtime_id)
        bridge = self._bridge_name(network)
        table = self._table_name(network_name)
        result = self._runner.run(("nft", "list", "table", "inet", table))
        if result.returncode != 0:
            self._raise_command(
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
                result,
                "nftables generation policy is unavailable",
            )
        evidence = result.stdout
        required = [bridge, "hook input", "hook forward", "drop"]
        required.extend(policy.allowed_ipv4_cidrs)
        required.extend(str(port) for port in policy.allowed_tcp_ports)
        if any(marker not in evidence for marker in required):
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "effective nftables generation policy is incomplete",
            )

    def cleanup_network(self, network_name: str, runtime_id: str) -> None:
        del runtime_id
        table = self._table_name(network_name)
        errors: list[str] = []
        nft_result = self._runner.run(("nft", "delete", "table", "inet", table))
        if nft_result.returncode != 0 and not self._cleanup_target_absent(nft_result):
            errors.append(nft_result.stderr.strip() or "nftables table cleanup failed")
        network_result = self._runner.run(("docker", "network", "rm", network_name))
        if network_result.returncode != 0 and not self._cleanup_target_absent(network_result):
            errors.append(network_result.stderr.strip() or "Docker network cleanup failed")
        if errors:
            raise RuntimeDriverError(
                "HOST_NETWORK_CLEANUP_FAILED",
                "generation network cleanup was incomplete: " + "; ".join(errors),
            )

    def _storage_capability(self) -> StorageIsolationBackend | None:
        if not self._command_available("btrfs"):
            return None
        result = self._runner.run(("btrfs", "filesystem", "show", str(self._btrfs_mount)))
        if result.returncode != 0:
            return None
        return StorageIsolationBackend.BOUNDED_VOLUME

    def _command_available(self, command: str) -> bool:
        return self._runner.run((command, "--version")).returncode == 0

    @staticmethod
    def _require_storage_backend(plan: RuntimeIsolationPlan) -> None:
        if plan.storage_backend is not StorageIsolationBackend.BOUNDED_VOLUME:
            raise RuntimeDriverError(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                "Linux backend requires Btrfs bounded-volume storage",
            )

    @staticmethod
    def _require_network_backend(plan: RuntimeIsolationPlan) -> None:
        if plan.network_backend is not NetworkIsolationBackend.NFTABLES:
            raise RuntimeDriverError(
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
                "Linux backend requires nftables network isolation",
            )

    def _policy_for(self, plan: RuntimeIsolationPlan) -> MarketDataEgressPolicy:
        policy = self._policies.resolve(plan.market_data_egress_policy_digest)
        if policy.policy_version != plan.market_data_egress_policy_version:
            raise RuntimeDriverError(
                "ISOLATION_PLAN_MISMATCH",
                "market-data egress policy version does not match isolation plan",
            )
        return policy

    def _approved_state_path(self, state_path: Path) -> Path:
        state = state_path.resolve()
        if state == self._state_root:
            raise RuntimeDriverError(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                "runtime state path must be a child of the approved state root",
            )
        try:
            state.relative_to(self._state_root)
        except ValueError as exc:
            raise RuntimeDriverError(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                "runtime state path escapes the approved state root",
            ) from exc
        return state

    def _network_info(self, network_name: str) -> dict[str, Any]:
        result = self._runner.run(
            ("docker", "network", "inspect", "--format", "{{json .}}", network_name)
        )
        if result.returncode != 0:
            self._raise_command(
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
                result,
                "generation network inspection failed",
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "generation network evidence is invalid JSON",
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "generation network evidence has an unexpected shape",
            )
        return payload

    def _attest_network_members(self, network: dict[str, Any], runtime_id: str) -> None:
        containers = network.get("Containers") or {}
        if not isinstance(containers, dict) or len(containers) > 2:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "generation network has an unexpected container membership",
            )
        for container_id in containers:
            result = self._runner.run(
                (
                    "docker",
                    "inspect",
                    "--format",
                    "{{json .Config.Labels}}",
                    str(container_id),
                )
            )
            if result.returncode != 0:
                self._raise_command(
                    "ISOLATION_ATTESTATION_FAILED",
                    result,
                    "generation network member identity is unavailable",
                )
            try:
                member_labels = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    "generation network member labels are invalid JSON",
                ) from exc
            if (
                not isinstance(member_labels, dict)
                or member_labels.get("ai.portal.runtime_id") != runtime_id
            ):
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    "unrelated container is attached to the generation network",
                )

    @staticmethod
    def _bridge_name(network: dict[str, Any]) -> str:
        network_id = str(network.get("Id", ""))
        if len(network_id) < 12 or any(
            character not in "0123456789abcdef" for character in network_id
        ):
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "Docker generation network ID is invalid",
            )
        return f"br-{network_id[:12]}"

    @staticmethod
    def _table_name(network_name: str) -> str:
        digest = hashlib.sha256(network_name.encode()).hexdigest()[:20]
        return f"portal_{digest}"

    @staticmethod
    def _cleanup_target_absent(result: CommandResult) -> bool:
        evidence = f"{result.stdout}\n{result.stderr}".lower()
        return any(
            marker in evidence
            for marker in (
                "no such file or directory",
                "no such network",
                "network not found",
                "not found",
            )
        )

    def _delete_table_if_present(self, table: str) -> None:
        present = self._runner.run(("nft", "list", "table", "inet", table))
        if present.returncode == 0:
            self._require_success(
                ("nft", "delete", "table", "inet", table),
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
            )

    def _nft(self, *args: str) -> None:
        self._require_success(("nft", *args), "HOST_NETWORK_ISOLATION_UNSUPPORTED")

    def _subvolume_id(self, state: Path) -> int:
        result = self._runner.run(("btrfs", "subvolume", "show", str(state)))
        if result.returncode != 0:
            self._raise_command(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                result,
                "runtime state is not a Btrfs subvolume",
            )
        for line in result.stdout.splitlines():
            if line.strip().startswith("Subvolume ID:"):
                try:
                    return int(line.split(":", 1)[1].strip())
                except ValueError as exc:
                    raise RuntimeDriverError(
                        "ISOLATION_ATTESTATION_FAILED",
                        "Btrfs subvolume ID is invalid",
                    ) from exc
        raise RuntimeDriverError(
            "ISOLATION_ATTESTATION_FAILED",
            "Btrfs subvolume ID is missing",
        )

    @staticmethod
    def _qgroup_max_rfer(output: str, qgroup: str) -> int | None:
        header: list[str] | None = None
        max_rfer_index: int | None = None
        for line in output.splitlines():
            fields = line.split()
            if not fields:
                continue
            if fields[0] == "qgroupid":
                header = fields
                try:
                    max_rfer_index = header.index("max_rfer")
                except ValueError:
                    return None
                continue
            if fields[0] != qgroup or max_rfer_index is None:
                continue
            if len(fields) <= max_rfer_index:
                return None
            raw_value = fields[max_rfer_index]
            if raw_value.lower() == "none":
                return None
            try:
                return int(raw_value)
            except ValueError:
                return None
        return None

    def _require_success(
        self,
        args: tuple[str, ...],
        reason_code: str,
        *,
        allow_already_enabled: bool = False,
    ) -> None:
        result = self._runner.run(args)
        if result.returncode == 0:
            return
        if allow_already_enabled and "already enabled" in result.stderr.lower():
            return
        self._raise_command(reason_code, result, f"command failed: {args[0]}")

    @staticmethod
    def _raise_command(
        reason_code: str,
        result: CommandResult,
        fallback: str,
    ) -> None:
        raise RuntimeDriverError(reason_code, result.stderr.strip() or fallback)
