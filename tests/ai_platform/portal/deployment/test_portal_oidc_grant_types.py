from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT_PATH = (
    ROOT / "deploy" / "synology" / "portal-oidc" / "verify_provider_grant_types.py"
)
BLUEPRINT_PATH = (
    ROOT
    / "deploy"
    / "synology"
    / "portal-oidc"
    / "blueprints"
    / "freqtrade-portal-public.yaml"
)
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "portal-oidc-public-deploy.yml"
SPEC = importlib.util.spec_from_file_location("portal_oidc_grant_types", SCRIPT_PATH)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def test_blueprint_enables_only_authorization_code_grant() -> None:
    blueprint = BLUEPRINT_PATH.read_text(encoding="utf-8")

    assert "      grant_types:\n        - authorization_code\n" in blueprint
    grant_section = blueprint.split("      grant_types:\n", maxsplit=1)[1].split(
        "      authorization_flow:", maxsplit=1
    )[0]
    assert "implicit" not in grant_section
    assert "password" not in grant_section
    assert "client_credentials" not in grant_section
    assert "refresh_token" not in grant_section


def test_query_requires_exact_authorization_code_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result_payload = {
        "name": verifier.AUTHENTIK_PROVIDER_NAME,
        "client_id": verifier.CLIENT_ID,
        "grant_types": ["authorization_code"],
    }

    def fake_run(
        command: list[str],
        *,
        sensitive: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        del sensitive, check
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=verifier.MARKER + json.dumps(result_payload),
            stderr="",
        )

    monkeypatch.setattr(verifier, "_run", fake_run)

    assert verifier._query_grant_types("authentik-server") == result_payload

    result_payload["grant_types"] = ["authorization_code", "implicit"]
    with pytest.raises(
        verifier.GrantTypeVerificationError,
        match="authorization-code-only",
    ):
        verifier._query_grant_types("authentik-server")


def test_report_records_target_side_grant_evidence(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "success",
                "authentik": {"provider_exists": True},
                "secret_values_recorded": False,
                "live_capital_authorized": False,
            }
        ),
        encoding="utf-8",
    )

    report = verifier._augment_report(
        report_path,
        {
            "name": verifier.AUTHENTIK_PROVIDER_NAME,
            "client_id": verifier.CLIENT_ID,
            "grant_types": ["authorization_code"],
        },
    )

    assert report["authentik"]["grant_types"] == ["authorization_code"]
    assert report["authentik"]["authorization_code_enabled"] is True
    assert report["authentik"]["legacy_grants_disabled"] is True
    assert report["secret_values_recorded"] is False
    assert report["live_capital_authorized"] is False
    assert report_path.stat().st_mode & 0o777 == 0o600


def test_workflow_verifies_and_enforces_grant_types() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Verify authorization-code-only Authentik provider" in workflow
    assert "verify_provider_grant_types.py" in workflow
    assert "GRANT_TYPES_OUTCOME" in workflow
    assert 'authentik.get("grant_types") != ["authorization_code"]' in workflow
    assert 'authentik.get("legacy_grants_disabled") is not True' in workflow
