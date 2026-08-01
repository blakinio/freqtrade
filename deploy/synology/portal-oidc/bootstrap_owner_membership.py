#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REQUEST_RELATIVE_PATH = (
    "deploy/synology/portal-oidc/run-requests/owner-membership-bootstrap-20260801-v1.json"
)
REQUEST_ID = "portal-authentik-owner-membership-bootstrap-20260801-v1"
AUTHENTIK_PROJECT = "portal-authentik-local-test"
AUTHENTIK_STATE_DIR = Path("/var/lib/freqtrade-staging-state/portal-authentik-local-test")
CONTROL_CONTAINER = "freqtrade-portal-control-plane"
TARGET_USERNAME = "akadmin"
TARGET_TENANT_ID = "tenant-local"
TARGET_ROLE = "admin"
SUBJECT_MODE = "user_uuid"
UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
MAX_DETAIL = 1000


class BootstrapError(RuntimeError):
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
    input_text: str | None = None,
    sensitive: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        input=input_text,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        if sensitive:
            raise BootstrapError(f"sensitive command failed: {Path(command[0]).name}")
        raise BootstrapError(
            f"command failed ({result.returncode}): {' '.join(command)}: {_bounded_detail(result)}"
        )
    return result


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _assert_secret_file(path: Path) -> None:
    if not path.is_file() or _mode(path) != 0o600:
        raise BootstrapError(f"protected runtime file must have mode 0600: {path}")


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


def _load_request(path: Path, expected_sha: str) -> dict[str, Any]:
    if not path.as_posix().endswith(REQUEST_RELATIVE_PATH):
        raise BootstrapError("request path does not match the frozen owner bootstrap path")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise BootstrapError("implementation SHA must be a full lowercase commit SHA")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "request_id": REQUEST_ID,
        "environment": "synology-staging",
        "runner": "freqtrade-staging",
        "implementation_sha": expected_sha,
        "target_username": TARGET_USERNAME,
        "target_tenant_id": TARGET_TENANT_ID,
        "target_role": TARGET_ROLE,
        "subject_mode": SUBJECT_MODE,
        "bootstrap_membership_authorized": True,
        "browser_acceptance_authorized": False,
        "public_ingress_authorized": True,
        "live_capital_authorized": False,
        "restore_authorized": False,
        "secret_values_in_request": False,
    }
    if payload != expected:
        raise BootstrapError("owner bootstrap request bytes do not match the frozen contract")
    return payload


def _extract_marker(result: subprocess.CompletedProcess[str], marker: str) -> dict[str, Any]:
    payload_text = next(
        (
            line.removeprefix(marker)
            for line in result.stdout.splitlines()
            if line.startswith(marker)
        ),
        None,
    )
    if payload_text is None:
        raise BootstrapError("sensitive command returned no expected marker")
    payload = json.loads(payload_text)
    if not isinstance(payload, dict):
        raise BootstrapError("sensitive command marker returned an invalid payload")
    return payload


def _authentik_server(repository: Path) -> str:
    result = _run([*_compose_command(repository), "ps", "-q", "server"])
    server = result.stdout.strip()
    if not server:
        raise BootstrapError("Authentik server container is unavailable")
    return server


