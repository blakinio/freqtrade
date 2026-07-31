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
    if request != EXPECTED_REQUEST:
        missing = sorted(set(EXPECTED_REQUEST) - set(request))
        extra = sorted(set(request) - set(EXPECTED_REQUEST))
        mismatched = sorted(
            key
            for key in set(EXPECTED_REQUEST) & set(request)
            if request[key] != EXPECTED_REQUEST[key]
        )
        raise DeploymentError(
            "frozen request mismatch "
            f"(missing={missing}, extra={extra}, mismatched={mismatched})"
        )


def runtime_values(postgres_password: str, secret_key: str, *, port: int) -> dict[str, str]:
    return {
        "AUTHENTIK_IMAGE": AUTHENTIK_IMAGE,
        "POSTGRES_IMAGE": POSTGRES_IMAGE,
        "AUTHENTIK_POSTGRESQL__NAME": "authentik",
        "AUTHENTIK_POSTGRESQL__USER": "authentik",
        "AUTHENTIK_POSTGRESQL__PASSWORD": postgres_password,
        "AUTHENTIK_SECRET_KEY": secret_key,
        "AUTHENTIK_BIND_ADDRESS": "0.0.0.0",  # noqa: S104 - explicit LAN-only test request
        "AUTHENTIK_HTTP_PORT": str(port),
        "AUTHENTIK_BOOTSTRAP_PASSWORD_HASH": "",
    }


def parse_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise DeploymentError(f"runtime env line {number} is malformed")
        key, value = line.split("=", 1)
        if key in result:
            raise DeploymentError(f"runtime env contains duplicate key {key}")
        result[key] = value
    return result


def render_env(values: dict[str, str]) -> str:
    order = [
        "AUTHENTIK_IMAGE",
        "POSTGRES_IMAGE",
        "AUTHENTIK_POSTGRESQL__NAME",
        "AUTHENTIK_POSTGRESQL__USER",
        "AUTHENTIK_POSTGRESQL__PASSWORD",
        "AUTHENTIK_SECRET_KEY",
        "AUTHENTIK_BIND_ADDRESS",
        "AUTHENTIK_HTTP_PORT",
        "AUTHENTIK_BOOTSTRAP_PASSWORD_HASH",
    ]
    return "\n".join(f"{key}={values[key]}" for key in order) + "\n"


