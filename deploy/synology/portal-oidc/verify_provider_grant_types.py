#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


AUTHENTIK_PROJECT = "portal-authentik-local-test"
AUTHENTIK_STATE_DIR = Path("/var/lib/freqtrade-staging-state/portal-authentik-local-test")
AUTHENTIK_PROVIDER_NAME = "Freqtrade Portal Public OIDC"
CLIENT_ID = "freqtrade-portal"
EXPECTED_GRANT_TYPES = ["authorization_code"]
MARKER = "__PORTAL_GRANTS__"
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


def _augment_report(report_path: Path, provider: dict[str, Any]) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("status") != "success":
        raise GrantTypeVerificationError(
            "deployment report must be successful before grant verification"
        )
    authentik = report.get("authentik")
    if not isinstance(authentik, dict):
        raise GrantTypeVerificationError("deployment report Authentik section is missing")
    authentik["grant_types"] = provider["grant_types"]
    authentik["authorization_code_enabled"] = True
    authentik["legacy_grants_disabled"] = True
    report["secret_values_recorded"] = False
    report["live_capital_authorized"] = False
    _write_json_atomic(report_path, report)
    return report


def run(*, repository: Path, report_path: Path) -> dict[str, Any]:
    provider = _query_grant_types(_server_container(repository))
    return _augment_report(report_path, provider)


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
                "secret_values_recorded": False,
                "live_capital_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
