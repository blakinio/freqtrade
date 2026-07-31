#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REQUEST_RELATIVE_PATH = (
    "deploy/synology/portal-oidc/run-requests/local-oidc-20260731-v1.json"
)
REQUEST_ID = "portal-local-authentik-oidc-20260731-v1"
AUTHENTIK_PROJECT = "portal-authentik-local-test"
AUTHENTIK_STATE_DIR = Path("/var/lib/freqtrade-staging-state/portal-authentik-local-test")
PORTAL_STATE_DIR = Path("/var/lib/freqtrade-staging-state/portal-oidc-local-test")
PORTAL_RUNTIME_ENV = PORTAL_STATE_DIR / "runtime.env"
PORTAL_DATA_DIR = PORTAL_STATE_DIR / "data"
PORTAL_NETWORK = "portal_oidc_local_test"
PORTAL_CONTAINER = "freqtrade-portal-staging"
CONTROL_CONTAINER = "freqtrade-portal-control-plane"
PORTAL_BIND_ADDRESS = "192.168.1.2"
PORTAL_PORT = 3031
AUTHENTIK_ORIGIN = "http://192.168.1.2:9000"
AUTHENTIK_SLUG = "freqtrade-portal-local"
ISSUER = f"{AUTHENTIK_ORIGIN}/application/o/{AUTHENTIK_SLUG}/"
REDIRECT_URI = f"http://{PORTAL_BIND_ADDRESS}:{PORTAL_PORT}/api/identity/callback"
CLIENT_ID = "freqtrade-portal-local"
BLUEPRINT_NAME = "freqtrade-portal-local.yaml"


class DeploymentError(RuntimeError):
    pass


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    sensitive: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        if sensitive:
            raise DeploymentError(f"sensitive command failed: {command[0]} {command[1]}")
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ["no output"]
        raise DeploymentError(f"command failed ({result.returncode}): {' '.join(command)}: {detail[0]}")
    return result


def _load_request(path: Path, expected_sha: str) -> dict[str, Any]:
    if path.as_posix().endswith(REQUEST_RELATIVE_PATH) is False:
        raise DeploymentError("request path does not match the frozen deployment request path")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "request_id": REQUEST_ID,
        "environment": "synology-staging",
        "runner": "freqtrade-staging",
        "implementation_sha": expected_sha,
        "authentik_origin": AUTHENTIK_ORIGIN,
        "portal_origin": f"http://{PORTAL_BIND_ADDRESS}:{PORTAL_PORT}",
        "identity_transport": "local_http_test",
        "identity_fixture_mode": "disabled",
        "dry_run_required": True,
        "public_ingress_authorized": False,
        "live_capital_authorized": False,
        "restore_authorized": False,
        "secret_values_in_request": False,
    }
    if payload != expected:
        raise DeploymentError("deployment request bytes do not match the frozen contract")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise DeploymentError("implementation SHA must be a full lowercase commit SHA")
    return payload


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _assert_secret_file(path: Path) -> None:
    if not path.is_file() or _mode(path) != 0o600:
        raise DeploymentError(f"protected runtime file must exist with mode 0600: {path}")


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        name, separator, value = raw.partition("=")
        if not separator or not name:
            raise DeploymentError(f"invalid runtime env entry in {path}")
        values[name] = value
    return values