def _lookup_exact_owner(server: str) -> dict[str, str]:
    script = f"""
import json
from authentik.core.models import User
user = User.objects.get(username={TARGET_USERNAME!r})
print('__PORTAL_OWNER__' + json.dumps({{
    'username': str(user.username),
    'subject': str(user.uuid),
    'display_name': str(user.name or user.username),
    'email': str(user.email or ''),
    'is_active': bool(user.is_active),
}}, sort_keys=True))
""".strip()
    result = _run(
        ["docker", "exec", server, "ak", "shell", "-c", script],
        sensitive=True,
    )
    payload = _extract_marker(result, "__PORTAL_OWNER__")
    expected_keys = {"username", "subject", "display_name", "email", "is_active"}
    if set(payload) != expected_keys:
        raise BootstrapError("Authentik owner lookup returned an invalid shape")
    if payload["username"] != TARGET_USERNAME or payload["is_active"] is not True:
        raise BootstrapError("exact Authentik owner account is missing or inactive")
    subject = payload["subject"]
    display_name = payload["display_name"]
    email = payload["email"]
    if not isinstance(subject, str) or not UUID_PATTERN.fullmatch(subject.lower()):
        raise BootstrapError("Authentik owner subject is not a UUID")
    if not isinstance(display_name, str) or not display_name.strip():
        raise BootstrapError("Authentik owner display name is empty")
    if not isinstance(email, str):
        raise BootstrapError("Authentik owner email is invalid")
    return {
        "username": TARGET_USERNAME,
        "subject": subject.lower(),
        "display_name": display_name.strip(),
        "email": email.strip(),
    }


def _bootstrap_exact_owner(identity: dict[str, str]) -> dict[str, Any]:
    payload = {
        "subject": identity["subject"],
        "display_name": identity["display_name"],
        "email": identity["email"] or None,
        "tenant_id": TARGET_TENANT_ID,
    }
    script = """
import argparse
import json
import sys
from ai_platform.portal.identity.bootstrap_membership import bootstrap
payload = json.loads(sys.stdin.read())
args = argparse.Namespace(
    subject=payload['subject'],
    display_name=payload['display_name'],
    email=payload.get('email'),
    tenant_id=payload['tenant_id'],
    confirm_exact_principal=True,
)
print('__PORTAL_BOOTSTRAP__' + json.dumps(bootstrap(args), sort_keys=True))
""".strip()
    result = _run(
        ["docker", "exec", "-i", CONTROL_CONTAINER, "python", "-c", script],
        input_text=json.dumps(payload, separators=(",", ":"), sort_keys=True),
        sensitive=True,
    )
    report = _extract_marker(result, "__PORTAL_BOOTSTRAP__")
    required = {
        "status": "success",
        "tenant_id": TARGET_TENANT_ID,
        "role": TARGET_ROLE,
        "secret_values_recorded": False,
        "live_capital_authorized": False,
        "subject_sha256": hashlib.sha256(identity["subject"].encode("utf-8")).hexdigest(),
    }
    for key, expected in required.items():
        if report.get(key) != expected:
            raise BootstrapError(f"membership bootstrap invariant failed: {key}")
    for key in ("principal_id", "membership_id", "issuer"):
        if not isinstance(report.get(key), str) or not report[key]:
            raise BootstrapError(f"membership bootstrap returned an invalid {key}")
    if type(report.get("created")) is not bool:
        raise BootstrapError("membership bootstrap returned an invalid created flag")
    return report


