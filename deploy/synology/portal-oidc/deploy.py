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
from urllib.parse import urlparse


REQUEST_RELATIVE_PATH = "deploy/synology/portal-oidc/run-requests/public-oidc-20260801-v1.json"
REQUEST_ID = "portal-authentik-public-oidc-20260801-v1"
AUTHENTIK_PROJECT = "portal-authentik-local-test"
AUTHENTIK_STATE_DIR = Path("/var/lib/freqtrade-staging-state/portal-authentik-local-test")
PORTAL_STATE_DIR = Path("/var/lib/freqtrade-staging-state/portal-oidc-public")
PORTAL_RUNTIME_ENV = PORTAL_STATE_DIR / "runtime.env"
PORTAL_DATA_DIR = Path("/volume1/docker/freqtrade-portal-oidc/data")
PORTAL_UID = 10001
PORTAL_GID = 10001
PORTAL_NETWORK = "portal_oidc_public"
PORTAL_CONTAINER = "freqtrade-portal-staging"
CONTROL_CONTAINER = "freqtrade-portal-control-plane"
PORTAL_BIND_ADDRESS = "192.168.1.2"
PORTAL_PORT = 3031
PORTAL_ORIGIN = "https://quant.molehill.cloud"
AUTHENTIK_ORIGIN = "https://auth.molehill.cloud"
APPLICATION_SLUG = "freqtrade-portal"
ISSUER = f"{AUTHENTIK_ORIGIN}/application/o/{APPLICATION_SLUG}/"
REDIRECT_URI = f"{PORTAL_ORIGIN}/api/identity/callback"
CLIENT_ID = "freqtrade-portal"
BLUEPRINT_NAME = "freqtrade-portal-public.yaml"
AUTHENTIK_PROVIDER_NAME = "Freqtrade Portal Public OIDC"
LIQUIDATIONS_HOST_ROOT = Path("/volume1/docker/freqtrade-liquidations/data")
LIQUIDATIONS_CONTAINER_ROOT = "/liquid20-data"
RUNTIME_TMPFS = "/tmp:rw,noexec,nosuid,nodev,size=64m"  # noqa: S108
WEB_CACHE_TMPFS = "/app/.next/cache:rw,noexec,nosuid,nodev,size=96m,uid=1000,gid=1000"


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
        capture_output=True,
    )
    if check and result.returncode != 0:
        if sensitive:
            executable = Path(command[0]).name
            raise DeploymentError(f"sensitive command failed: {executable}")
        lines = [
            line.strip()
            for stream in (result.stdout, result.stderr)
            for line in stream.splitlines()
            if line.strip()
        ]
        if not lines:
            detail = "no output"
        elif len(lines) <= 8:
            detail = " | ".join(lines)
        else:
            detail = " | ".join([*lines[:2], "...", *lines[-5:]])
        if len(detail) > 1000:
            detail = f"{detail[:997]}..."
        rendered = " ".join(command)
        raise DeploymentError(f"command failed ({result.returncode}): {rendered}: {detail}")
    return result


