#!/usr/bin/env python3
"""Deploy a bounded local-test Authentik stack on the trusted Synology runner."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


AUTHENTIK_IMAGE = (
    "docker.io/authentik/server:2026.5.5@sha256:"
    "50a833c48a714709f15d4f8846ec6b81a41d0d6a6bd2975087dfed3000d0d72e"
)
POSTGRES_IMAGE = (
    "docker.io/library/postgres:16.13-alpine3.23@sha256:"
    "57c72fd2a128e416c7fcc499958864df5301e940bca0a56f58fddf30ffc07777"
)
PROJECT_NAME = "portal-authentik-local-test"
STATE_SUBDIRECTORY = "portal-authentik-local-test"
REQUEST_ID = "portal-authentik-local-test-deploy-20260731-v1"
CONFIRMATION = "DEPLOY_LOCAL_TEST_AUTHENTIK_ON_SYNOLOGY"
DEFAULT_STATE_ROOT = Path("/var/lib/freqtrade-staging-state")
DEFAULT_PORT = 9000
ALL_INTERFACE_ADDRESSES = {"0.0.0.0", "::"}  # noqa: S104 - Docker bind states
EXPECTED_REQUEST: dict[str, Any] = {
    "schema_version": 1,
    "request_id": REQUEST_ID,
    "target_environment": "synology-staging",
    "runner_label": "freqtrade-staging",
    "deployment_mode": "local_test",
    "state_subdirectory": STATE_SUBDIRECTORY,
    "authentik_http_port": DEFAULT_PORT,
    "publish_scope": "private_lan",
    "initialize_via_gui": True,
    "mutation_authorized": True,
    "bootstrap_hash_authorized": False,
    "restore_authorized": False,
    "trading_credentials_authorized": False,
    "live_capital_authorized": False,
    "confirmation": CONFIRMATION,
}
ENV_ORDER = (
    "AUTHENTIK_IMAGE",
    "POSTGRES_IMAGE",
    "AUTHENTIK_POSTGRESQL__NAME",
    "AUTHENTIK_POSTGRESQL__USER",
    "AUTHENTIK_POSTGRESQL__PASSWORD",
    "AUTHENTIK_SECRET_KEY",
    "AUTHENTIK_BIND_ADDRESS",
    "AUTHENTIK_HTTP_PORT",
    "AUTHENTIK_BOOTSTRAP_PASSWORD_HASH",
)


class DeploymentError(RuntimeError):
    """A sanitized deployment failure safe to emit to workflow logs."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeploymentError(f"request could not be read: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise DeploymentError("request root must be an object")
    return value


def validate_request(request: dict[str, Any]) -> None:
    if request == EXPECTED_REQUEST:
        return
    missing = sorted(set(EXPECTED_REQUEST) - set(request))
    extra = sorted(set(request) - set(EXPECTED_REQUEST))
    mismatched = sorted(
        key for key in set(EXPECTED_REQUEST) & set(request) if request[key] != EXPECTED_REQUEST[key]
    )
    raise DeploymentError(
        f"frozen request mismatch (missing={missing}, extra={extra}, mismatched={mismatched})"
    )


def runtime_values(postgres_password: str, secret_key: str, *, port: int) -> dict[str, str]:
    return {
        "AUTHENTIK_IMAGE": AUTHENTIK_IMAGE,
        "POSTGRES_IMAGE": POSTGRES_IMAGE,
        "AUTHENTIK_POSTGRESQL__NAME": "authentik",
        "AUTHENTIK_POSTGRESQL__USER": "authentik",
        "AUTHENTIK_POSTGRESQL__PASSWORD": postgres_password,
        "AUTHENTIK_SECRET_KEY": secret_key,
        "AUTHENTIK_BIND_ADDRESS": "0.0.0.0",  # noqa: S104 - LAN-only test request
        "AUTHENTIK_HTTP_PORT": str(port),
        "AUTHENTIK_BOOTSTRAP_PASSWORD_HASH": "",
    }


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise DeploymentError(f"runtime env line {number} is malformed")
        key, value = line.split("=", 1)
        if key in values:
            raise DeploymentError(f"runtime env contains duplicate key {key}")
        values[key] = value
    return values


def render_env(values: dict[str, str]) -> str:
    return "\n".join(f"{key}={values[key]}" for key in ENV_ORDER) + "\n"


