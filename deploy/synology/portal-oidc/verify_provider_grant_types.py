#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


AUTHENTIK_PROJECT = "portal-authentik-local-test"
AUTHENTIK_STATE_DIR = Path("/var/lib/freqtrade-staging-state/portal-authentik-local-test")
AUTHENTIK_PROVIDER_NAME = "Freqtrade Portal Public OIDC"
CLIENT_ID = "freqtrade-portal"
EXPECTED_GRANT_TYPES = ["authorization_code"]
MARKER = "__PORTAL_GRANTS__"
CALLBACK_MARKER = "__PORTAL_PUBLIC_CALLBACK__"
PORTAL_CONTAINER = "freqtrade-portal-staging"
PORTAL_ORIGIN = "https://quant.molehill.cloud"
CALLBACK_RETURN_TO = "/portal"
RUNTIME_TMPFS = "/tmp:rw,noexec,nosuid,nodev,size=64m"  # noqa: S108
WEB_CACHE_TMPFS = "/app/.next/cache:rw,noexec,nosuid,nodev,size=96m,uid=1000,gid=1000"
MAX_DETAIL = 1000


class GrantTypeVerificationError(RuntimeError):
    pass


def _bounded_detail(result: subprocess.CompletedProcess[str]) -> str:
    lines = [
        line.strip()
        for stream in (result.stdout, result.stderr)
        for line in stream.splitlines()
        if line.strip()
    ]
    if not lines:
        return "no output"
    detail = " | ".join(lines[-8:])
    if len(detail) > MAX_DETAIL:
        return f"{detail[: MAX_DETAIL - 3]}..."
    return detail


def _run(
    command: list[str],
    *,
    sensitive: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        if sensitive:
            raise GrantTypeVerificationError(f"sensitive command failed: {Path(command[0]).name}")
        raise GrantTypeVerificationError(
            f"command failed ({result.returncode}): {' '.join(command)}: {_bounded_detail(result)}"
        )
    return result


def _assert_secret_file(path: Path) -> None:
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise GrantTypeVerificationError(f"protected runtime file must have mode 0600: {path}")


def _compose_command(repository: Path) -> list[str]:
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
        str(repository / "deploy/synology/portal-authentik/compose.yml"),
    ]


def _server_container(repository: Path) -> str:
    result = _run([*_compose_command(repository), "ps", "-q", "server"])
    server = result.stdout.strip()
    if not server:
        raise GrantTypeVerificationError("Authentik server container is unavailable")
    return server


def _query_grant_types(server: str) -> dict[str, Any]:
    script = f"""
import json
from authentik.providers.oauth2.models import OAuth2Provider
provider = OAuth2Provider.objects.get(name={AUTHENTIK_PROVIDER_NAME!r})
print({MARKER!r} + json.dumps({{
    'name': str(provider.name),
    'client_id': str(provider.client_id),
    'grant_types': sorted(str(item) for item in (provider.grant_types or [])),
}}, sort_keys=True))
""".strip()
    result = _run(
        ["docker", "exec", server, "ak", "shell", "-c", script],
        sensitive=True,
    )
    payload_text = next(
        (
            line.removeprefix(MARKER)
            for line in result.stdout.splitlines()
            if line.startswith(MARKER)
        ),
        None,
    )
    if payload_text is None:
        raise GrantTypeVerificationError("Authentik grant-type query returned no expected marker")
    payload = json.loads(payload_text)
    if not isinstance(payload, dict) or set(payload) != {
        "name",
        "client_id",
        "grant_types",
    }:
        raise GrantTypeVerificationError("Authentik grant-type query returned an invalid shape")
    if payload["name"] != AUTHENTIK_PROVIDER_NAME:
        raise GrantTypeVerificationError("deployed Authentik provider name differs")
    if payload["client_id"] != CLIENT_ID:
        raise GrantTypeVerificationError("deployed Authentik client ID differs")
    if payload["grant_types"] != EXPECTED_GRANT_TYPES:
        raise GrantTypeVerificationError(
            "deployed Authentik grant types are not authorization-code-only"
        )
    return payload


def _container_image(name: str) -> str:
    result = _run(["docker", "inspect", "--format", "{{.Config.Image}}", name])
    image = result.stdout.strip()
    if not image:
        raise GrantTypeVerificationError("Portal web container image is unavailable")
    return image


