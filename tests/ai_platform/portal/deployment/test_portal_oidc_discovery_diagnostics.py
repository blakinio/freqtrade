from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT = ROOT / "deploy" / "synology" / "portal-oidc"
WORKFLOW = ROOT / ".github" / "workflows" / "portal-oidc-public-deploy.yml"
SPEC = importlib.util.spec_from_file_location(
    "portal_oidc_discovery_diagnostics",
    DEPLOYMENT / "diagnose_discovery.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_failure_preserves_actionable_nonsensitive_discovery_error(monkeypatch) -> None:
    def fake_run(*_args, **_kwargs):
        return module.subprocess.CompletedProcess(
            args=["docker", "exec"],
            returncode=1,
            stdout="",
            stderr="urllib.error.URLError: certificate verify failed\n",
        )

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="certificate verify failed"):
        module.diagnose()


def test_success_reports_only_public_endpoint_statuses(monkeypatch) -> None:
    marker = (
        '__PORTAL_DISCOVERY_DIAGNOSTIC__{"discovery": 200, '
        '"issuer": "https://auth.molehill.cloud/application/o/freqtrade-portal/", '
        '"jwks_uri": 200}'
    )

    def fake_run(*_args, **_kwargs):
        return module.subprocess.CompletedProcess(
            args=["docker", "exec"],
            returncode=0,
            stdout=f"{marker}\n",
            stderr="",
        )

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module.diagnose() == {
        "discovery": 200,
        "issuer": module.ISSUER,
        "jwks_uri": 200,
    }


def test_workflow_runs_safe_diagnostic_only_after_deploy_failure() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    deploy_index = workflow.index("- name: Apply provider and deploy public Portal OIDC")
    diagnostic_index = workflow.index("- name: Diagnose discovery and JWKS failure safely")
    upload_index = workflow.index("- name: Upload secret-free deployment and supply-chain evidence")

    assert deploy_index < diagnostic_index < upload_index
    assert "if: steps.deploy.outcome == 'failure'" in workflow
    assert "continue-on-error: true" in workflow[diagnostic_index:upload_index]
    assert "diagnose_discovery.py" in workflow[diagnostic_index:upload_index]
