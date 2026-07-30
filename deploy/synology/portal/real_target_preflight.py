#!/usr/bin/env python3
"""Secret-free, read-only inventory for the real Synology portal target."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

EXPECTED_REQUEST = {
    "schema_version": 1,
    "request_id": "portal-real-target-readonly-preflight-20260730-v1",
    "expected_runner_name": "freqtrade-synology-staging",
    "expected_runner_label": "freqtrade-staging",
    "expected_environment": "synology-staging",
    "mutation_authorized": False,
    "bootstrap_authorized": False,
    "restore_authorized": False,
    "live_capital_authorized": False,
}

SAFE_ENV_VALUES = {
    "NODE_ENV",
    "PORTAL_ENVIRONMENT",
    "PORTAL_IDENTITY_FIXTURE_MODE",
    "PORTAL_WEB_DATA_MODE",
    "FREQTRADE__DRY_RUN",
    "DRY_RUN",
}
PRESENCE_ONLY_ENV = {
    "PORTAL_CONTROL_PLANE_URL",
    "PORTAL_DATABASE_URL",
    "PORTAL_IDENTITY_ISSUER_URL",
    "PORTAL_OIDC_CLIENT_ID",
    "PORTAL_OIDC_CLIENT_SECRET",
    "PORTAL_SESSION_HMAC_KEY_B64",
    "PORTAL_FLOW_ENCRYPTION_KEY_B64",
    "PORTAL_VAULT_ADDR",
    "VAULT_ADDR",
    "VAULT_ROLE_ID",
    "VAULT_SECRET_ID",
    "TUNNEL_TOKEN",
}
SAFE_VALUE_RE = re.compile(r"^[A-Za-z0-9_.:-]{0,64}$")
MIGRATION_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


def run_command(*args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def load_request(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data != EXPECTED_REQUEST:
        raise ValueError("request does not match the frozen read-only contract")
    return data


def bind_scope(address: str) -> str:
    normalized = address.strip().lower()
    if normalized in {"127.0.0.1", "::1", "localhost"}:
        return "loopback"
    if normalized in {"0.0.0.0", "::", ""}:
        return "all_interfaces"
    if normalized.startswith(
        (
            "10.",
            "192.168.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.2",
            "172.30.",
            "172.31.",
        )
    ):
        return "private_lan"
    return "specific_interface"


def parse_env(entries: Iterable[str]) -> tuple[list[str], dict[str, str], dict[str, bool]]:
    names: list[str] = []
    safe_values: dict[str, str] = {}
    presence: dict[str, bool] = {}
    for entry in entries:
        name, separator, value = entry.partition("=")
        if not separator or not name:
            continue
        names.append(name)
        if name in SAFE_ENV_VALUES:
            safe_values[name] = (
                value if SAFE_VALUE_RE.fullmatch(value) else "INVALID_OR_REDACTED"
            )
        if name in PRESENCE_ONLY_ENV:
            presence[name] = bool(value)
    return (
        sorted(set(names)),
        dict(sorted(safe_values.items())),
        dict(sorted(presence.items())),
    )


def source_fingerprint(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def relevant_role(name: str, image: str, labels: dict[str, str]) -> str | None:
    haystack = " ".join(
        [
            name.lower(),
            image.lower(),
            labels.get("com.docker.compose.project", "").lower(),
            labels.get("com.docker.compose.service", "").lower(),
        ]
    )
    if name == "freqtrade-portal-staging" or "portal-web" in haystack:
        return "portal_web"
    if "portal-api" in haystack or "control-plane" in haystack:
        return "portal_api"
    if "portal-authentik" in haystack or "authentik" in image.lower():
        if "postgres" in haystack:
            return "authentik_postgresql"
        return "authentik"
    if "portal-vault" in haystack or "hashicorp/vault" in image.lower():
        return "vault"
    if "cloudflared" in haystack:
        return "cloudflare_tunnel"
    if "postgres" in haystack and "portal" in haystack:
        return "portal_postgresql"
    if "nats" in haystack and "portal" in haystack:
        return "portal_nats"
    if "redis" in haystack and "portal" in haystack:
        return "portal_redis"
    if "freqtrade" in haystack and "runner" not in haystack and "portal" not in haystack:
        return "freqtrade_runtime"
    if name == "freqtrade-synology-staging-runner":
        return "github_runner"
    return None


def health_state(container: dict[str, Any]) -> str:
    state = container.get("State") or {}
    health = state.get("Health") or {}
    return str(health.get("Status") or state.get("Status") or "unknown")


def published_ports(container: dict[str, Any]) -> list[dict[str, Any]]:
    ports = ((container.get("NetworkSettings") or {}).get("Ports") or {})
    result: list[dict[str, Any]] = []
    for container_port, bindings in sorted(ports.items()):
        for binding in bindings or []:
            result.append(
                {
                    "container_port": container_port,
                    "host_port": str(binding.get("HostPort") or ""),
                    "bind_scope": bind_scope(str(binding.get("HostIp") or "")),
                }
            )
    return result


def sanitized_mounts(container: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for mount in container.get("Mounts") or []:
        source = str(mount.get("Source") or mount.get("Name") or "")
        result.append(
            {
                "destination": str(mount.get("Destination") or ""),
                "type": str(mount.get("Type") or ""),
                "read_write": bool(mount.get("RW")),
                "source_fingerprint": source_fingerprint(source),
            }
        )
    return sorted(result, key=lambda item: (item["destination"], item["type"]))


def config_fingerprint(record: dict[str, Any]) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def bounded_http_status(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "portal-real-target-preflight/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return {"reachable": True, "status": int(response.status)}
    except urllib.error.HTTPError as error:
        return {"reachable": True, "status": int(error.code)}
    except (urllib.error.URLError, TimeoutError, ValueError):
        return {"reachable": False, "status": None}


def container_probe_url(container: dict[str, Any]) -> str | None:
    ports = ((container.get("NetworkSettings") or {}).get("Ports") or {})
    for key in ("3000/tcp", "8000/tcp", "8080/tcp"):
        for binding in ports.get(key) or []:
            host_ip = str(binding.get("HostIp") or "")
            host_port = str(binding.get("HostPort") or "")
            if host_port:
                host = "127.0.0.1" if host_ip in {"0.0.0.0", "::", ""} else host_ip
                return f"http://{host}:{host_port}/"
    return None


def vault_status(container_name: str) -> dict[str, Any]:
    result = run_command(
        "docker", "exec", container_name, "vault", "status", "-format=json"
    )
    if result.returncode not in {0, 2}:
        return {"available": False}
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"available": False}
    return {
        "available": True,
        "initialized": bool(payload.get("initialized")),
        "sealed": bool(payload.get("sealed")),
        "storage_type": str(payload.get("storage_type") or ""),
        "ha_enabled": bool(payload.get("ha_enabled")),
        "version": str(payload.get("version") or ""),
    }


def migration_revision(container_name: str) -> str | None:
    result = run_command("docker", "exec", container_name, "alembic", "current", timeout=20)
    if result.returncode:
        return None
    candidates = [token.strip("(),") for token in result.stdout.split()]
    for token in candidates:
        if MIGRATION_RE.fullmatch(token) and any(character.isdigit() for character in token):
            return token
    return None


def inspect_containers() -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    ps = run_command("docker", "ps", "-aq")
    if ps.returncode:
        return [], ["docker_container_inventory_failed"]
    ids = [line.strip() for line in ps.stdout.splitlines() if line.strip()]
    if not ids:
        return [], blockers
    inspected = run_command("docker", "inspect", *ids, timeout=45)
    if inspected.returncode:
        return [], ["docker_inspect_failed"]
    try:
        containers = json.loads(inspected.stdout)
    except json.JSONDecodeError:
        return [], ["docker_inspect_unparseable"]

    result: list[dict[str, Any]] = []
    for container in containers:
        name = str(container.get("Name") or "").lstrip("/")
        config = container.get("Config") or {}
        labels = {
            str(key): str(value)
            for key, value in (config.get("Labels") or {}).items()
        }
        image = str(config.get("Image") or "")
        role = relevant_role(name, image, labels)
        if role is None:
            continue
        env_names, safe_env, env_presence = parse_env(config.get("Env") or [])
        host_config = container.get("HostConfig") or {}
        record: dict[str, Any] = {
            "id": str(container.get("Id") or "")[:12],
            "name": name,
            "role": role,
            "image_ref": image,
            "image_id": str(container.get("Image") or ""),
            "state": str((container.get("State") or {}).get("Status") or "unknown"),
            "health": health_state(container),
            "restart_policy": str(
                (host_config.get("RestartPolicy") or {}).get("Name") or "no"
            ),
            "compose_project": labels.get("com.docker.compose.project", ""),
            "compose_service": labels.get("com.docker.compose.service", ""),
            "deployment_commit": labels.get(
                "io.freqtrade.portal.commit",
                labels.get("org.opencontainers.image.revision", ""),
            ),
            "ports": published_ports(container),
            "networks": sorted(
                ((container.get("NetworkSettings") or {}).get("Networks") or {}).keys()
            ),
            "mounts": sanitized_mounts(container),
            "limits": {
                "memory_bytes": int(host_config.get("Memory") or 0),
                "nano_cpus": int(host_config.get("NanoCpus") or 0),
                "pids_limit": host_config.get("PidsLimit"),
                "read_only_rootfs": bool(host_config.get("ReadonlyRootfs")),
                "privileged": bool(host_config.get("Privileged")),
                "network_mode": str(host_config.get("NetworkMode") or ""),
                "user": str(config.get("User") or ""),
            },
            "environment_names": env_names,
            "safe_environment": safe_env,
            "environment_presence": env_presence,
        }
        fingerprint_material = {
            "image_id": record["image_id"],
            "ports": record["ports"],
            "networks": record["networks"],
            "mounts": record["mounts"],
            "safe_environment": safe_env,
            "environment_presence": env_presence,
        }
        record["sanitized_configuration_fingerprint"] = config_fingerprint(
            fingerprint_material
        )
        if role == "portal_web":
            probe_url = container_probe_url(container)
            record["lan_probe"] = (
                bounded_http_status(probe_url)
                if probe_url
                else {"reachable": False, "status": None}
            )
        elif role == "vault" and record["state"] == "running":
            record["vault_status"] = vault_status(name)
        elif role == "portal_api" and record["state"] == "running":
            record["migration_revision"] = migration_revision(name)
        result.append(record)
    return sorted(result, key=lambda item: (item["role"], item["name"])), blockers


def docker_summary() -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    info = run_command("docker", "info", "--format", "{{json .}}")
    if info.returncode:
        return {}, ["docker_info_unavailable"]
    try:
        payload = json.loads(info.stdout)
    except json.JSONDecodeError:
        return {}, ["docker_info_unparseable"]
    compose = run_command("docker", "compose", "version", "--short")
    if compose.returncode:
        blockers.append("docker_compose_v2_unavailable")
    return {
        "architecture": str(payload.get("Architecture") or ""),
        "cpus": int(payload.get("NCPU") or 0),
        "memory_bytes": int(payload.get("MemTotal") or 0),
        "server_version": str(payload.get("ServerVersion") or ""),
        "compose_v2_present": compose.returncode == 0,
    }, blockers


def disk_summary() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for label, path in (
        ("root", Path("/")),
        (
            "staging_state",
            Path(
                os.environ.get(
                    "FREQTRADE_STAGING_STATE_DIR", "/var/lib/freqtrade-staging-state"
                )
            ),
        ),
    ):
        if path.is_dir():
            usage = shutil.disk_usage(path)
            result[label] = {
                "present": True,
                "total_bytes": usage.total,
                "free_bytes": usage.free,
            }
        else:
            result[label] = {
                "present": False,
                "total_bytes": 0,
                "free_bytes": 0,
            }
    return result


def build_report(request: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    runner_name = os.environ.get("RUNNER_NAME_VALUE", "")
    runner_os = os.environ.get("RUNNER_OS_VALUE", "")
    runner_arch = os.environ.get("RUNNER_ARCH_VALUE", "")
    expected_env = os.environ.get("TARGET_ENVIRONMENT_VALUE", "")
    if runner_name != request["expected_runner_name"]:
        blockers.append("runner_name_mismatch")
    if runner_os != "Linux":
        blockers.append("runner_os_not_linux")
    if expected_env != request["expected_environment"]:
        blockers.append("environment_mismatch")

    docker, docker_blockers = docker_summary()
    containers, container_blockers = inspect_containers()
    blockers.extend(docker_blockers)
    blockers.extend(container_blockers)

    roles = {item["role"] for item in containers}
    portal = next((item for item in containers if item["role"] == "portal_web"), None)
    current_mode = {
        "portal_present": portal is not None,
        "data_mode": (portal or {}).get("safe_environment", {}).get(
            "PORTAL_WEB_DATA_MODE", "UNKNOWN"
        ),
        "identity_fixture_mode": (portal or {}).get("safe_environment", {}).get(
            "PORTAL_IDENTITY_FIXTURE_MODE", "UNKNOWN"
        ),
        "environment": (portal or {}).get("safe_environment", {}).get(
            "PORTAL_ENVIRONMENT", "UNKNOWN"
        ),
        "control_plane_url_present": bool(
            (portal or {})
            .get("environment_presence", {})
            .get("PORTAL_CONTROL_PLANE_URL")
        ),
    }

    public_config = {
        "portal_public_base_url_present": bool(
            os.environ.get("PI06_PORTAL_PUBLIC_BASE_URL")
        ),
        "authentik_public_base_url_present": bool(
            os.environ.get("PI06_AUTHENTIK_PUBLIC_BASE_URL")
        ),
        "portal_identity_client_id_present": bool(
            os.environ.get("PI06_PORTAL_IDENTITY_CLIENT_ID")
        ),
    }

    acceptance_blockers: list[str] = []
    required_roles = {
        "portal_web": "portal_web_missing",
        "portal_api": "portal_api_missing",
        "portal_postgresql": "portal_postgresql_missing",
        "authentik": "authentik_missing",
        "authentik_postgresql": "authentik_postgresql_missing",
        "vault": "vault_missing",
        "cloudflare_tunnel": "cloudflare_tunnel_container_missing_or_unverified",
        "freqtrade_runtime": "freqtrade_runtime_missing",
    }
    for role, marker in required_roles.items():
        if role not in roles:
            acceptance_blockers.append(marker)
    if portal is not None:
        if current_mode["data_mode"] != "api":
            acceptance_blockers.append("portal_api_data_mode_not_active")
        if current_mode["identity_fixture_mode"] == "enabled":
            acceptance_blockers.append("portal_identity_fixture_active")
        if not current_mode["control_plane_url_present"]:
            acceptance_blockers.append("portal_control_plane_url_missing")
        if not (portal.get("lan_probe") or {}).get("reachable"):
            acceptance_blockers.append("portal_lan_probe_unreachable")
    for key, present in public_config.items():
        if not present:
            acceptance_blockers.append(f"{key}_missing")

    role_vocabulary = {
        "portal_web",
        "portal_api",
        "portal_postgresql",
        "authentik",
        "authentik_postgresql",
        "vault",
        "cloudflare_tunnel",
        "freqtrade_runtime",
        "portal_redis",
        "portal_nats",
    }
    return {
        "schema_version": 1,
        "report_id": request["request_id"],
        "request_head": os.environ.get("HEAD_SHA", ""),
        "classification": "READ_ONLY_PREFLIGHT",
        "runner": {
            "name_matches": runner_name == request["expected_runner_name"],
            "os_is_linux": runner_os == "Linux",
            "arch": runner_arch,
            "selected_custom_label": request["expected_runner_label"],
            "environment": expected_env,
        },
        "docker": docker,
        "disk": disk_summary(),
        "containers": containers,
        "role_presence": {role: role in roles for role in sorted(role_vocabulary)},
        "current_portal_mode": current_mode,
        "public_configuration_presence": public_config,
        "rollback_record": {
            "previous_container_name": (portal or {}).get("name"),
            "previous_image_id": (portal or {}).get("image_id"),
            "previous_deployment_commit": (portal or {}).get("deployment_commit"),
            "previous_sanitized_configuration_fingerprint": (portal or {}).get(
                "sanitized_configuration_fingerprint"
            ),
            "previous_migration_revision": next(
                (
                    item.get("migration_revision")
                    for item in containers
                    if item["role"] == "portal_api"
                ),
                None,
            ),
            "backup_snapshot_identifiers": [],
            "rollback_commands_recorded": False,
        },
        "blockers": sorted(set(blockers)),
        "acceptance_blockers": sorted(set(acceptance_blockers)),
        "safety": {
            "mutation_executed": False,
            "bootstrap_executed": False,
            "restore_executed": False,
            "live_capital_authorized": False,
            "secret_values_recorded": False,
            "private_mount_sources_recorded": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    try:
        request = load_request(args.request)
        report = build_report(request)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"preflight failed: {error.__class__.__name__}", file=sys.stderr)
        return 2

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not report["blockers"] and not report["acceptance_blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
