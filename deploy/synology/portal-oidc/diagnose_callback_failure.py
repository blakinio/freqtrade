#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUEST_RELATIVE_PATH = (
    "deploy/synology/portal-oidc/run-requests/callback-diagnostic-20260801-v1.json"
)
REQUEST_ID = "portal-authentik-callback-diagnostic-20260801-v1"
CONTROL_CONTAINER = "freqtrade-portal-control-plane"
WEB_CONTAINER = "freqtrade-portal-staging"
MAX_LOG_BYTES = 2_000_000
MAX_MESSAGE = 600

SENSITIVE_PAIR = re.compile(
    r"(?i)(?P<prefix>(?:[?&]|\b)(?:code|state|client_secret|access_token|"
    r"refresh_token|id_token)\s*[:=]\s*[\"']?)(?P<value>[^&\s,\"';]+)"
)
SENSITIVE_HEADER = re.compile(r"(?i)\b(?P<name>authorization|cookie|set-cookie)\s*:\s*.*$")
BEARER = re.compile(r"(?i)\bbearer\s+\S+")
JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
LONG_TOKEN = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{24,}(?![A-Za-z0-9_-])")
FRAME = re.compile(r'File "(?P<path>[^"]+)", line (?P<line>\d+), in (?P<function>[A-Za-z0-9_<>]+)')
EXCEPTION = re.compile(
    r"(?P<type>(?:[A-Za-z_][\w]*\.)*[A-Za-z_][\w]*(?:Error|Exception))"
    r":\s*(?P<message>.*)$"
)


class DiagnosticError(RuntimeError):
    pass


def _run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        executable = Path(command[0]).name
        raise DiagnosticError(f"diagnostic command failed: {executable}")
    return result


def _load_request(path: Path, expected_sha: str) -> dict[str, Any]:
    if not path.as_posix().endswith(REQUEST_RELATIVE_PATH):
        raise DiagnosticError("request path does not match callback diagnostic contract")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "request_id": REQUEST_ID,
        "environment": "synology-staging",
        "runner": "freqtrade-staging",
        "implementation_sha": expected_sha,
        "since_minutes": 120,
        "diagnostic_only": True,
        "configuration_mutation_authorized": False,
        "browser_acceptance_authorized": False,
        "public_ingress_authorized": True,
        "live_capital_authorized": False,
        "restore_authorized": False,
        "secret_values_in_request": False,
    }
    if payload != expected:
        raise DiagnosticError("callback diagnostic request does not match frozen contract")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise DiagnosticError("implementation SHA must be a full lowercase commit SHA")
    return payload


def _sanitize(text: str) -> str:
    sanitized = SENSITIVE_PAIR.sub(
        lambda match: f"{match.group('prefix')}<redacted>",
        text,
    )
    sanitized = SENSITIVE_HEADER.sub(
        lambda match: f"{match.group('name')}: <redacted>",
        sanitized,
    )
    sanitized = BEARER.sub("Bearer <redacted>", sanitized)
    sanitized = JWT.sub("<redacted-jwt>", sanitized)
    sanitized = LONG_TOKEN.sub("<redacted-token>", sanitized)
    return sanitized[:MAX_MESSAGE]


def _container_revision(name: str) -> str:
    result = _run(
        [
            "docker",
            "inspect",
            "--format",
            '{{index .Config.Labels "org.opencontainers.image.revision"}}',
            name,
        ]
    )
    revision = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise DiagnosticError(f"container revision label is invalid: {name}")
    return revision


def _container_state(name: str) -> dict[str, str]:
    result = _run(
        [
            "docker",
            "inspect",
            "--format",
            "{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",
            name,
        ]
    )
    state, health = result.stdout.strip().split("|", 1)
    return {"state": state, "health": health, "revision": _container_revision(name)}


def _logs(name: str, since_minutes: int) -> str:
    result = _run(
        [
            "docker",
            "logs",
            "--since",
            f"{since_minutes}m",
            "--tail",
            "5000",
            name,
        ],
        check=False,
    )
    payload = f"{result.stdout}\n{result.stderr}"
    if len(payload.encode("utf-8", errors="replace")) > MAX_LOG_BYTES:
        payload = payload[-MAX_LOG_BYTES:]
    return payload