def _load_request(path: Path, expected_sha: str) -> dict[str, Any]:
    if not path.as_posix().endswith(REQUEST_RELATIVE_PATH):
        raise DeploymentError("request path does not match the frozen public deployment path")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "request_id": REQUEST_ID,
        "environment": "synology-staging",
        "runner": "freqtrade-staging",
        "implementation_sha": expected_sha,
        "portal_origin": PORTAL_ORIGIN,
        "authentik_origin": AUTHENTIK_ORIGIN,
        "identity_transport": "https",
        "identity_fixture_mode": "disabled",
        "bootstrap_membership_authorized": False,
        "dry_run_required": True,
        "public_ingress_authorized": True,
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
        raise DeploymentError(f"protected runtime file must have mode 0600: {path}")


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
    fd, temporary_name = tempfile.mkstemp(prefix=".runtime.", dir=path.parent, text=True)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for name in sorted(values):
                value = values[name]
                if "\n" in value or "\r" in value:
                    raise DeploymentError(f"runtime env value contains a newline: {name}")
                handle.write(f"{name}={value}\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()
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
        raise DeploymentError("public Authentik blueprint is missing")
    durable_dir = AUTHENTIK_STATE_DIR / "blueprints"
    durable_dir.mkdir(parents=True, exist_ok=True)
    durable = durable_dir / BLUEPRINT_NAME
    temporary = durable.with_suffix(".tmp")
    shutil.copyfile(source, temporary)
    temporary.chmod(0o644)
    temporary.replace(durable)

    compose = _compose_command(repo)
    worker = _run([*compose, "ps", "-q", "worker"]).stdout.strip()
    server = _run([*compose, "ps", "-q", "server"]).stdout.strip()
    if not worker or not server:
        raise DeploymentError("Authen­tik server or worker container is unavailable")
    _run(["docker", "exec", "-u", "0", worker, "mkdir", "-p", "/blueprints/custom"])
    _run(["docker", "cp", str(durable), f"{worker}:/blueprints/custom/{BLUEPRINT_NAME}"])
    _run(
        [
            "docker",
            "exec",
            worker,
            "ak",
            "apply_blueprint",
            f"/blueprints/custom/{BLUEPRINT_NAME}",
        ],
        sensitive=True,
    )
    return server, worker


def _authentik_metadata(server: str) -> dict[str, str]:
    script = f"""
import json
from authentik.core.models import Application
from authentik.providers.oauth2.models import OAuth2Provider
provider = OAuth2Provider.objects.get(name={AUTHENTIK_PROVIDER_NAME!r})
application = Application.objects.get(provider=provider)
print('__PORTAL_JSON__' + json.dumps({{
    'application_pk': str(application.pk),
    'application_slug': str(application.slug),
    'provider_pk': str(provider.pk),
    'client_id': str(provider.client_id),
    'client_secret': str(provider.client_secret),
}}, sort_keys=True))
""".strip()
    result = _run(
        ["docker", "exec", server, "ak", "shell", "-c", script],
        sensitive=True,
    )
    marker = next(
        (
            line.removeprefix("__PORTAL_JSON__")
            for line in result.stdout.splitlines()
            if line.startswith("__PORTAL_JSON__")
        ),
        None,
    )
    if marker is None:
        raise DeploymentError("Authen­tik metadata query did not return the marker")
    payload = json.loads(marker)
    required = {
        "application_pk",
        "application_slug",
        "provider_pk",
        "client_id",
        "client_secret",
    }
    if set(payload) != required or not all(
        isinstance(payload[key], str) and payload[key] for key in required
    ):
        raise DeploymentError("Authen­tik metadata query returned an invalid shape")
    if payload["application_slug"] != APPLICATION_SLUG:
        raise DeploymentError("deployed Authen­tik application slug differs from contract")
    if payload["client_id"] != CLIENT_ID:
        raise DeploymentError("deployed Authen­tik client ID differs from contract")
    payload["issuer"] = f"{AUTHENTIK_ORIGIN}/application/o/{payload['application_slug']}/"
    if payload["issuer"] != ISSUER:
        raise DeploymentError("derived deployed issuer differs from frozen issuer")
    return payload


def _secret_b64() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")


def _prepare_portal_runtime(metadata: dict[str, str]) -> None:
    existing = _read_env(PORTAL_RUNTIME_ENV)
    stored_secret = existing.get("PORTAL_IDENTITY_CLIENT_SECRET")
    if stored_secret and stored_secret != metadata["client_secret"]:
        raise DeploymentError(
            "stored Portal client secret differs from Authen­tik; refusing rotation"
        )
    values = {
        "PORTAL_DATABASE_URL": "sqlite+pysqlite:////state/portal.db",
        "PORTAL_ENVIRONMENT": "production",
        "PORTAL_IDENTITY_CLIENT_ID": CLIENT_ID,
        "PORTAL_IDENTITY_CLIENT_SECRET": metadata["client_secret"],
        "PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64": existing.get(
            "PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64",
            _secret_b64(),
        ),
        "PORTAL_IDENTITY_ISSUER": metadata["issuer"],
        "PORTAL_IDENTITY_REDIRECT_URI": REDIRECT_URI,
        "PORTAL_IDENTITY_SESSION_HMAC_KEY_B64": existing.get(
            "PORTAL_IDENTITY_SESSION_HMAC_KEY_B64",
            _secret_b64(),
        ),
        "PORTAL_IDENTITY_TRANSPORT_MODE": "https",
    }
    _write_env_atomic(PORTAL_RUNTIME_ENV, values)
    PORTAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    os.chown(PORTAL_DATA_DIR, PORTAL_UID, PORTAL_GID)
    PORTAL_DATA_DIR.chmod(0o700)


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
    return (
        control_image,
        _docker_image_id(control_image),
        web_image,
        _docker_image_id(web_image),
    )


def _ensure_network() -> None:
    result = _run(["docker", "network", "inspect", PORTAL_NETWORK], check=False)
    if result.returncode != 0:
        _run(["docker", "network", "create", "--driver", "bridge", PORTAL_NETWORK])


def _container_exists(name: str) -> bool:
    return _run(["docker", "container", "inspect", name], check=False).returncode == 0


def _remove_container(name: str) -> None:
    if _container_exists(name):
        _run(["docker", "rm", "-f", name])


def _wait_healthy(name: str, timeout_seconds: int = 150) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        state = _run(
            [
                "docker",
                "inspect",
                "--format",
                "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
                name,
            ],
            check=False,
        ).stdout.strip()
        if state == "healthy":
            return
        if state in {"exited", "dead", "unhealthy"}:
            raise DeploymentError(f"container {name} entered state {state}")
        time.sleep(2)
    raise DeploymentError(f"container {name} did not become healthy")


def _control_run_args(image: str, name: str) -> list[str]:
    return [
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
        RUNTIME_TMPFS,
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        "256",
        "--memory",
        "768m",
        "--user",
        f"{PORTAL_UID}:{PORTAL_GID}",
        "--env-file",
        str(PORTAL_RUNTIME_ENV),
        "--mount",
        f"type=bind,src={PORTAL_DATA_DIR},dst=/state,rw",
        "--label",
        "ai.freqtrade.identity-fixture=disabled",
        "--label",
        "ai.freqtrade.membership-bootstrap=explicit-only",
        "--label",
        "ai.freqtrade.live-capital-authorized=false",
        image,
    ]


def _start_control_candidate(image: str, suffix: str) -> str:
    candidate = f"{CONTROL_CONTAINER}-candidate-{suffix}"
    _remove_container(candidate)
    _run(_control_run_args(image, candidate))
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


def _liquidations_group_id() -> str:
    if not LIQUIDATIONS_HOST_ROOT.is_dir():
        raise DeploymentError("canonical Liquid20 mount is unavailable")
    return str(LIQUIDATIONS_HOST_ROOT.stat().st_gid)


def _web_run_args(image: str, name: str, *, publish: bool) -> list[str]:
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
        RUNTIME_TMPFS,
        "--tmpfs",
        WEB_CACHE_TMPFS,
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        "256",
        "--memory",
        "768m",
        "--group-add",
        _liquidations_group_id(),
        "--mount",
        (f"type=bind,src={LIQUIDATIONS_HOST_ROOT},dst={LIQUIDATIONS_CONTAINER_ROOT},readonly"),
        "--env",
        "PORTAL_WEB_DATA_MODE=fixture",
        "--env",
        "PORTAL_ENVIRONMENT=production",
        "--env",
        "PORTAL_IDENTITY_FIXTURE_MODE=disabled",
        "--env",
        "PORTAL_IDENTITY_TRANSPORT_MODE=https",
        "--env",
        f"PORTAL_IDENTITY_ISSUER={ISSUER}",
        "--env",
        f"PORTAL_CONTROL_PLANE_URL=http://{CONTROL_CONTAINER}:8000",
        "--env",
        f"PORTAL_LIQUIDATIONS_DATA_ROOT={LIQUIDATIONS_CONTAINER_ROOT}",
        "--label",
        "ai.freqtrade.identity-fixture=disabled",
        "--label",
        "ai.freqtrade.public-origin=quant.molehill.cloud",
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
    if not isinstance(location, str):
        raise DeploymentError("Portal login redirect is missing")
    parsed = urlparse(location)
    if parsed.scheme != "https" or parsed.netloc != "auth.molehill.cloud":
        raise DeploymentError("Portal login did not redirect to public Authen­tik")
    if not parsed.path.startswith("/application/o/authorize"):
        raise DeploymentError("Portal login redirect path is not the OIDC authorize endpoint")
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


def _discovery_from_identity_container() -> tuple[dict[str, Any], dict[str, int]]:
    script = f"""
import json
import urllib.request
issuer = {ISSUER!r}
discovery_url = issuer.rstrip('/') + '/.well-known/openid-configuration'
with urllib.request.urlopen(discovery_url, timeout=15) as response:
    discovery = json.loads(response.read().decode('utf-8'))
    discovery_status = response.status
if discovery.get('issuer') != issuer:
    raise SystemExit('issuer mismatch')
for key in ('authorization_endpoint', 'token_endpoint', 'jwks_uri'):
    value = discovery.get(key)
    if not isinstance(value, str) or not value.startswith({AUTHENTIK_ORIGIN!r} + '/'):
        raise SystemExit('invalid endpoint: ' + key)
with urllib.request.urlopen(discovery['jwks_uri'], timeout=15) as response:
    jwks = json.loads(response.read().decode('utf-8'))
    jwks_status = response.status
if not isinstance(jwks.get('keys'), list) or not jwks['keys']:
    raise SystemExit('empty JWKS')
print('__PORTAL_DISCOVERY__' + json.dumps({{
    'discovery': discovery_status,
    'jwks_uri': jwks_status,
    'issuer': discovery['issuer'],
}}, sort_keys=True))
""".strip()
    result = _run(
        ["docker", "exec", CONTROL_CONTAINER, "python", "-c", script],
        sensitive=True,
    )
    marker = next(
        (
            line.removeprefix("__PORTAL_DISCOVERY__")
            for line in result.stdout.splitlines()
            if line.startswith("__PORTAL_DISCOVERY__")
        ),
        None,
    )
    if marker is None:
        raise DeploymentError("identity container discovery probe returned no marker")
    payload = json.loads(marker)
    if payload.get("issuer") != ISSUER:
        raise DeploymentError("identity container observed an unexpected issuer")
    return {"issuer": payload["issuer"]}, {
        "discovery": int(payload["discovery"]),
        "jwks_uri": int(payload["jwks_uri"]),
    }


def _no_redirect_opener() -> urllib.request.OpenerDirector:
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, file_pointer, code, message, headers, url):
            return None

    return urllib.request.build_opener(NoRedirect)


