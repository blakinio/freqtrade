import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = ROOT / ".github/workflows"
WORKFLOW = WORKFLOW_DIR / "portal-wickhunter-wh09-browser-retry-trigger.yml"
REQUEST_DIR = ROOT / "deploy/synology/portal-oidc/run-requests"
REQUEST = REQUEST_DIR / "wickhunter-wh09-browser-acceptance-20260820-v1.json"
AUTHORIZATION_SHA = "eafc198857c90caf89a5920da60ae7661c1061ba"
ADOPTION_RUN_ID = 32373954360


def test_browser_retry_trigger_is_one_shot_and_dispatch_only() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "actions: write" in workflow
    assert 'git cat-file -e "$GITHUB_SHA^:$REQUEST_PATH"' in workflow
    assert "browser-only retry request is not newly introduced one-shot material" in workflow
    assert 'gh workflow run "$BROWSER_WORKFLOW"' in workflow
    assert '--field "authorization_sha=$AUTHORIZATION_SHA"' in workflow
    assert "portal-wickhunter-wh09-deployed-browser.yml" in workflow
    assert "wickhunter-wh09-portal-adoption-20260820-v4.json" not in workflow
    assert "docker restart" not in workflow
    assert "docker compose" not in workflow


def test_browser_retry_request_cannot_authorize_runtime_mutation() -> None:
    payload = json.loads(REQUEST.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["authorization_sha"] == AUTHORIZATION_SHA
    assert payload["adoption_run_id"] == ADOPTION_RUN_ID
    assert payload["browser_only"] is True
    assert payload["runtime_e2e_required"] is True
    assert payload["portal_deploy_authorized"] is False
    assert payload["wh09_redeploy_authorized"] is False
    assert payload["paper_activation_authorized"] is False
    assert payload["trading_credentials_present"] is False
    assert payload["order_adapter_present"] is False
    assert payload["execution_enabled"] is False
    assert payload["orders_submitted"] == 0
    assert payload["live_capital_authorized"] is False


def test_browser_retry_trigger_binds_to_accepted_v4_adoption() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert f"AUTHORIZATION_SHA: {AUTHORIZATION_SHA}" in workflow
    assert f'ADOPTION_RUN_ID: "{ADOPTION_RUN_ID}"' in workflow
    assert "actions/runs/$ADOPTION_RUN_ID" in workflow
    assert '[[ "${adoption[3]}" == "$AUTHORIZATION_SHA" ]]' in workflow
    assert '[[ "${adoption[5]}" == "success" ]]' in workflow
