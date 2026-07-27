#!/usr/bin/env python3
"""Read-only target preflight for PI-06 Authentik on Synology staging."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


AUTHENTIK_IMAGE = (
    "docker.io/authentik/server:2026.5.5@"
    "sha256:50a833c48a714709f15d4f8846ec6b81a41d0d6a6bd2975087dfed3000d0d72e"
)
POSTGRES_IMAGE = (
    "docker.io/library/postgres:16.13-alpine3.23@"
    "sha256:57c72fd2a128e416c7fcc499958864df5301e940bca0a56f58fddf30ffc07777"
)
EXPECTED_REQUEST = {
    "schema_version": 1,
    "request_id": "portal-pi06-authentik-synology-target-preflight-20260727-v1",
    "expected_runner_name": "freqtrade-synology-staging",
    "expected_runner_label": "freqtrade-staging",
    "expected_environment": "synology-staging",
    "expected_state_dir": "/var/lib/freqtrade-staging-state",
    "target_root": "/var/lib/freqtrade-staging-state/portal-authentik",
    "backup_root": "/var/lib/freqtrade-staging-state/portal-authentik-backups",
    "restore_root": "/var/lib/freqtrade-staging-state/portal-authentik-restore",
    "authentik_http_port": 9000,
    "bounded_storage_probe_authorized": True,
    "deployment_mutation_authorized": False,
    "bootstrap_authorized": False,
    "restore_authorized": False,
}
SENSITIVE_ENV = {
    "PI06_AUTHENTIK_POSTGRES_PASSWORD",
    "PI06_AUTHENTIK_SECRET_KEY",
    "PI06_AUTHENTIK_BOOTSTRAP_PASSWORD_HASH",
    "PI06_PORTAL_OIDC_CLIENT_SECRET",
    "PI06_PORTAL_SESSION_HMAC_KEY_B64",
    "PI06_PORTAL_FLOW_ENCRYPTION_KEY_B64",
    "PI06_AUTHENTIK_AGE_RECIPIENT",
}
PUBLIC_ENV = {
    "PI06_AUTHENTIK_PUBLIC_BASE_URL",
    "PI06_PORTAL_PUBLIC_BASE_URL",
    "PI06_PORTAL_IDENTITY_CLIENT_ID",
}
PLACEHOLDER_RE = re.compile(r"(REPLACE|CHANGEME|EXAMPLE|<|>)", re.IGNORECASE)
EXPECTED_VOLUMES = {
    "portal_authentik_postgresql_data",
    "portal_authentik_media",
    "portal_authentik_templates",
}
EXPECTED_NETWORKS = {"portal_authentik_front", "portal_authentik_data"}


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def decode_base64_at_least(value: str, minimum: int) -> bool:
    try:
        return len(base64.b64decode(value, validate=True)) >= minimum
    except (ValueError, TypeError):
        return False


def valid_secret_material(env: dict[str, str]) -> tuple[list[str], list[str]]:
    missing = sorted(name for name in SENSITIVE_ENV if not env.get(name))
    invalid: list[str] = []
    password = env.get("PI06_AUTHENTIK_POSTGRES_PASSWORD", "")
    if password and (PLACEHOLDER_RE.search(password) or not 32 <= len(password) <= 99):
        invalid.append("PI06_AUTHENTIK_POSTGRES_PASSWORD")
    secret_key = env.get("PI06_AUTHENTIK_SECRET_KEY", "")
    if secret_key and (PLACEHOLDER_RE.search(secret_key) or len(secret_key) < 50):
        invalid.append("PI06_AUTHENTIK_SECRET_KEY")
    bootstrap_hash = env.get("PI06_AUTHENTIK_BOOTSTRAP_PASSWORD_HASH", "")
    if bootstrap_hash and (PLACEHOLDER_RE.search(bootstrap_hash) or "$" not in bootstrap_hash):
        invalid.append("PI06_AUTHENTIK_BOOTSTRAP_PASSWORD_HASH")
    oidc_secret = env.get("PI06_PORTAL_OIDC_CLIENT_SECRET", "")
    if oidc_secret and (PLACEHOLDER_RE.search(oidc_secret) or len(oidc_secret) < 24):
        invalid.append("PI06_PORTAL_OIDC_CLIENT_SECRET")
    for name in (
        "PI06_PORTAL_SESSION_HMAC_KEY_B64",
        "PI06_PORTAL_FLOW_ENCRYPTION_KEY_B64",
    ):
        value = env.get(name, "")
        if value and not decode_base64_at_least(value, 32):
            invalid.append(name)
    recipient = env.get("PI06_AUTHENTIK_AGE_RECIPIENT", "")
    if recipient and not recipient.startswith("age1"):
        invalid.append("PI06_AUTHENTIK_AGE_RECIPIENT")
    return missing, sorted(invalid)


def valid_public_configuration(
    env: dict[str, str],
) -> tuple[list[str], list[str], dict[str, bool]]:
    missing = sorted(name for name in PUBLIC_ENV if not env.get(name))
    invalid: list[str] = []
    dns = {"authentik_host_resolves": False, "portal_host_resolves": False}
    for name, report_key in (
        ("PI06_AUTHENTIK_PUBLIC_BASE_URL", "authentik_host_resolves"),
        ("PI06_PORTAL_PUBLIC_BASE_URL", "portal_host_resolves"),
    ):
        value = env.get(name, "")
        if not value:
            continue
        parsed = urlparse(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.hostname.endswith(".invalid")
        ):
            invalid.append(name)
            continue
        try:
            socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        except socket.gaierror:
            invalid.append(f"{name}:dns")
        else:
            dns[report_key] = True
    client_id = env.get("PI06_PORTAL_IDENTITY_CLIENT_ID", "")
    if client_id and (PLACEHOLDER_RE.search(client_id) or len(client_id) > 128):
        invalid.append("PI06_PORTAL_IDENTITY_CLIENT_ID")
    return missing, sorted(invalid), dns


def check_paths(request: dict[str, Any], env: dict[str, str]) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    state_dir = Path(env.get("FREQTRADE_STAGING_STATE_DIR", ""))
    expected_state = Path(request["expected_state_dir"])
    if state_dir != expected_state:
        blockers.append("FREQTRADE_STAGING_STATE_DIR")
    if not state_dir.is_absolute() or not state_dir.is_dir():
        blockers.append("state_dir_missing")
    elif not os.access(state_dir, os.W_OK):
        blockers.append("state_dir_not_writable")
    workspace = Path(env.get("GITHUB_WORKSPACE", "/nonexistent")).resolve()
    runner_temp = Path(env.get("RUNNER_TEMP", "/nonexistent")).resolve()
    roots: dict[str, str] = {}
    for key in ("target_root", "backup_root", "restore_root"):
        root = Path(request[key])
        roots[key] = str(root)
        if root.parent != expected_state:
            blockers.append(f"{key}_outside_state_dir")
        resolved = root.resolve()
        if resolved == workspace or workspace in resolved.parents:
            blockers.append(f"{key}_inside_workspace")
        if resolved == runner_temp or runner_temp in resolved.parents:
            blockers.append(f"{key}_inside_runner_temp")
    if len(set(roots.values())) != 3:
        blockers.append("target_backup_restore_roots_not_distinct")
    probe_sha256 = ""
    free_bytes = 0
    path_ready = not {
        "FREQTRADE_STAGING_STATE_DIR",
        "state_dir_missing",
        "state_dir_not_writable",
    }.intersection(blockers)
    if path_ready:
        probe_dir = Path(tempfile.mkdtemp(prefix=".pi06-preflight-", dir=state_dir))
        try:
            source = probe_dir / "probe.tmp"
            sealed = probe_dir / "probe.sealed"
            payload = b"portal-pi06-authentik-synology-target-preflight-v1\n"
            with source.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            source.replace(sealed)
            observed = sealed.read_bytes()
            if observed != payload:
                blockers.append("durable_storage_readback")
            probe_sha256 = hashlib.sha256(observed).hexdigest()
        finally:
            shutil.rmtree(probe_dir)
        free_bytes = shutil.disk_usage(state_dir).free
        if free_bytes < 4 * 1024**3:
            blockers.append("state_dir_less_than_4_gib_free")
    return sorted(set(blockers)), {
        "state_dir": str(state_dir),
        "roots": roots,
        "free_bytes": free_bytes,
        "atomic_write_fsync_rename_readback": bool(probe_sha256),
        "probe_sha256": probe_sha256,
    }


def docker_host_capacity(blockers: list[str]) -> tuple[str, int, int]:
    info = run_command("docker", "info", "--format", "{{.Architecture}}|{{.NCPU}}|{{.MemTotal}}")
    if info.returncode:
        blockers.append("docker_info_unavailable")
        return "", 0, 0
    try:
        architecture, cpu, memory = info.stdout.strip().split("|")
        cpu_count = int(cpu)
        memory_bytes = int(memory)
    except (ValueError, TypeError):
        blockers.append("docker_info_unparseable")
        return "", 0, 0
    if architecture not in {"x86_64", "aarch64", "amd64", "arm64"}:
        blockers.append("unsupported_docker_architecture")
    if cpu_count < 2:
        blockers.append("fewer_than_2_cpu_cores")
    if memory_bytes < 2 * 1024**3:
        blockers.append("less_than_2_gib_memory")
    return architecture, cpu_count, memory_bytes


def docker_named_inventory(
    kind: str,
    expected: set[str],
    blockers: list[str],
    *,
    failure: str,
    partial: str,
) -> set[str]:
    inventory = run_command("docker", kind, "ls", "--format", "{{.Name}}")
    if inventory.returncode:
        blockers.append(failure)
        return set()
    present = expected & set(inventory.stdout.splitlines())
    if 0 < len(present) < len(expected):
        blockers.append(partial)
    return present


def docker_container_inventory(request: dict[str, Any], blockers: list[str]) -> tuple[int, int]:
    containers = run_command("docker", "ps", "--format", "{{.Names}}\t{{.Ports}}")
    if containers.returncode:
        blockers.append("docker_container_inventory_failed")
        return 0, 0
    matching_containers = 0
    port_conflicts = 0
    token = f":{request['authentik_http_port']}->"
    for line in containers.stdout.splitlines():
        name, _, ports = line.partition("\t")
        if name.startswith("portal-authentik"):
            matching_containers += 1
        elif token in ports:
            port_conflicts += 1
    if port_conflicts:
        blockers.append("authentik_http_port_conflict")
    return matching_containers, port_conflicts


def check_docker(request: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    socket_path = Path("/var/run/docker.sock")
    if not socket_path.exists():
        blockers.append("docker_socket_missing")
    elif not os.access(socket_path, os.R_OK | os.W_OK):
        blockers.append("docker_socket_not_accessible")
    version = run_command("docker", "version", "--format", "{{.Server.Version}}")
    compose = run_command("docker", "compose", "version", "--short")
    if version.returncode:
        blockers.append("docker_server_unavailable")
    if compose.returncode:
        blockers.append("docker_compose_v2_unavailable")
    architecture, cpu_count, memory_bytes = docker_host_capacity(blockers)
    present_volumes = docker_named_inventory(
        "volume",
        EXPECTED_VOLUMES,
        blockers,
        failure="docker_volume_inventory_failed",
        partial="partial_existing_authentik_volume_state",
    )
    present_networks = docker_named_inventory(
        "network",
        EXPECTED_NETWORKS,
        blockers,
        failure="docker_network_inventory_failed",
        partial="partial_existing_authentik_network_state",
    )
    matching_containers, port_conflicts = docker_container_inventory(request, blockers)
    return sorted(set(blockers)), {
        "socket_present": socket_path.exists(),
        "server_version_present": not version.returncode,
        "compose_v2_present": not compose.returncode,
        "architecture": architecture,
        "cpu_count": cpu_count,
        "memory_bytes": memory_bytes,
        "expected_volumes_present": len(present_volumes),
        "expected_networks_present": len(present_networks),
        "matching_running_containers": matching_containers,
        "conflicting_port_publishers": port_conflicts,
    }


def validate_runtime_render(root: Path, env: dict[str, str]) -> list[str]:
    blockers: list[str] = []
    runtime = {
        "AUTHENTIK_IMAGE": AUTHENTIK_IMAGE,
        "POSTGRES_IMAGE": POSTGRES_IMAGE,
        "AUTHENTIK_POSTGRESQL__NAME": "authentik",
        "AUTHENTIK_POSTGRESQL__USER": "authentik",
        "AUTHENTIK_POSTGRESQL__PASSWORD": env.get("PI06_AUTHENTIK_POSTGRES_PASSWORD", ""),
        "AUTHENTIK_SECRET_KEY": env.get("PI06_AUTHENTIK_SECRET_KEY", ""),
        "AUTHENTIK_BIND_ADDRESS": "127.0.0.1",
        "AUTHENTIK_HTTP_PORT": "9000",
        "AUTHENTIK_BOOTSTRAP_PASSWORD_HASH": "",
    }
    with tempfile.TemporaryDirectory(prefix="pi06-runtime-", dir=env["RUNNER_TEMP"]) as temp:
        env_file = Path(temp) / "runtime.env"
        env_file.write_text(
            "".join(f"{key}={value}\n" for key, value in runtime.items()),
            encoding="utf-8",
        )
        env_file.chmod(0o600)
        validation = run_command("python3", str(root / "validate.py"), "--env-file", str(env_file))
        if validation.returncode:
            blockers.append("runtime_environment_validation_failed")
        render = run_command(
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "-f",
            str(root / "compose.yml"),
            "config",
            "--quiet",
        )
        if render.returncode:
            blockers.append("compose_render_failed")
    return blockers


def build_report(request_path: Path, report_path: Path) -> int:
    env = dict(os.environ)
    blockers: list[str] = []
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        request = {}
        blockers.append("request_unreadable")
    if request != EXPECTED_REQUEST:
        blockers.append("request_contract_mismatch")
    runner = {
        "name_matches": env.get("RUNNER_NAME_VALUE") == EXPECTED_REQUEST["expected_runner_name"],
        "os_is_linux": env.get("RUNNER_OS_VALUE") == "Linux",
        "arch": env.get("RUNNER_ARCH_VALUE", ""),
        "selected_custom_label": EXPECTED_REQUEST["expected_runner_label"],
        "environment": EXPECTED_REQUEST["expected_environment"],
    }
    if not runner["name_matches"]:
        blockers.append("runner_name_mismatch")
    if not runner["os_is_linux"]:
        blockers.append("runner_os_not_linux")
    missing_secrets, invalid_secrets = valid_secret_material(env)
    missing_public, invalid_public, dns = valid_public_configuration(env)
    blockers.extend(f"missing:{name}" for name in missing_secrets + missing_public)
    blockers.extend(f"invalid:{name}" for name in invalid_secrets + invalid_public)
    path_blockers, storage = check_paths(EXPECTED_REQUEST, env)
    docker_blockers, docker = check_docker(EXPECTED_REQUEST)
    blockers.extend(path_blockers + docker_blockers)
    required_tools = ("python3", "docker", "age", "openssl")
    missing_tools = sorted(name for name in required_tools if shutil.which(name) is None)
    blockers.extend(f"missing_tool:{name}" for name in missing_tools)
    if not missing_secrets and not invalid_secrets and not missing_tools:
        root = Path("deploy/synology/portal-authentik").resolve()
        blockers.extend(validate_runtime_render(root, env))
    unique_blockers = sorted(set(blockers))
    report = {
        "schema_version": 1,
        "report_id": EXPECTED_REQUEST["request_id"],
        "request_head": env.get("HEAD_SHA", ""),
        "runner": runner,
        "storage": storage,
        "docker": docker,
        "configuration": {
            "required_secret_names": sorted(SENSITIVE_ENV),
            "missing_secret_names": missing_secrets,
            "invalid_secret_names": invalid_secrets,
            "required_public_variable_names": sorted(PUBLIC_ENV),
            "missing_public_variable_names": missing_public,
            "invalid_public_variable_names": invalid_public,
            "dns": dns,
            "missing_tools": missing_tools,
        },
        "safety": {
            "secret_values_recorded": False,
            "container_changes_executed": False,
            "bootstrap_executed": False,
            "restore_executed": False,
            "bounded_storage_probe_removed": True,
            "live_capital_authorized": False,
        },
        "blockers": unique_blockers,
        "ready_for_controlled_deployment": not unique_blockers,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not unique_blockers else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    return build_report(args.request.resolve(), args.report.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