def create_runtime_env(path: Path, *, port: int) -> dict[str, str]:
    values = runtime_values(
        secrets.token_urlsafe(48),
        secrets.token_urlsafe(72),
        port=port,
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
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
    spec = importlib.util.spec_from_file_location(
        "authentik_deployment_validate",
        root / "validate.py",
    )
    if spec is None or spec.loader is None:
        raise DeploymentError("deployment validator could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_runtime(root: Path, values: dict[str, str], *, port: int) -> None:
    required = set(runtime_values("x" * 48, "y" * 64, port=port))
    if set(values) != required:
        raise DeploymentError("runtime env key set does not match the frozen contract")
    if values["AUTHENTIK_BIND_ADDRESS"] != "0.0.0.0":  # noqa: S104
        raise DeploymentError("local-test Authentik must publish on the Synology LAN listener")
    if values["AUTHENTIK_HTTP_PORT"] != str(port):
        raise DeploymentError("runtime env port does not match the frozen request")
    if values["AUTHENTIK_BOOTSTRAP_PASSWORD_HASH"]:
        raise DeploymentError("steady-state bootstrap material is forbidden")

    validator = load_validator(root)
    validator_values = dict(values)
    validator_values["AUTHENTIK_BIND_ADDRESS"] = "127.0.0.1"
    errors = validator.validate_environment(validator_values, example=False)
    errors.extend(validator.validate_compose((root / "compose.yml").read_text(encoding="utf-8")))
    if errors:
        raise DeploymentError(f"runtime contract validation failed ({len(errors)} error(s))")


def run_command(command: list[str], *, label: str) -> str:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise DeploymentError(f"{label} failed with exit code {completed.returncode}")
    return completed.stdout.strip()


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


def project_resources_present(compose: list[str]) -> bool:
    output = run_command([*compose, "ps", "-aq"], label="inspect existing project")
    return bool(output.strip())


def other_container_uses_port(port: int) -> str | None:
    output = run_command(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"],
        label="inspect Docker port usage",
    )
    needle = f":{port}->"
    for line in output.splitlines():
        if needle not in line:
            continue
        name = line.split("\t", 1)[0]
        if not name.startswith(f"{PROJECT_NAME}-"):
            return name
    return None


def inspect_container(container_id: str) -> dict[str, Any]:
    output = run_command(["docker", "inspect", container_id], label="inspect deployed container")
    payload = json.loads(output)
    if not isinstance(payload, list) or len(payload) != 1:
        raise DeploymentError("Docker inspect returned an unexpected payload")
    return payload[0]


def wait_for_healthy(
    compose: list[str], *, timeout_seconds: int = 600
) -> dict[str, dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    services = ("postgresql", "server", "worker")
    last_states: dict[str, str] = {}
    while time.monotonic() < deadline:
        inspected: dict[str, dict[str, Any]] = {}
        all_healthy = True
        for service in services:
            container_id = run_command(
                [*compose, "ps", "-q", service],
                label=f"locate {service} container",
            )
            if not container_id:
                all_healthy = False
                last_states[service] = "missing"
                continue
            details = inspect_container(container_id)
            inspected[service] = details
            state = details.get("State", {})
            health = state.get("Health", {}).get("Status", state.get("Status", "unknown"))
            last_states[service] = str(health)
            if health != "healthy":
                all_healthy = False
        if all_healthy and len(inspected) == len(services):
            return inspected
        time.sleep(5)
    raise DeploymentError(f"containers did not become healthy: {last_states}")


def verify_container_controls(
    inspected: dict[str, dict[str, Any]],
    *,
    port: int,
) -> dict[str, Any]:
    for service, details in inspected.items():
        host_config = details.get("HostConfig", {})
        if host_config.get("Privileged"):
            raise DeploymentError(f"{service} unexpectedly runs privileged")
        if host_config.get("NetworkMode") == "host":
            raise DeploymentError(f"{service} unexpectedly uses host networking")
        for mount in details.get("Mounts", []):
            if mount.get("Source") == "/var/run/docker.sock":
                raise DeploymentError(f"{service} unexpectedly mounts the Docker socket")

    postgres_ports = inspected["postgresql"].get("NetworkSettings", {}).get("Ports", {})
    if any(bindings for bindings in postgres_ports.values()):
        raise DeploymentError("PostgreSQL unexpectedly publishes a host port")

    server_ports = inspected["server"].get("NetworkSettings", {}).get("Ports", {})
    bindings = server_ports.get("9000/tcp") or []
    if not any(
        binding.get("HostPort") == str(port)
        and binding.get("HostIp") in {"0.0.0.0", "::"}
        for binding in bindings
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


def safe_container_summary(details: dict[str, Any]) -> dict[str, Any]:
    state = details.get("State", {})
    config = details.get("Config", {})
    return {
        "name": str(details.get("Name", "")).lstrip("/"),
        "image": config.get("Image", ""),
        "state": state.get("Status", "unknown"),
        "health": state.get("Health", {}).get("Status", "unknown"),
        "restart_policy": details.get("HostConfig", {}).get("RestartPolicy", {}).get("Name", ""),
    }


def path_fingerprint(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16]


def deploy(root: Path, request: dict[str, Any], report_path: Path) -> dict[str, Any]:
    validate_request(request)
    port = int(request["authentik_http_port"])
    state_root = Path(os.environ.get("FREQTRADE_STAGING_STATE_DIR", str(DEFAULT_STATE_ROOT)))
    state_root = state_root.resolve()
    if not state_root.is_absolute() or not state_root.is_dir():
        raise DeploymentError("staging state root is unavailable")
    if not os.access(state_root, os.W_OK):
        raise DeploymentError("staging state root is not writable")

    state_dir = (state_root / STATE_SUBDIRECTORY).resolve()
    if state_dir.parent != state_root:
        raise DeploymentError("state directory escaped the staging root")
    state_dir.mkdir(mode=0o700, exist_ok=True)
    os.chmod(state_dir, 0o700)
    env_file = state_dir / "runtime.env"
    compose = compose_command(root, env_file)

    existing_project = False
    if env_file.exists():
        os.chmod(env_file, 0o600)
        values = parse_env(env_file)
        secrets_generated = False
        existing_project = project_resources_present(compose)
    else:
        orphan_names = [
            "portal_authentik_postgresql_data",
            "portal_authentik_media",
            "portal_authentik_templates",
        ]
        for volume in orphan_names:
            result = subprocess.run(
                ["docker", "volume", "inspect", volume],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                raise DeploymentError(
                    "Authentik persistent resources exist without the protected runtime env"
                )
        values = create_runtime_env(env_file, port=port)
        secrets_generated = True

    validate_runtime(root, values, port=port)
    conflict = other_container_uses_port(port)
    if conflict:
        raise DeploymentError(f"TCP port {port} is already published by container {conflict}")

    run_command([*compose, "config", "--quiet"], label="render Authentik Compose")
    run_command([*compose, "pull"], label="pull pinned Authentik images")
    run_command(
        [*compose, "up", "-d", "postgresql", "server", "worker"],
        label="start local-test Authentik stack",
    )
    inspected = wait_for_healthy(compose)
    run_command(
        [*compose, "exec", "-T", "server", "ak", "healthcheck"],
        label="server healthcheck",
    )
    run_command(
        [*compose, "exec", "-T", "worker", "ak", "healthcheck"],
        label="worker healthcheck",
    )
    controls = verify_container_controls(inspected, port=port)

    report = {
        "schema_version": 1,
        "request_id": request["request_id"],
        "classification": "LOCAL_TEST_DEPLOYMENT",
        "target_environment": request["target_environment"],
        "project_name": PROJECT_NAME,
        "deployment_action": "updated" if existing_project else "created",
        "containers": {
            service: safe_container_summary(details)
            for service, details in sorted(inspected.items())
        },
        "controls": controls,
        "state": {
            "runtime_env_present": True,
            "runtime_env_mode": "0600",
            "state_directory_fingerprint": path_fingerprint(state_dir),
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
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
    )
    args = parser.parse_args()

    try:
        request = load_json(args.request.resolve())
        report = deploy(args.root.resolve(), request, args.report.resolve())
    except DeploymentError as exc:
        print(f"local-test Authentik deployment blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
