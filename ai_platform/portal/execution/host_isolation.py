from __future__ import annotations

import hashlib
import ipaddress
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, NoReturn
from uuid import UUID

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


def _is_exclusively_public_ipv4_network(
    network: ipaddress.IPv4Network | ipaddress.IPv6Network,
) -> bool:
    return (
        network.version == 4
        and network.is_global
        and not any(network.overlaps(blocked) for blocked in _NON_PUBLIC_IPV4_NETWORKS)
    )


@dataclass(frozen=True)
class MarketDataEgressPolicy:
    policy_version: str
    allowed_ipv4_cidrs: tuple[str, ...]
    dns_resolver_ipv4_addresses: tuple[str, ...]
    allowed_tcp_ports: tuple[int, ...] = (443,)

    def __post_init__(self) -> None:  # noqa: C901 - immutable policy validation boundary.
        if not self.policy_version.strip():
            raise ValueError("policy_version must not be empty")
        if not self.allowed_ipv4_cidrs:
            raise ValueError("at least one public market-data CIDR is required")
        for cidr in self.allowed_ipv4_cidrs:
            network = ipaddress.ip_network(cidr, strict=True)
            if not _is_exclusively_public_ipv4_network(network):
                raise ValueError(
                    "market-data CIDRs must be exclusively public globally routable IPv4 networks"
                )
        if not self.dns_resolver_ipv4_addresses:
            raise ValueError("at least one approved public DNS resolver is required")
        if len(set(self.dns_resolver_ipv4_addresses)) != len(self.dns_resolver_ipv4_addresses):
            raise ValueError("approved DNS resolvers must be unique")
        for address in self.dns_resolver_ipv4_addresses:
            try:
                resolver = ipaddress.ip_address(address)
            except ValueError as exc:
                raise ValueError("approved DNS resolvers must be IPv4 addresses") from exc
            if not isinstance(resolver, ipaddress.IPv4Address):
                raise ValueError("approved DNS resolvers must be IPv4 addresses")
            resolver_network = ipaddress.ip_network(f"{resolver}/32", strict=True)
            if not _is_exclusively_public_ipv4_network(resolver_network):
                raise ValueError(
                    "approved DNS resolvers must be public globally routable IPv4 addresses"
                )
        if not self.allowed_tcp_ports:
            raise ValueError("at least one market-data TCP port is required")
        if any(port <= 0 or port > 65535 for port in self.allowed_tcp_ports):
            raise ValueError("market-data TCP ports must be in the range 1..65535")

    def digest(self) -> str:
        return _policy_digest({"schema": "market-data-egress-policy/v2", **asdict(self)})


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
    """Concrete compatible-host backend for the #1354 hard isolation envelope."""

    def __init__(
        self,
        runner: CommandRunner,
        *,
        policy_provider: MarketDataEgressPolicyProvider,
        state_root: Path,
        btrfs_mount: Path,
        btrfs_sysfs_root: Path = Path("/sys/fs/btrfs"),
    ) -> None:
        self._runner = runner
        self._policies = policy_provider
        self._state_root = state_root.resolve()
        self._btrfs_mount = btrfs_mount.resolve()
        self._btrfs_sysfs_root = btrfs_sysfs_root.resolve()
        self._network_ids: dict[str, str] = {}

    def capabilities(self) -> ExternalIsolationCapabilities:
        storage = self._storage_capability()
        network = NetworkIsolationBackend.NFTABLES if self._command_available("nft") else None
        return ExternalIsolationCapabilities(
            storage_backend=storage,
            network_backend=network,
        )

    def dns_resolvers(self, plan: RuntimeIsolationPlan) -> tuple[str, ...]:
        self._require_network_backend(plan)
        return self._policy_for(plan).dns_resolver_ipv4_addresses

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
        runtime_uid, runtime_gid = self._runtime_identity(plan)
        self._require_success(
            ("chown", f"{runtime_uid}:{runtime_gid}", str(state)),
            "HOST_STORAGE_ISOLATION_UNSUPPORTED",
        )
        self._require_success(
            ("chmod", "0700", str(state)),
            "HOST_STORAGE_ISOLATION_UNSUPPORTED",
        )
        self._require_success(
            ("btrfs", "quota", "enable", str(self._btrfs_mount)),
            "HOST_STORAGE_ISOLATION_UNSUPPORTED",
            allow_already_enabled=True,
        )
        self._require_success(
            ("btrfs", "qgroup", "limit", str(plan.durable_state_max_bytes), str(state)),
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
        create_result = self._require_success(
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
        network_id = create_result.stdout.strip()
        if not network_id:
            raise RuntimeDriverError(
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
                "Docker network create did not return an immutable network identity",
            )
        self._network_ids[runtime_id] = network_id
        try:
            network = self._owned_network_info(network_name, runtime_id)
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
            self._nft("add", "chain", "inet", table, "egress")
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
                        "egress",
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
            for resolver in policy.dns_resolver_ipv4_addresses:
                self._nft(
                    "add",
                    "rule",
                    "inet",
                    table,
                    "egress",
                    "ip",
                    "daddr",
                    resolver,
                    "udp",
                    "dport",
                    "53",
                    "counter",
                    "accept",
                )
                self._nft(
                    "add",
                    "rule",
                    "inet",
                    table,
                    "egress",
                    "ip",
                    "daddr",
                    resolver,
                    "tcp",
                    "dport",
                    "53",
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

    def activate_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        self._captured_network_id(runtime_id)
        self.attest_network(plan, network_name, runtime_id)
        network = self._owned_network_info(network_name, runtime_id)
        bridge = self._bridge_name(network)
        table = self._table_name(network_name)
        self._nft(
            "insert",
            "rule",
            "inet",
            table,
            "forward",
            "iifname",
            bridge,
            "counter",
            "jump",
            "egress",
        )
        result = self._runner.run(("nft", "-j", "list", "table", "inet", table))
        if result.returncode != 0:
            self._raise_command(
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
                result,
                "activated nftables generation policy is unavailable",
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "activated nftables generation policy evidence is invalid JSON",
            ) from exc
        self._attest_canonical_nftables(
            payload,
            table,
            bridge,
            self._policy_for(plan),
            active=True,
        )

    def attest_storage(self, plan: RuntimeIsolationPlan, state_path: Path) -> None:
        state = self._approved_state_path(state_path)
        self._attest_qgroup_accounting()
        runtime_uid, runtime_gid = self._runtime_identity(plan)
        ownership = self._runner.run(("stat", "-c", "%u:%g:%a", str(state)))
        if ownership.returncode != 0:
            self._raise_command(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                ownership,
                "runtime state ownership evidence is unavailable",
            )
        if ownership.stdout.strip() != f"{runtime_uid}:{runtime_gid}:700":
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "runtime state owner or mode does not match isolation plan",
            )
        subvolume_id = self._subvolume_id(state)
        result = self._runner.run(
            (
                "btrfs",
                "qgroup",
                "show",
                "--sync",
                "--raw",
                "-r",
                str(self._btrfs_mount),
            )
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
        self._attest_network_state(plan, network_name, runtime_id, active=False)

    def attest_active_network(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
    ) -> None:
        self._attest_network_state(plan, network_name, runtime_id, active=True)

    def _attest_network_state(
        self,
        plan: RuntimeIsolationPlan,
        network_name: str,
        runtime_id: str,
        *,
        active: bool,
    ) -> None:
        policy = self._policy_for(plan)
        network = self._network_info(network_name)
        expected_network_id = self._network_ids.get(runtime_id)
        if expected_network_id is not None:
            self._require_network_identity(network, runtime_id, expected_network_id)
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
        self._attest_network_members(network, plan, runtime_id)
        table = self._table_name(network_name)
        result = self._runner.run(("nft", "-j", "list", "table", "inet", table))
        if result.returncode != 0:
            self._raise_command(
                "HOST_NETWORK_ISOLATION_UNSUPPORTED",
                result,
                "nftables generation policy is unavailable",
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "nftables generation policy evidence is invalid JSON",
            ) from exc
        self._attest_canonical_nftables(
            payload, table, self._bridge_name(network), policy, active=active
        )

    def cleanup_network(self, network_name: str, runtime_id: str) -> None:
        table = self._table_name(network_name)
        expected = self._network_ids.get(runtime_id)
        current = self._runner.run(
            ("docker", "network", "inspect", "--format", "{{json .}}", network_name)
        )
        present = False
        if current.returncode == 0:
            present = True
            network = self._parse_network_ownership(current)
            if expected is None:
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    "immutable network identity is unavailable; refusing name-based cleanup",
                )
            self._require_network_identity(network, runtime_id, expected)
        elif not self._cleanup_target_absent(current):
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                current.stderr.strip() or "generation network ownership evidence is unavailable",
            )
        if expected is None:
            return
        if not present:
            immutable = self._runner.run(
                ("docker", "network", "inspect", "--format", "{{json .}}", expected)
            )
            if immutable.returncode == 0:
                network = self._parse_network_ownership(immutable)
                self._require_network_identity(network, runtime_id, expected)
                present = True
            elif not self._cleanup_target_absent(immutable):
                raise RuntimeDriverError(
                    "GENERATION_OWNERSHIP_CONFLICT",
                    immutable.stderr.strip() or "immutable generation network evidence is unavailable",
                )
        if present:
            removed = self._runner.run(("docker", "network", "rm", expected))
            if removed.returncode != 0 and not self._cleanup_target_absent(removed):
                raise RuntimeDriverError(
                    "HOST_NETWORK_CLEANUP_FAILED",
                    "generation network cleanup was incomplete; retaining nftables policy: "
                    + (removed.stderr.strip() or "Docker network cleanup failed"),
                )
        nft_result = self._runner.run(("nft", "delete", "table", "inet", table))
        if nft_result.returncode != 0 and not self._cleanup_target_absent(nft_result):
            raise RuntimeDriverError(
                "HOST_NETWORK_CLEANUP_FAILED",
                "generation network was removed but nftables table cleanup failed: "
                + (nft_result.stderr.strip() or "nftables table cleanup failed"),
            )
        self._network_ids.pop(runtime_id, None)

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

    @staticmethod
    def _runtime_identity(plan: RuntimeIsolationPlan) -> tuple[int, int]:
        user, separator, group = plan.runtime_user.partition(":")
        if (
            separator != ":"
            or not user.isdigit()
            or not group.isdigit()
            or int(user) == 0
            or int(group) == 0
        ):
            raise RuntimeDriverError(
                "ISOLATION_PLAN_MISMATCH",
                "runtime isolation plan must bind a non-root numeric uid:gid",
            )
        return int(user), int(group)

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

    def _attest_qgroup_accounting(self) -> None:
        filesystem_uuid = self._filesystem_uuid()
        qgroups = self._btrfs_sysfs_root / filesystem_uuid / "qgroups"
        enabled = self._read_qgroup_status(qgroups / "enabled", "enabled")
        inconsistent = self._read_qgroup_status(qgroups / "inconsistent", "inconsistent")
        if enabled != "1" or inconsistent != "0":
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "Btrfs qgroup accounting is disabled or inconsistent",
            )
        mode_path = qgroups / "mode"
        if mode_path.exists():
            try:
                mode = mode_path.read_text(encoding="utf-8").strip().lower()
            except OSError as exc:
                raise RuntimeDriverError(
                    "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                    "Btrfs qgroup accounting mode is unreadable",
                ) from exc
            if mode != "qgroup":
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    "Btrfs storage isolation requires full qgroup accounting",
                )

    def _filesystem_uuid(self) -> str:
        result = self._runner.run(("btrfs", "filesystem", "show", str(self._btrfs_mount)))
        if result.returncode != 0:
            self._raise_command(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                result,
                "Btrfs filesystem identity is unavailable",
            )
        for line in result.stdout.splitlines():
            marker = line.lower().find("uuid:")
            if marker < 0:
                continue
            raw = line[marker + len("uuid:") :].strip().split(maxsplit=1)[0]
            try:
                return str(UUID(raw))
            except (ValueError, AttributeError) as exc:
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    "Btrfs filesystem UUID is invalid",
                ) from exc
        raise RuntimeDriverError(
            "ISOLATION_ATTESTATION_FAILED",
            "Btrfs filesystem UUID is missing",
        )

    @staticmethod
    def _read_qgroup_status(path: Path, field_name: str) -> str:
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeDriverError(
                "HOST_STORAGE_ISOLATION_UNSUPPORTED",
                f"Btrfs qgroup {field_name} status is unavailable",
            ) from exc
        if value not in {"0", "1"}:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                f"Btrfs qgroup {field_name} status is invalid",
            )
        return value

    def _captured_network_id(self, runtime_id: str) -> str:
        network_id = self._network_ids.get(runtime_id)
        if not network_id:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "immutable network identity is unavailable for the requested generation",
            )
        return network_id

    @staticmethod
    def _parse_network_ownership(result: CommandResult) -> dict[str, Any]:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "generation network ownership evidence is invalid",
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "generation network ownership evidence has an unexpected shape",
            )
        return payload

    @staticmethod
    def _require_network_identity(
        network: dict[str, Any], runtime_id: str, expected: str
    ) -> None:
        network_id = network.get("Id")
        labels = network.get("Labels")
        if (
            not isinstance(network_id, str)
            or not network_id
            or not isinstance(labels, dict)
            or labels.get("ai.portal.runtime_id") != runtime_id
            or network_id != expected
        ):
            raise RuntimeDriverError(
                "GENERATION_OWNERSHIP_CONFLICT",
                "generation network immutable identity does not match runtime ownership",
            )

    def _owned_network_info(self, network_name: str, runtime_id: str) -> dict[str, Any]:
        expected = self._captured_network_id(runtime_id)
        network = self._network_info(network_name)
        self._require_network_identity(network, runtime_id, expected)
        return network

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

    def _attest_network_members(
        self,
        network: dict[str, Any],
        plan: RuntimeIsolationPlan,
        runtime_id: str,
    ) -> None:
        containers = network.get("Containers") or {}
        if not isinstance(containers, dict) or len(containers) > 1:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "generation network has an unexpected container membership",
            )
        for container_id, member in containers.items():
            if not isinstance(member, dict) or member.get("Name") != runtime_id:
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    "generation network member is not the exact runtime container",
                )
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
                or member_labels.get("ai.portal.isolation_plan_digest") != plan.digest()
            ):
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    "generation network member identity does not match the trusted runtime",
                )

    def _attest_canonical_nftables(  # noqa: C901 - exact canonical policy comparison.
        self,
        payload: object,
        table: str,
        bridge: str,
        policy: MarketDataEgressPolicy,
        *,
        active: bool = False,
    ) -> None:
        if not isinstance(payload, dict) or not isinstance(payload.get("nftables"), list):
            self._nft_mismatch()
        chains: dict[str, dict[str, Any]] = {}
        rules: dict[str, list[tuple[object, ...]]] = {
            "input": [],
            "forward": [],
            "egress": [],
        }
        table_count = 0
        for entry in payload["nftables"]:
            if not isinstance(entry, dict):
                self._nft_mismatch()
            if "metainfo" in entry:
                continue
            if "table" in entry:
                table_entry = entry["table"]
                if (
                    not isinstance(table_entry, dict)
                    or table_entry.get("family") != "inet"
                    or table_entry.get("name") != table
                ):
                    self._nft_mismatch()
                table_count += 1
                continue
            if "chain" in entry:
                chain = entry["chain"]
                if (
                    not isinstance(chain, dict)
                    or chain.get("family") != "inet"
                    or chain.get("table") != table
                    or chain.get("name") not in rules
                ):
                    self._nft_mismatch()
                chains[str(chain["name"])] = chain
                continue
            if "rule" in entry:
                rule = entry["rule"]
                if (
                    not isinstance(rule, dict)
                    or rule.get("family") != "inet"
                    or rule.get("table") != table
                    or rule.get("chain") not in rules
                ):
                    self._nft_mismatch()
                rules[str(rule["chain"])].append(self._nft_rule_signature(rule))
                continue
            self._nft_mismatch()
        if table_count != 1 or set(chains) != {"input", "forward", "egress"}:
            self._nft_mismatch()
        self._require_chain(chains["input"], hook="input")
        self._require_chain(chains["forward"], hook="forward")
        self._require_regular_chain(chains["egress"])
        expected_input, expected_forward, expected_egress = self._expected_nft_rule_signatures(
            bridge,
            policy,
            active=active,
        )
        if (
            rules["input"] != expected_input
            or rules["forward"] != expected_forward
            or rules["egress"] != expected_egress
        ):
            self._nft_mismatch()

    @staticmethod
    def _require_chain(chain: dict[str, Any], *, hook: str) -> None:
        if (
            chain.get("type") != "filter"
            or chain.get("hook") != hook
            or chain.get("prio") != -40
            or chain.get("policy") != "accept"
        ):
            LinuxNftablesBtrfsIsolationAttestor._nft_mismatch()

    @staticmethod
    def _require_regular_chain(chain: dict[str, Any]) -> None:
        if any(key in chain for key in ("hook", "prio", "policy")):
            LinuxNftablesBtrfsIsolationAttestor._nft_mismatch()

    @classmethod
    def _nft_rule_signature(cls, rule: dict[str, Any]) -> tuple[object, ...]:
        expressions = rule.get("expr")
        if not isinstance(expressions, list):
            cls._nft_mismatch()
        signature: list[object] = []
        for expression in expressions:
            if not isinstance(expression, dict):
                cls._nft_mismatch()
            if "counter" in expression:
                continue
            if "match" in expression:
                match = expression["match"]
                if not isinstance(match, dict):
                    cls._nft_mismatch()
                signature.append(cls._nft_match_signature(match))
                continue
            if set(expression) == {"accept"}:
                signature.append(("verdict", "accept"))
                continue
            if set(expression) == {"drop"}:
                signature.append(("verdict", "drop"))
                continue
            if set(expression) == {"jump"}:
                jump = expression["jump"]
                if not isinstance(jump, dict) or set(jump) != {"target"}:
                    cls._nft_mismatch()
                signature.append(("verdict", "jump", str(jump["target"])))
                continue
            cls._nft_mismatch()
        return tuple(signature)

    @classmethod
    def _nft_match_signature(cls, match: dict[str, Any]) -> tuple[object, ...]:
        left = match.get("left")
        if not isinstance(left, dict):
            cls._nft_mismatch()
        selector: tuple[str, str, str]
        if isinstance(left.get("meta"), dict):
            key = left["meta"].get("key")
            if key not in {"iifname", "oifname"}:
                cls._nft_mismatch()
            selector = ("meta", str(key), "")
        elif isinstance(left.get("payload"), dict):
            protocol = left["payload"].get("protocol")
            field = left["payload"].get("field")
            if (protocol, field) not in {
                ("ip", "daddr"),
                ("tcp", "dport"),
                ("udp", "dport"),
            }:
                cls._nft_mismatch()
            selector = ("payload", str(protocol), str(field))
        elif isinstance(left.get("ct"), dict) and left["ct"].get("key") == "state":
            selector = ("ct", "state", "")
        else:
            cls._nft_mismatch()
        return (*selector, str(match.get("op")), cls._normalize_nft_value(match.get("right")))

    @classmethod
    def _normalize_nft_value(cls, value: object) -> object:
        if isinstance(value, dict) and set(value) == {"prefix"}:
            prefix = value["prefix"]
            if not isinstance(prefix, dict) or not isinstance(prefix.get("addr"), str):
                cls._nft_mismatch()
            try:
                target = f"{prefix['addr']}/{int(prefix['len'])}"
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeDriverError(
                    "ISOLATION_ATTESTATION_FAILED",
                    "nftables prefix evidence is invalid",
                ) from exc
            return cls._canonical_ipv4_target(target)
        if isinstance(value, dict) and set(value) == {"set"}:
            members = value["set"]
            if not isinstance(members, list):
                cls._nft_mismatch()
            return tuple(sorted(str(member) for member in members))
        if isinstance(value, list):
            return tuple(sorted(str(member) for member in value))
        return value

    @classmethod
    def _canonical_ipv4_target(cls, value: str) -> str:
        try:
            network = ipaddress.ip_network(value, strict=True)
        except ValueError as exc:
            raise RuntimeDriverError(
                "ISOLATION_ATTESTATION_FAILED",
                "nftables IPv4 target evidence is invalid",
            ) from exc
        if not isinstance(network, ipaddress.IPv4Network):
            cls._nft_mismatch()
        if network.prefixlen == network.max_prefixlen:
            return str(network.network_address)
        return str(network)

    @classmethod
    def _expected_nft_rule_signatures(
        cls,
        bridge: str,
        policy: MarketDataEgressPolicy,
        *,
        active: bool,
    ) -> tuple[
        list[tuple[object, ...]],
        list[tuple[object, ...]],
        list[tuple[object, ...]],
    ]:
        input_rules: list[tuple[object, ...]] = [
            (("meta", "iifname", "", "==", bridge), ("verdict", "drop"))
        ]
        forward_rules: list[tuple[object, ...]] = []
        if active:
            forward_rules.append(
                (("meta", "iifname", "", "==", bridge), ("verdict", "jump", "egress"))
            )
        forward_rules.extend(
            [
                (
                    ("meta", "iifname", "", "==", bridge),
                    ("meta", "oifname", "", "==", bridge),
                    ("verdict", "accept"),
                ),
                (("meta", "iifname", "", "==", bridge), ("verdict", "drop")),
            ]
        )
        states = ("established", "new")
        egress_rules: list[tuple[object, ...]] = []
        for cidr in policy.allowed_ipv4_cidrs:
            target = cls._canonical_ipv4_target(cidr)
            for port in policy.allowed_tcp_ports:
                egress_rules.append(
                    (
                        ("payload", "ip", "daddr", "==", target),
                        ("payload", "tcp", "dport", "==", port),
                        ("ct", "state", "", "in", states),
                        ("verdict", "accept"),
                    )
                )
        for resolver in policy.dns_resolver_ipv4_addresses:
            egress_rules.append(
                (
                    ("payload", "ip", "daddr", "==", resolver),
                    ("payload", "udp", "dport", "==", 53),
                    ("verdict", "accept"),
                )
            )
            egress_rules.append(
                (
                    ("payload", "ip", "daddr", "==", resolver),
                    ("payload", "tcp", "dport", "==", 53),
                    ("ct", "state", "", "in", states),
                    ("verdict", "accept"),
                )
            )
        return input_rules, forward_rules, egress_rules

    @staticmethod
    def _nft_mismatch() -> NoReturn:
        raise RuntimeDriverError(
            "ISOLATION_ATTESTATION_FAILED",
            "effective nftables generation policy does not match the canonical policy",
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
        max_rfer_index: int | None = None
        for line in output.splitlines():
            fields = line.split()
            if not fields:
                continue
            normalized_fields = [field.lower() for field in fields]
            if normalized_fields[0] == "qgroupid":
                if "max_rfer" in normalized_fields:
                    max_rfer_index = normalized_fields.index("max_rfer")
                else:
                    max_rfer_index = next(
                        (
                            index
                            for index in range(len(normalized_fields) - 1)
                            if normalized_fields[index : index + 2] == ["max", "referenced"]
                        ),
                        None,
                    )
                    if max_rfer_index is None:
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
