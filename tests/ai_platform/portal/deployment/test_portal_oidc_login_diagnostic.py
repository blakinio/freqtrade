from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DIAGNOSTIC_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "diagnose_login_failure.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "portal-oidc-login-diagnostic.yml"
SPEC = importlib.util.spec_from_file_location(
    "portal_oidc_login_diagnostic",
    DIAGNOSTIC_PATH,
)
assert SPEC and SPEC.loader
diagnostic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diagnostic)


def test_extractor_keeps_only_sanitized_login_exception_evidence() -> None:
    logs = """
INFO: "GET /v1/identity/login?return_to=%2F HTTP/1.1" 500
Traceback (most recent call last):
  File "/app/ai_platform/portal/identity/service.py", line 104, in begin_login
    session.commit()
  File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
sqlalchemy.exc.OperationalError: database is locked state=secret-state
"""

    payload = diagnostic._extract_login_failure(logs)

    assert payload["login_500_count"] == 1
    assert payload["latest_exception"] == {
        "type": "sqlalchemy.exc.OperationalError",
        "message": "database is locked state=<redacted>",
    }
    assert payload["frames"] == [
        {
            "path": "/app/ai_platform/portal/identity/service.py",
            "line": 104,
            "function": "begin_login",
        }
    ]
    assert "secret-state" not in repr(payload)


def test_extractor_ignores_non_login_500() -> None:
    logs = 'INFO: "GET /v1/identity/callback?code=secret HTTP/1.1" 500\n'

    payload = diagnostic._extract_login_failure(logs)

    assert payload["login_500_count"] == 0


def test_workflow_is_request_only_and_secret_free() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "login-diagnostic-20260802-v1.json" in workflow
    assert "must add exactly one frozen request file" in workflow
    assert "diagnostic_only" in workflow
    assert "configuration_mutation_authorized" in workflow
    assert "secret_values_in_request" in workflow
    assert "secret_values_recorded" in workflow
    assert "live_capital_authorized" in workflow
    assert "diagnose_login_failure.py" in workflow
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in workflow
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in workflow
    assert "docker logs" not in workflow
    assert "code=" not in workflow
    assert "state=" not in workflow
