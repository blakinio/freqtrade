from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/portal-wickhunter-wh09-deployed-browser.yml"
BROWSER = ROOT / "ai_platform/portal/web/e2e/wickhunter-api-mode-ci.mjs"
BOTS_PAGE = ROOT / "ai_platform/portal/web/app/bots/page.tsx"
BROWSER_DOCKERFILE = ROOT / "deploy/synology/portal-oidc/Dockerfile.wickhunter-browser"


def test_deployed_browser_acceptance_is_one_shot_and_post_adoption() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_run:" not in workflow
    assert "push:" in workflow
    assert "actions: read" in workflow
    assert "Wait for exact Portal adoption success" in workflow
    assert "portal-wickhunter-wh09-adoption.yml/runs" in workflow
    assert "wickhunter-wh09-portal-adoption-20260820-v4.json" in workflow
    assert 'git cat-file -e "$AUTHORIZATION_SHA^:$REQUEST_PATH"' in workflow
    assert (
        "deployed-browser acceptance is not bound to a newly introduced one-shot request"
        in workflow
    )


def test_deployed_browser_helper_is_exact_and_disposable() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    dockerfile = BROWSER_DOCKERFILE.read_text(encoding="utf-8")

    assert "Dockerfile.wickhunter-browser" in workflow
    assert "org.opencontainers.image.revision=$AUTHORIZATION_SHA" in workflow
    assert '"tar_sha256": sys.argv[4]' in workflow
    assert '"persistent_runtime": False' in workflow
    assert "retention-days: 1" in workflow
    assert 'docker image rm "$BROWSER_IMAGE"' in workflow
    assert (
        "node:22.23.1-bookworm-slim@sha256:6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3"
        in dockerfile
    )
    assert "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1" in dockerfile
    assert "chromium" in dockerfile
    assert "USER node" in dockerfile


def test_deployed_browser_session_has_read_only_authority_and_bounded_lifetime() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "secrets.PORTAL_WH09_ACCEPTANCE_SESSION_TOKEN" not in workflow
    assert "openssl rand -base64 48" in workflow
    assert "::add-mask::$session_token" in workflow
    assert "roles=(RoleName.USER,)" in workflow
    assert "timedelta(minutes=15)" in workflow
    assert workflow.count("timedelta(minutes=30)") >= 2
    assert "acceptance_key=" in workflow
    assert 'principal_id="wh09-p-${acceptance_key}"' in workflow
    assert 'membership_id="wh09-m-${acceptance_key}"' in workflow
    assert '[[ ${#principal_id} -le 36 ]]' in workflow
    assert '[[ ${#membership_id} -le 36 ]]' in workflow
    assert 'membership_id="wh09-browser-membership-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"' not in workflow
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
    assert "freqtrade-staging" in workflow
    assert "WICKHUNTER_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium" in workflow
    assert "WICKHUNTER_BROWSER_NO_SANDBOX=1" in workflow
    assert "WICKHUNTER_BROWSER_NO_SANDBOX" in browser
    assert "WICKHUNTER_SESSION_TOKEN" in browser
    assert "WICKHUNTER_BROWSER_EXECUTABLE_PATH" in browser
    assert "portal_fixture_" in browser
    assert r"Decisions: (\d+) · NO_TRADE: (\d+)" in browser
    assert "WICKHUNTER_BROWSER_EVIDENCE_PATH" in browser
    assert "Decisions: {runtime.decision_count} · NO_TRADE: {runtime.no_trade_count}" in bots_page
    assert 'WICKHUNTER_CSRF_TOKEN="${session_token}:csrf"' in workflow


def test_deployed_browser_cleanup_is_exact_and_fail_closed() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "PortalSessionRow" in workflow
    assert "TenantMembershipRow" in workflow
    assert "IdentityPrincipalRow" in workflow
    assert "refusing to remove non-task-owned Portal session" in workflow
    assert "refusing to remove non-task-owned membership" in workflow
    assert "refusing to remove non-task-owned principal" in workflow
    assert 'rm -f "$token_file"' in workflow
    assert 'if docker inspect "$browser_name"' in workflow
    assert 'docker rm -f "$browser_name"' in workflow
    assert 'if docker image inspect "$BROWSER_IMAGE"' in workflow
    assert '[[ "$cleanup_rc" -eq 0 ]]' in workflow
    assert '[[ "$resource_cleanup_rc" -eq 0 ]]' in workflow
    assert '[[ "$browser_rc" -eq 0 ]]' in workflow
    assert "if docker create" in workflow