def _probe_public_portal() -> tuple[int, str]:
    url = f"{PORTAL_ORIGIN}/api/identity/login?return_to=%2F"
    request = urllib.request.Request(url, headers={"accept": "text/html"})  # noqa: S310
    opener = _no_redirect_opener()
    try:
        opener.open(request, timeout=15)
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        location = exc.headers.get("location", "")
    else:
        raise DeploymentError("public Portal login unexpectedly did not redirect")
    if status_code not in {302, 303, 307, 308}:
        raise DeploymentError(f"public Portal login returned status {status_code}")
    parsed = urlparse(location)
    if parsed.scheme != "https" or parsed.netloc != "auth.molehill.cloud":
        raise DeploymentError("public Portal login did not redirect to public Authen­tik")
    return status_code, location


def _container_status(name: str) -> dict[str, str]:
    inspect_format = (
        "{{.Name}}|{{.State.Status}}|"
        "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}|{{.Config.Image}}"
    )
    result = _run(["docker", "inspect", "--format", inspect_format, name]).stdout.strip()
    container_name, state, health, image = result.split("|", 3)
    return {
        "name": container_name.removeprefix("/"),
        "state": state,
        "health": health,
        "image": image,
    }


def _assert_container_hardening(name: str, *, published: bool) -> None:
    payload = json.loads(_run(["docker", "inspect", name]).stdout)[0]
    host_config = payload["HostConfig"]
    if host_config.get("Privileged"):
        raise DeploymentError(f"container is privileged: {name}")
    if host_config.get("NetworkMode") == "host":
        raise DeploymentError(f"container uses host networking: {name}")
    if not host_config.get("ReadonlyRootfs"):
        raise DeploymentError(f"container root filesystem is writable: {name}")
    binds = host_config.get("Binds") or []
    if any("/var/run/docker.sock" in value for value in binds):
        raise DeploymentError(f"container mounts the Docker socket: {name}")
    port_bindings = host_config.get("PortBindings") or {}
    if published and "3000/tcp" not in port_bindings:
        raise DeploymentError("Portal web container is not bound to the LAN origin")
    if not published and port_bindings:
        raise DeploymentError("identity control plane unexpectedly publishes a port")