def _extract_callback_failure(logs: str) -> dict[str, Any]:
    lines = logs.splitlines()
    callback_500_count = sum(
        "/v1/identity/callback?" in line and re.search(r"\s500(?:\s|$)", line) is not None
        for line in lines
    )
    exceptions: list[dict[str, str]] = []
    frames: list[dict[str, object]] = []
    seen_frames: set[tuple[str, int, str]] = set()

    for raw in lines:
        frame = FRAME.search(raw)
        if frame:
            path = frame.group("path")
            if "/app/" in path or "ai_platform/" in path:
                key = (path, int(frame.group("line")), frame.group("function"))
                if key not in seen_frames:
                    seen_frames.add(key)
                    frames.append(
                        {
                            "path": path,
                            "line": key[1],
                            "function": key[2],
                        }
                    )

        match = EXCEPTION.search(raw)
        if match:
            exception = {
                "type": match.group("type"),
                "message": _sanitize(match.group("message")),
            }
            if not exceptions or exceptions[-1] != exception:
                exceptions.append(exception)

    return {
        "callback_500_count": callback_500_count,
        "exceptions": exceptions[-12:],
        "frames": frames[-40:],
        "latest_exception": exceptions[-1] if exceptions else None,
    }


def _database_snapshot() -> dict[str, Any]:
    code = r"""
import json
import os
from sqlalchemy import func, select
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.identity.models import (
    IdentityAuditEventRow,
    IdentityPrincipalRow,
    OidcLoginFlowRow,
    PortalSessionRow,
    TenantMembershipRow,
)

engine = build_engine(os.environ["PORTAL_DATABASE_URL"])
factory = build_session_factory(engine)
with factory() as session:
    latest_flow = session.scalars(
        select(OidcLoginFlowRow).order_by(OidcLoginFlowRow.created_at.desc()).limit(1)
    ).first()
    latest_audit = session.scalars(
        select(IdentityAuditEventRow)
        .order_by(IdentityAuditEventRow.occurred_at.desc())
        .limit(1)
    ).first()
    payload = {
        "flow_count": session.scalar(select(func.count()).select_from(OidcLoginFlowRow)),
        "principal_count": session.scalar(
            select(func.count()).select_from(IdentityPrincipalRow)
        ),
        "membership_count": session.scalar(
            select(func.count()).select_from(TenantMembershipRow)
        ),
        "session_count": session.scalar(select(func.count()).select_from(PortalSessionRow)),
        "latest_flow_present": latest_flow is not None,
        "latest_flow_consumed": (
            latest_flow is not None and latest_flow.consumed_at is not None
        ),
        "latest_audit_action": latest_audit.action if latest_audit else None,
        "latest_audit_result": latest_audit.result if latest_audit else None,
        "latest_audit_reason": latest_audit.reason if latest_audit else None,
    }
print("__PORTAL_CALLBACK_DIAGNOSTIC__" + json.dumps(payload, sort_keys=True))
""".strip()
    result = _run(["docker", "exec", CONTROL_CONTAINER, "python", "-c", code])
    marker = next(
        (
            line.removeprefix("__PORTAL_CALLBACK_DIAGNOSTIC__")
            for line in result.stdout.splitlines()
            if line.startswith("__PORTAL_CALLBACK_DIAGNOSTIC__")
        ),
        None,
    )
    if marker is None:
        raise DiagnosticError("database diagnostic did not return its marker")
    payload = json.loads(marker)
    payload["latest_audit_reason"] = _sanitize(str(payload.get("latest_audit_reason") or ""))
    return payload


def _write_report(path: Path, report: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def diagnose(args: argparse.Namespace) -> int:
    report: dict[str, Any] = {
        "schema_version": 1,
        "request_id": REQUEST_ID,
        "implementation_sha": args.expected_repository_sha,
        "status": "failed",
        "diagnostic_only": True,
        "configuration_mutation_authorized": False,
        "browser_acceptance_authorized": False,
        "public_ingress_authorized": True,
        "restore_authorized": False,
        "secret_values_recorded": False,
        "live_capital_authorized": False,
    }
    return_code = 1
    try:
        request = _load_request(Path(args.request).resolve(), args.expected_repository_sha)
        since_minutes = int(request["since_minutes"])
        control_logs = _logs(CONTROL_CONTAINER, since_minutes)
        web_logs = _logs(WEB_CONTAINER, since_minutes)
        callback = _extract_callback_failure(control_logs)
        web_callback = _extract_callback_failure(web_logs)
        report.update(
            {
                "status": "success",
                "containers": {
                    "control_plane": _container_state(CONTROL_CONTAINER),
                    "web": _container_state(WEB_CONTAINER),
                },
                "callback": callback,
                "web_callback": web_callback,
                "database": _database_snapshot(),
            }
        )
        if callback["callback_500_count"] < 1:
            raise DiagnosticError("no control-plane callback HTTP 500 was observed")
        if callback["latest_exception"] is None:
            raise DiagnosticError("no sanitized control-plane exception was observed")
        return_code = 0
    except Exception as exc:
        report["failure"] = {
            "type": type(exc).__name__,
            "message": _sanitize(str(exc)),
        }
    digest = _write_report(Path(args.report).resolve(), report)
    print(
        json.dumps(
            {
                "report": str(Path(args.report).resolve()),
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
    return diagnose(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
