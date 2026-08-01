from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DIAGNOSTIC_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "diagnose_callback_failure.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "portal-oidc-callback-diagnostic.yml"
SPEC = importlib.util.spec_from_file_location(
    "portal_oidc_callback_diagnostic",
    DIAGNOSTIC_PATH,
)
assert SPEC and SPEC.loader
diagnostic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diagnostic)


def test_sanitizer_removes_callback_and_header_secrets() -> None:
    source = (
        "GET /v1/identity/callback?code=9830e4f51e7a42a6b70563a879ea9343"
        "&state=Nz0Rn0sVcURvBfR_kNnemzQT-e-ga5hM81j8EzWz39Y "
        "client_secret=super-secret Authorization: Bearer abc.def.ghi"
    )

    sanitized = diagnostic._sanitize(source)

    assert "9830e4f51e7a42a6b70563a879ea9343" not in sanitized
    assert "Nz0Rn0sVcURvBfR_kNnemzQT-e-ga5hM81j8EzWz39Y" not in sanitized
    assert "super-secret" not in sanitized
    assert "abc.def.ghi" not in sanitized
    assert "code=<redacted>" in sanitized
    assert "state=<redacted>" in sanitized


def test_extractor_keeps_only_sanitized_exception_evidence() -> None:
    logs = """
INFO: "GET /v1/identity/callback?code=secret-code&state=secret-state HTTP/1.1" 500
Traceback (most recent call last):
  File "/app/ai_platform/portal/identity/service.py", line 133, in complete_login
    identity = self._oidc.exchange_code(...)
  File "/usr/local/lib/python3.12/site-packages/jwt/api_jwt.py", line 250, in decode
jwt.exceptions.MissingRequiredClaimError: Token is missing the "nonce" claim
"""

    payload = diagnostic._extract_callback_failure(logs)

    assert payload["callback_500_count"] == 1
    assert payload["latest_exception"] == {
        "type": "jwt.exceptions.MissingRequiredClaimError",
        "message": 'Token is missing the "nonce" claim',
    }
    assert payload["frames"] == [
        {
            "path": "/app/ai_platform/portal/identity/service.py",
            "line": 133,
            "function": "complete_login",
        }
    ]
    encoded = repr(payload)
    assert "secret-code" not in encoded
    assert "secret-state" not in encoded


def test_workflow_is_request_only_and_secret_free() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "callback-diagnostic-20260801-v1.json" in workflow
    assert "must add exactly one frozen request file" in workflow
    assert "diagnostic_only" in workflow
    assert "configuration_mutation_authorized" in workflow
    assert "secret_values_in_request" in workflow
    assert "secret_values_recorded" in workflow
    assert "live_capital_authorized" in workflow
    assert "diagnose_callback_failure.py" in workflow
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in workflow
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in workflow
    assert "docker logs" not in workflow
    assert "code=" not in workflow
    assert "state=" not in workflow
