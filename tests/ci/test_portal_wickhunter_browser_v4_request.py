import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUEST = ROOT / "deploy/synology/portal-oidc/run-requests/wickhunter-wh09-browser-acceptance-20260820-v4.json"
WORKFLOW = ROOT / ".github/workflows/portal-wickhunter-wh09-browser-retry-trigger.yml"


def test_v4_request_is_zero_authority() -> None:
    payload = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert payload["request_id"] == "wickhunter-wh09-browser-acceptance-20260820-v4"
    assert payload["target_authorization_sha"] == "eafc198857c90caf89a5920da60ae7661c1061ba"
    assert payload["adoption_run_id"] == 32373954360
    assert payload["browser_only"] is True
    assert payload["portal_deploy_authorized"] is False
    assert payload["wh09_redeploy_authorized"] is False
    assert payload["paper_activation_authorized"] is False
    assert payload["trading_credentials_present"] is False
    assert payload["order_adapter_present"] is False
    assert payload["execution_enabled"] is False
    assert payload["orders_submitted"] == 0
    assert payload["live_capital_authorized"] is False


def test_helper_approval_schema_is_consistent() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert '"schema_version": 3' in workflow
    assert 'approval.get("schema_version") != 3' in workflow
    assert "20260820-v4.json" in workflow
