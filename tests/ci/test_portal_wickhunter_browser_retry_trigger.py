from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/portal-wickhunter-wh09-browser-retry-trigger.yml"
REQUEST = ROOT / (
    "deploy/synology/portal-oidc/run-requests/wickhunter-wh09-browser-acceptance-20260820-v4.json"
)
BROWSER = ROOT / "ai_platform/portal/web/e2e/wickhunter-api-mode-ci.mjs"
TARGET = "eafc198857c90caf89a5920da60ae7661c1061ba"


def test_v4_is_one_shot_dual_provenance_browser_only() -> None:
    w = WORKFLOW.read_text()
    assert 'git cat-file -e "$GITHUB_SHA^:$REQUEST_PATH"' in w
    assert "browser-only v4 request is not newly introduced one-shot material" in w
    assert "harness_source_sha" in w and "target_authorization_sha" in w
    assert '[[ "$GITHUB_SHA" == "$HARNESS_SHA" ]]' in w
    assert "docker restart" not in w and "docker compose" not in w
    assert "Real authenticated Chromium v4 against deployed Portal" in w


def test_v4_request_preserves_zero_authority() -> None:
    p = json.loads(REQUEST.read_text())
    assert p["schema_version"] == 4
    assert p["target_authorization_sha"] == TARGET
    assert p["session_token_format"] == "urlsafe"
    assert p["browser_only"] is True
    assert p["portal_deploy_authorized"] is False
    assert p["wh09_redeploy_authorized"] is False
    assert p["paper_activation_authorized"] is False
    assert p["trading_credentials_present"] is False
    assert p["order_adapter_present"] is False
    assert p["execution_enabled"] is False
    assert p["orders_submitted"] == 0
    assert p["live_capital_authorized"] is False


def test_v4_helper_schema_and_bounded_health_convergence_match() -> None:
    w = WORKFLOW.read_text()
    assert '"schema_version":4' in w
    assert 'a.get("schema_version") != 4' in w
    assert "for attempt in range(181):" in w
    assert "if attempt<180: time.sleep(5)" in w
    assert "timeout-minutes: 50" in w


def test_v4_session_is_production_format_read_only_and_exact_cleanup() -> None:
    w = WORKFLOW.read_text()
    assert "secrets.token_urlsafe(48)" in w
    assert "roles=(RoleName.USER,)" in w
    assert "refusing non-task session cleanup" in w
    assert "refusing non-task membership cleanup" in w
    assert "refusing non-task principal cleanup" in w
    assert 'docker rm -f "$browser_name"' in w
    assert 'docker image rm "$BROWSER_IMAGE"' in w


def test_v4_browser_evidence_requires_real_visible_truth() -> None:
    w = WORKFLOW.read_text()
    b = BROWSER.read_text()
    assert "https://quant.molehill.cloud" in w
    assert "PORTAL_WEB_DATA_MODE=api" in w
    assert "PORTAL_IDENTITY_FIXTURE_MODE=disabled" in w
    assert "fixture_cookie_present" in w
    assert "runtime_generation_converged" in w
    assert "reload_persistence" in w
    assert "decision_count" in w and "no_trade_count" in w
    assert "trading_credentials_present" in w and "orders_submitted" in w
    assert 'const expectedBotsUrl = new URL("/bots", origin).toString()' in b
    assert "portal_fixture_" in b
