import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/portal-wickhunter-wh09-browser-retry-trigger.yml"
REQUEST = ROOT / (
    "deploy/synology/portal-oidc/run-requests/wickhunter-wh09-browser-acceptance-20260820-v2.json"
)
BROWSER = ROOT / "ai_platform/portal/web/e2e/wickhunter-api-mode-ci.mjs"
TARGET_AUTHORIZATION_SHA = "eafc198857c90caf89a5920da60ae7661c1061ba"
ADOPTION_RUN_ID = 32373954360


def test_browser_v2_is_one_shot_and_dual_provenance() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'git cat-file -e "$GITHUB_SHA^:$REQUEST_PATH"' in workflow
    assert "browser-only v2 request is not newly introduced one-shot material" in workflow
    assert "harness_sha=%s" in workflow
    assert "harness_source_sha" in workflow
    assert "target_authorization_sha" in workflow
    assert "ftai.target_authorization_sha" in workflow
    assert "org.opencontainers.image.revision=$HARNESS_SHA" in workflow
    assert "portal-wh09-deployed-browser-v2" in workflow
    assert "gh workflow run" not in workflow
    assert "docker restart" not in workflow
    assert "docker compose" not in workflow


def test_browser_v2_request_cannot_authorize_runtime_mutation() -> None:
    payload = json.loads(REQUEST.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 2
    assert payload["target_authorization_sha"] == TARGET_AUTHORIZATION_SHA
    assert payload["harness_source"] == "trigger_merge_sha"
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


def test_browser_v2_binds_to_accepted_v4_target_without_redeployment() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert f"TARGET_AUTHORIZATION_SHA: {TARGET_AUTHORIZATION_SHA}" in workflow
    assert f'ADOPTION_RUN_ID: "{ADOPTION_RUN_ID}"' in workflow
    assert "actions/runs/$ADOPTION_RUN_ID" in workflow
    assert '[[ "${adoption[3]}" == "$TARGET_AUTHORIZATION_SHA" ]]' in workflow
    assert '[[ "${adoption[5]}" == "success" ]]' in workflow
    assert 'control_revision" == "$TARGET_AUTHORIZATION_SHA"' in workflow
    assert 'web_revision" == "$TARGET_AUTHORIZATION_SHA"' in workflow


def test_browser_v2_keeps_zero_authority_and_exact_cleanup() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "roles=(RoleName.USER,)" in workflow
    assert 'principal_id="wh09-vp-${acceptance_key}"' in workflow
    assert 'membership_id="wh09-vm-${acceptance_key}"' in workflow
    assert "[[ ${#principal_id} -le 36 ]]" in workflow
    assert "[[ ${#membership_id} -le 36 ]]" in workflow
    assert "refusing to remove non-task-owned Portal session" in workflow
    assert "refusing to remove non-task-owned membership" in workflow
    assert "refusing to remove non-task-owned principal" in workflow
    assert '[[ "$cleanup_rc" -eq 0 ]]' in workflow
    assert '[[ "$resource_cleanup_rc" -eq 0 ]]' in workflow
    assert '[[ "$browser_rc" -eq 0 ]]' in workflow
    assert '"execution_enabled": False' in workflow
    assert '"orders_submitted": 0' in workflow
    assert '"live_capital_authorized": False' in workflow


def test_browser_harness_uses_bounded_content_convergence() -> None:
    browser = BROWSER.read_text(encoding="utf-8")

    assert "page.goto(`${origin}/bots`" in browser
    assert 'new URL(page.url()).pathname !== "/bots"' in browser
    assert 'page.locator("body").innerText()' in browser
    assert "for (let attempt = 0; attempt < 3; attempt += 1)" in browser
    assert "missing_markers" in browser
    assert "body_sha256" in browser
    assert "portal_fixture_" in browser
    assert "Execution: disabled · Orders: 0" in browser
    assert "Live capital: false" in browser
    assert r"Decisions: (\d+) · NO_TRADE: (\d+)" in browser
    assert 'getByText("WickHunter", { exact: true })' not in browser
