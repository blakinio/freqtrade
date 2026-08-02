#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


BASE_PATH = Path(__file__).with_name("diagnose_callback_failure.py")
SPEC = importlib.util.spec_from_file_location("portal_oidc_callback_diagnostic_base", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load callback diagnostic base")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

REQUEST_RELATIVE_PATH = "deploy/synology/portal-oidc/run-requests/login-diagnostic-20260802-v1.json"
REQUEST_ID = "portal-authentik-login-diagnostic-20260802-v1"
LOGIN_PATH = "/v1/identity/login"
HTTP_500 = re.compile(r"\s500(?:\s|$)")


class DiagnosticError(RuntimeError):
    pass


def _load_request(path: Path, expected_sha: str) -> dict[str, Any]:
    if not path.as_posix().endswith(REQUEST_RELATIVE_PATH):
        raise DiagnosticError("request path does not match login diagnostic contract")
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
        raise DiagnosticError("login diagnostic request does not match frozen contract")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise DiagnosticError("implementation SHA must be a full lowercase commit SHA")
    return payload


def _extract_login_failure(logs: str) -> dict[str, Any]:
    lines = logs.splitlines()
    login_500_count = sum(
        LOGIN_PATH in line and HTTP_500.search(line) is not None for line in lines
    )
    exceptions: list[dict[str, str]] = []
    frames: list[dict[str, object]] = []
    seen_frames: set[tuple[str, int, str]] = set()

    for raw in lines:
        frame = base.FRAME.search(raw)
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

        match = base.EXCEPTION.search(raw)
        if match:
            exception = {
                "type": match.group("type"),
                "message": base._sanitize(match.group("message")),
            }
            if not exceptions or exceptions[-1] != exception:
                exceptions.append(exception)

    return {
        "login_500_count": login_500_count,
        "exceptions": exceptions[-12:],
        "frames": frames[-40:],
        "latest_exception": exceptions[-1] if exceptions else None,
    }


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
        control_logs = base._logs(base.CONTROL_CONTAINER, since_minutes)
        web_logs = base._logs(base.WEB_CONTAINER, since_minutes)
        login = _extract_login_failure(control_logs)
        web_login = _extract_login_failure(web_logs)
        report.update(
            {
                "status": "success",
                "containers": {
                    "control_plane": base._container_state(base.CONTROL_CONTAINER),
                    "web": base._container_state(base.WEB_CONTAINER),
                },
                "login": login,
                "web_login": web_login,
                "database": base._database_snapshot(),
            }
        )
        if login["login_500_count"] < 1:
            raise DiagnosticError("no control-plane login HTTP 500 was observed")
        if login["latest_exception"] is None:
            raise DiagnosticError("no sanitized control-plane exception was observed")
        return_code = 0
    except Exception as exc:
        report["failure"] = {
            "type": type(exc).__name__,
            "message": base._sanitize(str(exc)),
        }
    digest = base._write_report(Path(args.report).resolve(), report)
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