def _callback_probe_script() -> str:
    target = (
        "http://127.0.0.1:3000/api/identity/callback"
        f"?code=public-origin-probe&state=public-origin-probe&return_to={CALLBACK_RETURN_TO}"
    )
    return (
        f"fetch({target!r},{{redirect:'manual'}}).then(async r=>{{"
        f"console.log({CALLBACK_MARKER!r}+JSON.stringify({{status:r.status,"
        "location:r.headers.get('location')}}));"
        "if(r.status!==303)process.exit(2)"
        "}).catch(e=>{console.error(String(e));process.exit(3)})"
    )


def _probe_public_callback_redirect(image: str) -> str:
    name = f"freqtrade-portal-public-origin-probe-{os.getpid()}"
    _run(["docker", "rm", "-f", name], check=False)
    _run(
        [
            "docker",
            "run",
            "--detach",
            "--name",
            name,
            "--network",
            "none",
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
            "128",
            "--memory",
            "512m",
            "--env",
            "PORTAL_WEB_DATA_MODE=fixture",
            "--env",
            "PORTAL_ENVIRONMENT=test",
            "--env",
            "PORTAL_IDENTITY_FIXTURE_MODE=enabled",
            "--env",
            "PORTAL_IDENTITY_TRANSPORT_MODE=https",
            "--env",
            f"PORTAL_PUBLIC_ORIGIN={PORTAL_ORIGIN}",
            image,
        ]
    )
    try:
        deadline = time.monotonic() + 90
        last_result: subprocess.CompletedProcess[str] | None = None
        while time.monotonic() < deadline:
            result = _run(
                ["docker", "exec", name, "node", "-e", _callback_probe_script()],
                check=False,
            )
            last_result = result
            if result.returncode == 0:
                payload_text = next(
                    (
                        line.removeprefix(CALLBACK_MARKER)
                        for line in result.stdout.splitlines()
                        if line.startswith(CALLBACK_MARKER)
                    ),
                    None,
                )
                if payload_text is None:
                    raise GrantTypeVerificationError(
                        "Portal public callback probe returned no expected marker"
                    )
                payload = json.loads(payload_text)
                expected_location = f"{PORTAL_ORIGIN}{CALLBACK_RETURN_TO}"
                if payload != {"status": 303, "location": expected_location}:
                    raise GrantTypeVerificationError(
                        "Portal callback did not redirect to the public Portal origin"
                    )
                return expected_location
            state = _run(
                ["docker", "inspect", "--format", "{{.State.Status}}", name],
                check=False,
            ).stdout.strip()
            if state in {"exited", "dead"}:
                raise GrantTypeVerificationError(
                    "Portal public callback probe container stopped unexpectedly"
                )
            time.sleep(2)
        detail = _bounded_detail(last_result) if last_result is not None else "no probe result"
        raise GrantTypeVerificationError(f"Portal public callback probe timed out: {detail}")
    finally:
        _run(["docker", "rm", "-f", name], check=False)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".grant-types.", dir=path.parent, text=True)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _augment_report(
    report_path: Path,
    provider: dict[str, Any],
    callback_location: str,
) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("status") != "success":
        raise GrantTypeVerificationError(
            "deployment report must be successful before grant verification"
        )
    authentik = report.get("authentik")
    if not isinstance(authentik, dict):
        raise GrantTypeVerificationError("deployment report Authentik section is missing")
    portal = report.get("portal")
    if not isinstance(portal, dict):
        raise GrantTypeVerificationError("deployment report Portal section is missing")
    authentik["grant_types"] = provider["grant_types"]
    authentik["authorization_code_enabled"] = True
    authentik["legacy_grants_disabled"] = True
    portal["public_callback_redirect_location"] = callback_location
    portal["public_callback_redirect_verified"] = True
    report["secret_values_recorded"] = False
    report["live_capital_authorized"] = False
    _write_json_atomic(report_path, report)
    return report


def run(*, repository: Path, report_path: Path) -> dict[str, Any]:
    provider = _query_grant_types(_server_container(repository))
    callback_location = _probe_public_callback_redirect(_container_image(PORTAL_CONTAINER))
    return _augment_report(report_path, provider, callback_location)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run(
            repository=args.repository.resolve(),
            report_path=args.report.resolve(),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": report["status"],
                "grant_types": report["authentik"]["grant_types"],
                "public_callback_redirect_verified": report["portal"][
                    "public_callback_redirect_verified"
                ],
                "secret_values_recorded": False,
                "live_capital_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