def create_runtime_env(path: Path, *, port: int) -> dict[str, str]:
    values = runtime_values(secrets.token_urlsafe(48), secrets.token_urlsafe(72), port=port)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(render_env(values))
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return values


def load_validator(root: Path) -> Any:
    spec = importlib.util.spec_from_file_location("authentik_validator", root / "validate.py")
    if spec is None or spec.loader is None:
        raise DeploymentError("deployment validator could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_runtime(root: Path, values: dict[str, str], *, port: int) -> None:
    if set(values) != set(ENV_ORDER):
        raise DeploymentError("runtime env key set does not match the frozen contract")
    if values["AUTHENTIK_BIND_ADDRESS"] != "0.0.0.0":  # noqa: S104
        raise DeploymentError("local-test Authentik must publish on the Synology LAN listener")
    if values["AUTHENTIK_HTTP_PORT"] != str(port):
        raise DeploymentError("runtime env port does not match the frozen request")
    if values["AUTHENTIK_BOOTSTRAP_PASSWORD_HASH"]:
        raise DeploymentError("steady-state bootstrap material is forbidden")

    validator = load_validator(root)
    safe_values = dict(values)
    safe_values["AUTHENTIK_BIND_ADDRESS"] = "127.0.0.1"
    errors = validator.validate_environment(safe_values, example=False)
    errors += validator.validate_compose((root / "compose.yml").read_text(encoding="utf-8"))
    if errors:
        raise DeploymentError(f"runtime contract validation failed ({len(errors)} error(s))")


def run_command(command: list[str], *, label: str) -> str:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise DeploymentError(f"{label} failed with exit code {result.returncode}")
    return result.stdout.strip()


def compose_command(root: Path, env_file: Path) -> list[str]:
    return [
        "docker",
        "compose",
        "--project-name",
        PROJECT_NAME,
        "--env-file",
        str(env_file),
        "-f",
        str(root / "compose.yml"),
    ]


def other_container_uses_port(port: int) -> str | None:
    output = run_command(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"],
        label="inspect Docker port usage",
    )
    for line in output.splitlines():
        if f":{port}->" in line:
            name = line.split("\t", 1)[0]
            if not name.startswith(f"{PROJECT_NAME}-"):
                return name
    return None


def inspect_service(compose: list[str], service: str) -> dict[str, Any]:
    container_id = run_command([*compose, "ps", "-q", service], label=f"locate {service}")
    if not container_id:
        raise DeploymentError(f"{service} container is missing")
    payload = json.loads(
        run_command(["docker", "inspect", container_id], label=f"inspect {service}")
    )
    if not isinstance(payload, list) or len(payload) != 1:
        raise DeploymentError(f"unexpected Docker inspect payload for {service}")
    return payload[0]


def wait_for_healthy(
    compose: list[str], *, timeout_seconds: int = 600
) -> dict[str, dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    services = ("postgresql", "server", "worker")
    last_states: dict[str, str] = {}
    while time.monotonic() < deadline:
        inspected: dict[str, dict[str, Any]] = {}
        for service in services:
            try:
                details = inspect_service(compose, service)
            except DeploymentError:
                last_states[service] = "missing"
                break
            inspected[service] = details
            state = details.get("State", {})
            last_states[service] = state.get("Health", {}).get(
                "Status", state.get("Status", "unknown")
            )
        if len(inspected) == len(services) and set(last_states.values()) == {"healthy"}:
            return inspected
        time.sleep(5)
    raise DeploymentError(f"containers did not become healthy: {last_states}")


def verify_controls(inspected: dict[str, dict[str, Any]], *, port: int) -> dict[str, Any]:
    for service, details in inspected.items():
        host = details.get("HostConfig", {})
        if host.get("Privileged") or host.get("NetworkMode") == "host":
            raise DeploymentError(f"unsafe container controls detected for {service}")
        if any(
            mount.get("Source") == "/var/run/docker.sock" for mount in details.get("Mounts", [])
        ):
            raise DeploymentError(f"{service} unexpectedly mounts the Docker socket")

    postgres_ports = inspected["postgresql"].get("NetworkSettings", {}).get("Ports", {})
    if any(postgres_ports.values()):
        raise DeploymentError("PostgreSQL unexpectedly publishes a host port")
    server_ports = inspected["server"].get("NetworkSettings", {}).get("Ports", {})
    bindings = server_ports.get("9000/tcp") or []
    if not any(
        item.get("HostPort") == str(port) and item.get("HostIp") in ALL_INTERFACE_ADDRESSES
        for item in bindings
    ):
        raise DeploymentError("Authentik LAN port mapping does not match the frozen request")
    return {
        "postgresql_host_port_published": False,
        "authentik_host_port": port,
        "authentik_bind_scope": "private_lan",
        "privileged_containers": False,
        "host_network_containers": False,
        "docker_socket_mounted": False,
    }


def container_summary(details: dict[str, Any]) -> dict[str, Any]:
    state = details.get("State", {})
    return {
        "name": str(details.get("Name", "")).lstrip("/"),
        "image": details.get("Config", {}).get("Image", ""),
        "state": state.get("Status", "unknown"),
        "health": state.get("Health", {}).get("Status", "unknown"),
        "restart_policy": details.get("HostConfig", {}).get("RestartPolicy", {}).get("Name", ""),
    }


def deploy(root: Path, request: dict[str, Any], report_path: Path) -> dict[str, Any]:
    validate_request(request)
    port = int(request["authentik_http_port"])
    state_root = Path(
        os.environ.get("FREQTRADE_STAGING_STATE_DIR", str(DEFAULT_STATE_ROOT))
    ).resolve()
    if not state_root.is_dir() or not os.access(state_root, os.W_OK):
        raise DeploymentError("staging state root is unavailable or not writable")
    state_dir = (state_root / STATE_SUBDIRECTORY).resolve()
    if state_dir.parent != state_root:
        raise DeploymentError("state directory escaped the staging root")
    state_dir.mkdir(mode=0o700, exist_ok=True)
    state_dir.chmod(0o700)
    env_file = state_dir / "runtime.env"
    compose = compose_command(root, env_file)

    existing_project = False
    if env_file.exists():
        env_file.chmod(0o600)
        values = parse_env(env_file)
        secrets_generated = False
        existing_project = bool(run_command([*compose, "ps", "-aq"], label="inspect project"))
    else:
        for volume in (
            "portal_authentik_postgresql_data",
            "portal_authentik_media",
            "portal_authentik_templates",
        ):
            result = subprocess.run(
                ["docker", "volume", "inspect", volume],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                raise DeploymentError(
                    "persistent resources exist without the protected runtime env"
                )
        values = create_runtime_env(env_file, port=port)
        secrets_generated = True

    validate_runtime(root, values, port=port)
    if conflict := other_container_uses_port(port):
        raise DeploymentError(f"TCP port {port} is already published by container {conflict}")
    run_command([*compose, "config", "--quiet"], label="render Authentik Compose")
    run_command([*compose, "pull"], label="pull pinned Authentik images")
    run_command(
        [*compose, "up", "-d", "postgresql", "server", "worker"],
        label="start local-test Authentik stack",
    )
    inspected = wait_for_healthy(compose)
    for service in ("server", "worker"):
        run_command(
            [*compose, "exec", "-T", service, "ak", "healthcheck"],
            label=f"{service} healthcheck",
        )

    report = {
        "schema_version": 1,
        "request_id": request["request_id"],
        "classification": "LOCAL_TEST_DEPLOYMENT",
        "target_environment": request["target_environment"],
        "project_name": PROJECT_NAME,
        "deployment_action": "updated" if existing_project else "created",
        "containers": {
            service: container_summary(details) for service, details in sorted(inspected.items())
        },
        "controls": verify_controls(inspected, port=port),
        "state": {
            "runtime_env_present": True,
            "runtime_env_mode": "0600",
            "state_directory_fingerprint": hashlib.sha256(
                str(state_dir).encode("utf-8")
            ).hexdigest()[:16],
            "secrets_generated_on_target": secrets_generated,
            "secret_values_recorded": False,
        },
        "initial_setup": {
            "required": True,
            "admin_user": "akadmin",
            "path": "/if/flow/initial-setup/",
            "lan_url_template": f"http://<SYNOLOGY_LAN_IP>:{port}/if/flow/initial-setup/",
            "password_transmitted_through_github": False,
            "mfa_owner_action_required": True,
        },
        "safety": {
            "mutation_executed": True,
            "restore_executed": False,
            "bootstrap_hash_used": False,
            "trading_credentials_authorized": False,
            "live_capital_authorized": False,
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    try:
        report = deploy(
            args.root.resolve(),
            load_json(args.request.resolve()),
            args.report.resolve(),
        )
    except DeploymentError as exc:
        print(f"local-test Authentik deployment blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
