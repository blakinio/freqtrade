from json import loads
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/portal-wickhunter-wh09-browser-retry-trigger.yml"
REQUEST = ROOT / (
    "deploy/synology/portal-oidc/run-requests/"
    "wickhunter-wh09-browser-acceptance-20260820-v4.json"
)
SCRIPT = ROOT / "deploy/synology/portal-oidc/wickhunter-browser-accept-v4.sh"
BROWSER = ROOT / "ai_platform/portal/web/e2e/wickhunter-api-mode-ci.mjs"
TARGET = "eafc198857c90caf89a5920da60ae7661c1061ba"


def test_v4_is_one_shot_and_dual_provenance() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'git cat-file -e "$GITHUB_SHA^:$REQUEST_PATH"' in workflow
    assert "browser-only v4 request is not newly introduced one-shot material" in workflow
    assert '"schema_version":3' in workflow
    assert 'a.get("schema_version")!=3' in workflow
    assert "harness_source_sha" in workflow
    assert "target_authorization_sha" in workflow
    assert "accept_script_sha256" in workflow
    assert "org.opencontainers.image.revision=$HARNESS_SHA" in workflow
    assert "ftai.target_authorization_sha=$TARGET_AUTHORIZATION_SHA" in workflow
    assert '[[ "$GITHUB_SHA" == "$HARNESS_SHA" ]]' in workflow
    assert "docker restart" not in workflow
    assert "docker compose" not in workflow


def test_v4_request_is_zero_authority() -> None:
    payload = loads(REQUEST.read_text(encoding="utf-8"))
    assert payload["request_id"].endswith("20260820-v4")
    assert payload["target_authorization_sha"] == TARGET
    assert payload["adoption_run_id"] == 32373954360
    assert payload["session_token_format"] == "urlsafe"
    assert payload["browser_only"] is True
    false_fields = (
        "portal_deploy_authorized",
        "wh09_redeploy_authorized",
        "paper_activation_authorized",
        "trading_credentials_present",
        "order_adapter_present",
        "execution_enabled",
        "live_capital_authorized",
    )
    for key in false_fields:
        assert payload[key] is False
    assert payload["orders_submitted"] == 0


def test_v4_script_is_bounded_read_only_acceptance() -> None:
    script = SCRIPT.read_text(encoding="utf-8")
    assert "secrets.token_urlsafe(48)" in script
    assert "RoleName.USER" in script
    assert "trading_credentials_present" in script
    assert "order_adapter_present" in script
    assert "execution_enabled" in script
    assert "orders_submitted" in script
    assert "live_capital_authorized" in script
    assert "refusing non-task session cleanup" in script
    assert "refusing non-task membership cleanup" in script
    assert "refusing non-task principal cleanup" in script
    assert "docker restart" not in script
    assert "docker compose" not in script


def test_browser_harness_keeps_meaningful_content_checks() -> None:
    browser = BROWSER.read_text(encoding="utf-8")
    assert 'const expectedBotsUrl = new URL("/bots", origin).toString()' in browser
    assert "finalUrl === expectedBotsUrl" in browser
    assert "missing_visible_markers" in browser
    assert "portal_fixture_" in browser
    assert "Live capital: false" in browser
    assert r"Decisions: (\d+) · NO_TRADE: (\d+)" in browser