def _verify_exact_owner(identity: dict[str, str]) -> dict[str, Any]:
    payload = {"subject": identity["subject"], "tenant_id": TARGET_TENANT_ID}
    script = """
import json
import os
import sys
from datetime import UTC, datetime
from sqlalchemy import select
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.identity.models import IdentityAuditEventRow
from ai_platform.portal.identity.repository import IdentityRepository
payload = json.loads(sys.stdin.read())
issuer = os.environ['PORTAL_IDENTITY_ISSUER']
database_url = os.environ['PORTAL_DATABASE_URL']
session_factory = build_session_factory(build_engine(database_url))
now = datetime.now(UTC)
with session_factory() as session:
    repository = IdentityRepository(session)
    principal = repository.get_principal_by_external_identity(issuer, payload['subject'])
    if principal is None:
        raise SystemExit('principal missing')
    memberships = repository.list_memberships_for_principal(principal.principal_id, now)
    matching = [item for item in memberships if item.tenant_id == payload['tenant_id']]
    if len(matching) != 1:
        raise SystemExit('exact active membership missing')
    membership = matching[0]
    audit = session.scalar(
        select(IdentityAuditEventRow)
        .where(
            IdentityAuditEventRow.action == 'identity.membership_bootstrapped',
            IdentityAuditEventRow.principal_id == principal.principal_id,
            IdentityAuditEventRow.tenant_id == membership.tenant_id,
            IdentityAuditEventRow.membership_id == membership.membership_id,
            IdentityAuditEventRow.result == 'success',
        )
        .order_by(IdentityAuditEventRow.occurred_at.desc())
    )
    print('__PORTAL_VERIFY__' + json.dumps({
        'principal_id': principal.principal_id,
        'principal_status': principal.status,
        'membership_id': membership.membership_id,
        'membership_status': membership.status,
        'tenant_id': membership.tenant_id,
        'roles_json': membership.roles_json,
        'audit_present': audit is not None,
    }, sort_keys=True))
""".strip()
    result = _run(
        ["docker", "exec", "-i", CONTROL_CONTAINER, "python", "-c", script],
        input_text=json.dumps(payload, separators=(",", ":"), sort_keys=True),
        sensitive=True,
    )
    report = _extract_marker(result, "__PORTAL_VERIFY__")
    required = {
        "principal_status": "active",
        "membership_status": "active",
        "tenant_id": TARGET_TENANT_ID,
        "roles_json": json.dumps([TARGET_ROLE]),
        "audit_present": True,
    }
    for key, expected in required.items():
        if report.get(key) != expected:
            raise BootstrapError(f"membership verification invariant failed: {key}")
    for key in ("principal_id", "membership_id"):
        if not isinstance(report.get(key), str) or not report[key]:
            raise BootstrapError(f"membership verification returned an invalid {key}")
    return report


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".owner-bootstrap.", dir=path.parent, text=True)
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


def run(
    *,
    repository: Path,
    request_path: Path,
    expected_repository_sha: str,
    report_path: Path,
) -> dict[str, Any]:
    request = _load_request(request_path, expected_repository_sha)
    server = _authentik_server(repository)
    identity = _lookup_exact_owner(server)
    bootstrap = _bootstrap_exact_owner(identity)
    verification = _verify_exact_owner(identity)
    if bootstrap["principal_id"] != verification["principal_id"]:
        raise BootstrapError("verified principal ID differs from bootstrap result")
    if bootstrap["membership_id"] != verification["membership_id"]:
        raise BootstrapError("verified membership ID differs from bootstrap result")

    report = {
        "status": "success",
        "request_id": request["request_id"],
        "implementation_sha": expected_repository_sha,
        "target_username": TARGET_USERNAME,
        "target_tenant_id": TARGET_TENANT_ID,
        "target_role": TARGET_ROLE,
        "subject_mode": SUBJECT_MODE,
        "subject_sha256": bootstrap["subject_sha256"],
        "principal_id": bootstrap["principal_id"],
        "membership_id": bootstrap["membership_id"],
        "membership_created": bootstrap["created"],
        "audit_action": "identity.membership_bootstrapped",
        "audit_present": verification["audit_present"],
        "browser_acceptance": "explicit_owner_action_required",
        "logout_validation": "explicit_owner_action_required",
        "secret_values_recorded": False,
        "live_capital_authorized": False,
        "restore_authorized": False,
        "public_ingress_authorized": True,
    }
    _write_report(report_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--expected-repository-sha", required=True)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run(
            repository=args.repository.resolve(),
            request_path=args.request.resolve(),
            expected_repository_sha=args.expected_repository_sha,
            report_path=args.report.resolve(),
        )
    except Exception as exc:
        failure = {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "secret_values_recorded": False,
            "live_capital_authorized": False,
        }
        _write_report(args.report.resolve(), failure)
        print(str(exc), file=sys.stderr)
        return 1
    digest = hashlib.sha256(args.report.resolve().read_bytes()).hexdigest()
    print(json.dumps({"status": report["status"], "report": str(args.report), "sha256": digest}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