def _write_env_atomic(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".runtime.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for name in sorted(values):
                value = values[name]
                if "\n" in value or "\r" in value:
                    raise DeploymentError(f"runtime env value contains a newline: {name}")
                handle.write(f"{name}={value}\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    _assert_secret_file(path)


def _compose_command(repo: Path) -> list[str]:
    runtime_env = AUTHENTIK_STATE_DIR / "runtime.env"
    _assert_secret_file(runtime_env)
    return [
        "docker",
        "compose",
        "--project-name",
        AUTHENTIK_PROJECT,
        "--env-file",
        str(runtime_env),
        "-f",
        str(repo / "deploy/synology/portal-authentik/compose.yml"),
    ]


def _copy_and_apply_blueprint(repo: Path) -> tuple[str, str]:
    source = repo / "deploy/synology/portal-oidc/blueprints" / BLUEPRINT_NAME
    if not source.is_file():
        raise DeploymentError("Authen­tik blueprint is missing")
    durable_dir = AUTHENTIK_STATE_DIR / "blueprints"
    durable_dir.mkdir(parents=True, exist_ok=True)
    durable = durable_dir / BLUEPRINT_NAME
    temporary = durable.with_suffix(".tmp")
    shutil.copyfile(source, temporary)
    os.chmod(temporary, 0o644)
    os.replace(temporary, durable)

    compose = _compose_command(repo)
    worker = _run([*compose, "ps", "-q", "worker"]).stdout.strip()
    server = _run([*compose, "ps", "-q", "server"]).stdout.strip()
    if not worker or not server:
        raise DeploymentError("Authen­tik server or worker container is unavailable")
    _run(["docker", "exec", "-u", "0", worker, "mkdir", "-p", "/blueprints/custom"])
    _run(["docker", "cp", str(durable), f"{worker}:/blueprints/custom/{BLUEPRINT_NAME}"])
    _run(
        ["docker", "exec", worker, "ak", "apply_blueprint", f"/blueprints/custom/{BLUEPRINT_NAME}"],
        sensitive=True,
    )
    return server, worker


def _authentik_metadata(server: str) -> dict[str, str]:
    script = """
import json
from authentik.core.models import Application, User
from authentik.providers.oauth2.models import OAuth2Provider
provider = OAuth2Provider.objects.get(name='Freqtrade Portal Local OIDC')
application = Application.objects.get(slug='freqtrade-portal-local')
user = User.objects.get(username='akadmin')
subject = provider.get_subject(user)
print('__PORTAL_JSON__' + json.dumps({
    'application_pk': str(application.pk),
    'provider_pk': str(provider.pk),
    'client_id': str(provider.client_id),
    'client_secret': str(provider.client_secret),
    'subject': str(subject),
}, sort_keys=True))
""".strip()
    result = _run(
        ["docker", "exec", server, "ak", "shell", "-c", script],
        sensitive=True,
    )
    marker = next(
        (line.removeprefix("__PORTAL_JSON__") for line in result.stdout.splitlines() if line.startswith("__PORTAL_JSON__")),
        None,
    )
    if marker is None:
        raise DeploymentError("Authen­tik metadata query did not return the expected marker")
    payload = json.loads(marker)
    required = {"application_pk", "provider_pk", "client_id", "client_secret", "subject"}
    if set(payload) != required or not all(isinstance(payload[key], str) and payload[key] for key in required):
        raise DeploymentError("Authen­tik metadata query returned an invalid shape")
    if payload["client_id"] != CLIENT_ID:
        raise DeploymentError("Authen­tik provider client ID differs from the frozen contract")
    return payload


def _secret_b64() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")


def _prepare_portal_runtime(metadata: dict[str, str]) -> dict[str, str]:
    existing = _read_env(PORTAL_RUNTIME_ENV)
    if existing and existing.get("PORTAL_IDENTITY_CLIENT_SECRET") != metadata["client_secret"]:
        raise DeploymentError("stored Portal client secret differs from Authen­tik; refusing rotation")
    values = {
        "PORTAL_DATABASE_URL": "sqlite+pysqlite:////state/portal.db",
        "PORTAL_ENVIRONMENT": "test",
        "PORTAL_IDENTITY_BOOTSTRAP_DISPLAY_NAME": "akadmin",
        "PORTAL_IDENTITY_BOOTSTRAP_SUBJECT": metadata["subject"],
        "PORTAL_IDENTITY_BOOTSTRAP_TENANT_ID": "tenant-local",
        "PORTAL_IDENTITY_CLIENT_ID": CLIENT_ID,
        "PORTAL_IDENTITY_CLIENT_SECRET": metadata["client_secret"],
        "PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64": existing.get(
            "PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64", _secret_b64()
        ),
        "PORTAL_IDENTITY_ISSUER": ISSUER,
        "PORTAL_IDENTITY_REDIRECT_URI": REDIRECT_URI,
        "PORTAL_IDENTITY_SESSION_HMAC_KEY_B64": existing.get(
            "PORTAL_IDENTITY_SESSION_HMAC_KEY_B64", _secret_b64()
        ),
        "PORTAL_IDENTITY_TRANSPORT_MODE": "local_http_test",
    }
    _write_env_atomic(PORTAL_RUNTIME_ENV, values)
    PORTAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return values


def _docker_image_id(image: str) -> str:
    return _run(["docker", "image", "inspect", "--format", "{{.Id}}", image]).stdout.strip()


def _build_images(repo: Path, implementation_sha: str) -> tuple[str, str, str, str]:
    suffix = implementation_sha[:12]
    control_image = f"local/freqtrade-portal-control-plane:{suffix}"
    web_image = f"local/freqtrade-portal-web:{suffix}"
    _run(
        [
            "docker",
            "build",
            "--pull=false",
            "--label",
            f"org.opencontainers.image.revision={implementation_sha}",
            "--file",
            str(repo / "deploy/synology/portal-oidc/Dockerfile.control-plane"),
            "--tag",
            control_image,
            str(repo),
        ],
        cwd=repo,
    )
    web_root = repo / "ai_platform/portal/web"
    _run(
        [
            "docker",
            "build",
            "--pull=false",
            "--label",
            f"org.opencontainers.image.revision={implementation_sha}",
            "--file",
            str(repo / "deploy/synology/portal/Dockerfile"),
            "--tag",
            web_image,
            str(web_root),
        ],
        cwd=repo,
    )
    return control_image, _docker_image_id(control_image), web_image, _docker_image_id(web_image)


def _ensure_network() -> None:
    if _run(["docker", "network", "inspect", PORTAL_NETWORK], check=False).returncode != 0:
        _run(["docker", "network", "create", "--driver", "bridge", PORTAL_NETWORK])


def _container_exists(name: str) -> bool:
    return _run(["docker", "container", "inspect", name], check=False).returncode == 0


def _remove_container(name: str) -> None:
    if _container_exists(name):
        _run(["docker", "rm", "-f", name])


def _wait_healthy(name: str, timeout_seconds: int = 120) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        status_value = _run(
            [
                "docker",
                "inspect",
                "--format",
                "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
                name,
            ],
            check=False,
        ).stdout.strip()
        if status_value == "healthy":
            return
        if status_value in {"exited", "dead", "unhealthy"}:
            raise DeploymentError(f"container {name} entered state {status_value}")
        time.sleep(2)
    raise DeploymentError(f"container {name} did not become healthy")


def _start_control_candidate(image: str, suffix: str) -> str:
    candidate = f"{CONTROL_CONTAINER}-candidate-{suffix}"
    _remove_container(candidate)
    uid = str(os.getuid())
    gid = str(os.getgid())
    _run(
        [
            "docker",
            "run",
            "--detach",
            "--name",
            candidate,
            "--restart",
            "unless-stopped",
            "--network",
            PORTAL_NETWORK,
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=64m",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            "256",
            "--memory",
            "768m",
            "--user",
            f"{uid}:{gid}",
            "--env-file",
            str(PORTAL_RUNTIME_ENV),
            "--mount",
            f"type=bind,src={PORTAL_DATA_DIR},dst=/state,rw",
            "--label",
            "ai.freqtrade.identity-fixture=disabled",
            "--label",
            "ai.freqtrade.live-capital-authorized=false",
            image,
        ]
    )
    _wait_healthy(candidate)
    return candidate


def _promote_control(candidate: str) -> str | None:
    backup = None
    if _container_exists(CONTROL_CONTAINER):
        backup = f"{CONTROL_CONTAINER}-backup-{int(time.time())}"
        _run(["docker", "stop", CONTROL_CONTAINER])
        _run(["docker", "rename", CONTROL_CONTAINER, backup])
    try:
        _run(["docker", "rename", candidate, CONTROL_CONTAINER])
        _run(["docker", "network", "disconnect", PORTAL_NETWORK, CONTROL_CONTAINER])
        _run(
            [
                "docker",
                "network",
                "connect",
                "--alias",
                CONTROL_CONTAINER,
                PORTAL_NETWORK,
                CONTROL_CONTAINER,
            ]
        )
        _run(["docker", "start", CONTROL_CONTAINER])
        _wait_healthy(CONTROL_CONTAINER)
    except Exception:
        _remove_container(CONTROL_CONTAINER)
        if backup:
            _run(["docker", "rename", backup, CONTROL_CONTAINER])
            _run(["docker", "start", CONTROL_CONTAINER])
        raise
    return backup


def _web_run_args(image: str, name: str, *, publish: bool) -> list[str]:
    liquid_root = Path("/volume1/docker/freqtrade-staging/liquid20-market-data")
    if not liquid_root.is_dir():
        raise DeploymentError("canonical Liquid20 mount is unavailable")
    liquid_gid = str(liquid_root.stat().st_gid)
    args = [
        "docker",
        "run",
        "--detach",
        "--name",
        name,
        "--restart",
        "unless-stopped",
        "--network",
        PORTAL_NETWORK,
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=64m",
        "--tmpfs",
        "/app/.next/cache:rw,noexec,nosuid,nodev,size=96m,uid=1000,gid=1000",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        "256",
        "--memory",
        "768m",
        "--group-add",
        liquid_gid,
        "--mount",
        f"type=bind,src={liquid_root},dst=/runtime-data/liquid20,readonly",
        "--env",
        "PORTAL_WEB_DATA_MODE=fixture",
        "--env",
        "PORTAL_ENVIRONMENT=test",
        "--env",
        "PORTAL_IDENTITY_FIXTURE_MODE=disabled",
        "--env",
        "PORTAL_IDENTITY_TRANSPORT_MODE=local_http_test",
        "--env",
        f"PORTAL_IDENTITY_ISSUER={ISSUER}",
        "--env",
        f"PORTAL_CONTROL_PLANE_URL=http://{CONTROL_CONTAINER}:8000",
        "--env",
        "PORTAL_LIQUID20_DATA_ROOT=/runtime-data/liquid20",
        "--label",
        "ai.freqtrade.identity-fixture=disabled",
        "--label",
        "ai.freqtrade.live-capital-authorized=false",
    ]
    if publish:
        args.extend(["--publish", f"{PORTAL_BIND_ADDRESS}:{PORTAL_PORT}:3000"])
    args.append(image)
    return args


def _probe_web_login(container: str) -> str:
    script = (
        "fetch('http://127.0.0.1:3000/api/identity/login?return_to=%2F',"
        "{redirect:'manual'}).then(async r=>{console.log(JSON.stringify({status:r.status,"
        "location:r.headers.get('location')}));if(r.status<300||r.status>=400)process.exit(2)})"
        ".catch(e=>{console.error(String(e));process.exit(3)})"
    )
    result = _run(["docker", "exec", container, "node", "-e", script])
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    location = payload.get("location")
    if not isinstance(location, str) or not location.startswith(f"{AUTHENTIK_ORIGIN}/"):
        raise DeploymentError("Portal login did not redirect to local Authen­tik")
    return location


def _deploy_web(image: str, suffix: str) -> tuple[str | None, str]:
    candidate = f"{PORTAL_CONTAINER}-candidate-{suffix}"
    _remove_container(candidate)
    _run(_web_run_args(image, candidate, publish=False))
    _wait_healthy(candidate)
    authorization_url = _probe_web_login(candidate)
    _remove_container(candidate)

    backup = None
    if _container_exists(PORTAL_CONTAINER):
        backup = f"{PORTAL_CONTAINER}-backup-{int(time.time())}"
        _run(["docker", "stop", PORTAL_CONTAINER])
        _run(["docker", "rename", PORTAL_CONTAINER, backup])
    try:
        _run(_web_run_args(image, PORTAL_CONTAINER, publish=True))
        _wait_healthy(PORTAL_CONTAINER)
        _probe_web_login(PORTAL_CONTAINER)
    except Exception:
        _remove_container(PORTAL_CONTAINER)
        if backup:
            _run(["docker", "rename", backup, PORTAL_CONTAINER])
            _run(["docker", "start", PORTAL_CONTAINER])
        raise
    return backup, authorization_url


def _http_status(url: str, *, accepted: set[int]) -> int:
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status_code = response.status
    except urllib.error.HTTPError as exc:
        status_code = exc.code
    if status_code not in accepted:
        raise DeploymentError(f"unexpected endpoint status {status_code}: {url}")
    return status_code


def _discovery() -> tuple[dict[str, Any], dict[str, int]]:
    url = f"{ISSUER.rstrip('/')}/.well-known/openid-configuration"
    with urllib.request.urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
        discovery_status = response.status
    if payload.get("issuer") != ISSUER:
        raise DeploymentError("Authen­tik discovery issuer differs from the Portal issuer")
    endpoint_statuses = {"discovery": discovery_status}
    for key, accepted in {
        "authorization_endpoint": {200, 302, 400},
        "token_endpoint": {400, 401, 405},
        "jwks_uri": {200},
    }.items():
        endpoint = payload.get(key)
        if not isinstance(endpoint, str) or not endpoint.startswith(AUTHENTIK_ORIGIN):
            raise DeploymentError(f"discovery endpoint is invalid: {key}")
        endpoint_statuses[key] = _http_status(endpoint, accepted=accepted)
    return payload, endpoint_statuses


def _container_status(name: str) -> dict[str, str]:
    result = _run(
        [
            "docker",
            "inspect",
            "--format",
            "{{.Name}}|{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}|{{.Config.Image}}",
            name,
        ]
    ).stdout.strip()
    container_name, state_value, health, image = result.split("|", 3)
    return {
        "name": container_name.removeprefix("/"),
        "state": state_value,
        "health": health,
        "image": image,
    }


def _authentik_statuses(repo: Path) -> list[dict[str, str]]:
    compose = _compose_command(repo)
    statuses: list[dict[str, str]] = []
    for service in ("postgresql", "server", "worker"):
        container = _run([*compose, "ps", "-q", service]).stdout.strip()
        if not container:
            raise DeploymentError(f"Authen­tik service is missing: {service}")
        status_payload = _container_status(container)
        status_payload["service"] = service
        if status_payload["health"] != "healthy":
            raise DeploymentError(f"Authen­tik service is not healthy: {service}")
        statuses.append(status_payload)
    return statuses


def _write_report(path: Path, report: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def deploy(args: argparse.Namespace) -> int:
    repo = Path(args.repository).resolve()
    request_path = Path(args.request).resolve()
    report_path = Path(args.report).resolve()
    report: dict[str, Any] = {
        "schema_version": 1,
        "request_id": REQUEST_ID,
        "implementation_sha": args.expected_repository_sha,
        "status": "failed",
        "secret_values_recorded": False,
        "live_capital_authorized": False,
        "public_ingress_authorized": False,
        "restore_authorized": False,
        "identity_fixture_disabled": False,
        "browser_acceptance": "not_executed",
    }
    control_backup: str | None = None
    web_backup: str | None = None
    try:
        _load_request(request_path, args.expected_repository_sha)
        _assert_secret_file(AUTHENTIK_STATE_DIR / "runtime.env")
        _ensure_network()
        server, _worker = _copy_and_apply_blueprint(repo)
        metadata = _authentik_metadata(server)
        _prepare_portal_runtime(metadata)
        control_image, control_id, web_image, web_id = _build_images(
            repo, args.expected_repository_sha
        )
        suffix = args.expected_repository_sha[:12]
        control_candidate = _start_control_candidate(control_image, suffix)
        control_backup = _promote_control(control_candidate)
        discovery, endpoint_statuses = _discovery()
        web_backup, authorization_url = _deploy_web(web_image, suffix)
        authentik_statuses = _authentik_statuses(repo)
        portal_status = _container_status(PORTAL_CONTAINER)
        control_status = _container_status(CONTROL_CONTAINER)
        if portal_status["health"] != "healthy" or control_status["health"] != "healthy":
            raise DeploymentError("Portal containers are not healthy after promotion")
        inspected_env = _run(
            ["docker", "inspect", "--format", "{{json .Config.Env}}", PORTAL_CONTAINER]
        ).stdout
        if "PORTAL_IDENTITY_FIXTURE_MODE=disabled" not in inspected_env:
            raise DeploymentError("Portal identity fixture mode is not disabled")
        report.update(
            {
                "status": "success",
                "authentik": {
                    "application_exists": bool(metadata["application_pk"]),
                    "provider_exists": bool(metadata["provider_pk"]),
                    "issuer": discovery["issuer"],
                    "redirect_uri": REDIRECT_URI,
                    "scopes": ["openid", "profile", "email"],
                    "services": authentik_statuses,
                },
                "endpoint_statuses": endpoint_statuses,
                "portal": {
                    "origin": f"http://{PORTAL_BIND_ADDRESS}:{PORTAL_PORT}",
                    "authorization_url": authorization_url,
                    "container": portal_status,
                    "control_plane": control_status,
                    "web_image_id": web_id,
                    "control_plane_image_id": control_id,
                    "identity_transport": "local_http_test",
                },
                "identity_fixture_disabled": True,
                "browser_acceptance": "ready_for_owner_mfa",
                "next_owner_url": f"http://{PORTAL_BIND_ADDRESS}:{PORTAL_PORT}/",
            }
        )
        for backup in (web_backup, control_backup):
            if backup:
                _remove_container(backup)
        return_code = 0
    except Exception as exc:
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        return_code = 1
    digest = _write_report(report_path, report)
    print(json.dumps({"report": str(report_path), "sha256": digest, "status": report["status"]}))
    return return_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--expected-repository-sha", required=True)
    parser.add_argument("--report", required=True)
    return deploy(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
