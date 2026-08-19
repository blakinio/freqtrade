from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/portal-wickhunter-wh09-deployed-browser.yml"
BROWSER = ROOT / "ai_platform/portal/web/e2e/wickhunter-api-mode-ci.mjs"
BOTS_PAGE = ROOT / "ai_platform/portal/web/app/bots/page.tsx"


def test_deployed_browser_acceptance_is_one_shot_and_post_adoption() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_run:" not in workflow
    assert "push:" in workflow
    assert "actions: read" in workflow
    assert "Wait for exact Portal adoption success" in workflow
    assert "portal-wickhunter-wh09-adoption.yml/runs" in workflow
    assert "wickhunter-wh09-portal-adoption-20260819-v2.json" in workflow
    assert 'git cat-file -e "$AUTHORIZATION_SHA^:$REQUEST_PATH"' in workflow
    assert (
        "deployed-browser acceptance is not bound to a newly introduced one-shot request"
        in workflow
    )


def test_deployed_browser_session_has_read_only_authority_and_bounded_lifetime() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "PORTAL_WH09_ACCEPTANCE_SESSION_TOKEN" in workflow
    assert "roles=(RoleName.USER,)" in workflow
    assert "timedelta(minutes=15)" in workflow
    assert workflow.count("timedelta(minutes=30)") >= 2
    for forbidden in (
        "RoleName.TRADER",
        "RoleName.ANALYST",
        "RoleName.MODEL_REVIEWER",
        "RoleName.ADMIN",
    ):
        assert forbidden not in workflow
    assert '"execution_enabled": False' in workflow
    assert '"orders_submitted": 0' in workflow
    assert '"live_capital_authorized": False' in workflow


def test_deployed_browser_proves_real_api_mode_public_wickhunter_truth() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    browser = BROWSER.read_text(encoding="utf-8")
    bots_page = BOTS_PAGE.read_text(encoding="utf-8")

    assert "https://quant.molehill.cloud" in workflow
    assert '"PORTAL_WEB_DATA_MODE=api"' in workflow
    assert '"PORTAL_IDENTITY_FIXTURE_MODE=disabled"' in workflow
    assert "runs-on: ubuntu-24.04" in workflow
    assert "command -v google-chrome" in workflow
    assert "node e2e/wickhunter-api-mode-ci.mjs" in workflow
    assert "WICKHUNTER_SESSION_TOKEN" in browser
    assert "WICKHUNTER_BROWSER_EXECUTABLE_PATH" in browser
    assert "portal_fixture_" in browser
    assert r"Decisions: (\d+) · NO_TRADE: (\d+)" in browser
    assert "WICKHUNTER_BROWSER_EVIDENCE_PATH" in browser
    assert "Decisions: {runtime.decision_count} · NO_TRADE: {runtime.no_trade_count}" in bots_page
    assert 'WICKHUNTER_CSRF_TOKEN="${PORTAL_WH09_ACCEPTANCE_SESSION_TOKEN}:csrf"' in workflow


def test_deployed_browser_cleanup_is_exact_and_fail_closed() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    cleanup = workflow.split("cleanup-session:", 1)[1]

    assert "if: always()" in cleanup
    assert "PortalSessionRow" in cleanup
    assert "TenantMembershipRow" in cleanup
    assert "IdentityPrincipalRow" in cleanup
    assert "refusing to remove non-task-owned Portal session" in cleanup
    assert "refusing to remove non-task-owned membership" in cleanup
    assert "refusing to remove non-task-owned principal" in cleanup
    assert '[[ "$SEED_RESULT" == "success" ]]' in cleanup
    assert '[[ "$BROWSER_RESULT" == "success" ]]' in cleanup