def _authentik_statuses(repo: Path) -> list[dict[str, str]]:
    compose = _compose_command(repo)
    statuses: list[dict[str, str]] = []
    for service in ("postgresql", "server", "worker"):
        container = _run([*compose, "ps", "-q", service]).stdout.strip()
        if not container:
            raise DeploymentError(f"Authen­tik service is missing: {service}")
        status = _container_status(container)
        status["service"] = service
        if status["health"] != "healthy":
            raise DeploymentError(f"Authen­tik service is not healthy: {service}")
        statuses.append(status)
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
        "public_ingress_authorized": True,
        "restore_authorized": False,
        "identity_fixture_disabled": False,
        "membership_bootstrap": "not_authorized",
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
            repo,
            args.expected_repository_sha,
        )
        suffix = args.expected_repository_sha[:12]
        control_candidate = _start_control_candidate(control_image, suffix)
        control_backup = _promote_control(control_candidate)
        discovery, endpoint_statuses = _discovery_from_identity_container()
        web_backup, authorization_url = _deploy_web(web_image, suffix)
        public_status, public_authorization_url = _probe_public_portal()
        authentik_statuses = _authentik_statuses(repo)
        portal_status = _container_status(PORTAL_CONTAINER)
        control_status = _container_status(CONTROL_CONTAINER)
        if portal_status["health"] != "healthy" or control_status["health"] != "healthy":
            raise DeploymentError("Portal containers are not healthy after promotion")
        _assert_container_hardening(PORTAL_CONTAINER, published=True)
        _assert_container_hardening(CONTROL_CONTAINER, published=False)
        report.update(
            {
                "status": "success",
                "authentik": {
                    "application_exists": bool(metadata["application_pk"]),
                    "application_slug": metadata["application_slug"],
                    "provider_exists": bool(metadata["provider_pk"]),
                    "issuer": discovery["issuer"],
                    "redirect_uri": REDIRECT_URI,
                    "scopes": ["openid", "profile", "email"],
                    "services": authentik_statuses,
                },
                "endpoint_statuses": endpoint_statuses,
                "portal": {
                    "origin": PORTAL_ORIGIN,
                    "internal_authorization_url": authorization_url,
                    "public_authorization_url": public_authorization_url,
                    "public_login_status": public_status,
                    "container": portal_status,
                    "control_plane": control_status,
                    "web_image_id": web_id,
                    "control_plane_image_id": control_id,
                    "identity_transport": "https",
                },
                "identity_fixture_disabled": True,
                "membership_bootstrap": "explicit_owner_action_required",
                "browser_acceptance": "ready_for_owner_password_totp",
                "next_owner_url": PORTAL_ORIGIN,
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
    print(
        json.dumps(
            {
                "report": str(report_path),
                "sha256": digest,
                "status": report["status"],
            }
        )
    )
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
