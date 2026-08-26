import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/portal-wickhunter-wh09-browser-retry-trigger.yml"
REQUEST = (
    ROOT
    / "deploy/synology/portal-oidc/run-requests/wickhunter-wh09-browser-acceptance-20260826-v7.json"
)
SCRIPT = ROOT / "deploy/synology/portal-oidc/wickhunter-browser-accept-v6.sh"
BROWSER = ROOT / "ai_platform/portal/web/e2e/wickhunter-api-mode-ci.mjs"
TARGET = "eafc198857c90caf89a5920da60ae7661c1061ba"


def test_v7_is_one_shot_and_dual_provenance() -> None:
    w = WORKFLOW.read_text(encoding="utf-8")
    assert 'git cat-file -e "$GITHUB_SHA^:$REQUEST_PATH"' in w
    assert "browser-only v7 request is not newly introduced one-shot material" in w
    assert '"schema_version":3' in w
    assert 'a.get("schema_version")!=3' in w
    assert "harness_source_sha" in w and "target_authorization_sha" in w
    assert "accept_script_sha256" in w
    assert "org.opencontainers.image.revision=$HARNESS_SHA" in w
    assert "ftai.target_authorization_sha=$TARGET_AUTHORIZATION_SHA" in w
    assert '[[ "$GITHUB_SHA" == "$HARNESS_SHA" ]]' in w
    assert 'bash "$RUNNER_TEMP/portal-wh09-browser-image/accept.sh"' in w
    assert "docker restart" not in w and "docker compose" not in w


def test_v7_request_is_zero_authority() -> None:
    p = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert p["request_id"].endswith("20260826-v7")
    assert p["target_authorization_sha"] == TARGET
    assert p["adoption_run_id"] == 32373954360
    assert p["session_token_format"] == "urlsafe"
    assert p["browser_only"] is True
    for key in (
        "portal_deploy_authorized",
        "wh09_redeploy_authorized",
        "paper_activation_authorized",
        "trading_credentials_present",
        "order_adapter_present",
        "execution_enabled",
        "live_capital_authorized",
    ):
        assert p[key] is False
    assert p["orders_submitted"] == 0


def test_v6_script_binds_browser_to_canonical_runtime_contract() -> None:
    s = SCRIPT.read_text(encoding="utf-8")
    assert "secrets.token_urlsafe(48)" in s
    assert "RoleName.USER" in s
    assert 'observed.get("model_version")' in s
    assert 'observed.get("managed_mode")=="shadow"' in s
    assert 'desired.get("generation_id")==observed.get("generation_id")' in s
    assert 'WICKHUNTER_EXPECTED_MODEL_VERSION="$expected_model_version"' in s
    assert 'WICKHUNTER_EXPECTED_DESIRED_GENERATION="$expected_desired_generation"' in s
    assert 'WICKHUNTER_EXPECTED_OBSERVED_GENERATION="$expected_observed_generation"' in s
    assert "trading_credentials_present" in s and "order_adapter_present" in s
    assert "execution_enabled" in s and "orders_submitted" in s and "live_capital_authorized" in s
    assert "refusing non-task session cleanup" in s
    assert "refusing non-task membership cleanup" in s
    assert "refusing non-task principal cleanup" in s
    assert "WICKHUNTER_EVIDENCE=" in BROWSER.read_text(encoding="utf-8")
    assert "docker restart" not in s and "docker compose" not in s


def test_browser_harness_keeps_meaningful_content_checks() -> None:
    b = BROWSER.read_text(encoding="utf-8")
    assert 'const expectedBotsUrl = new URL("/bots", origin).toString()' in b
    assert "finalUrl === expectedBotsUrl" in b
    assert "missing_visible_markers" in b
    assert "portal_fixture_" in b
    assert "Live capital: false" in b
    assert r"Decisions: (\d+) · NO_TRADE: (\d+)" in b
    assert "WICKHUNTER_EXPECTED_MODEL_VERSION" in b
    assert "WICKHUNTER_EXPECTED_DESIRED_GENERATION" in b
    assert "WICKHUNTER_EXPECTED_OBSERVED_GENERATION" in b
    assert "const expectedModeModelMarker" in b
    assert "expectedModeModelMarker" in b


def test_browser_harness_waits_for_rendered_truth_without_network_idle() -> None:
    b = BROWSER.read_text(encoding="utf-8")
    assert 'waitUntil: "domcontentloaded"' in b
    assert 'waitUntil: "networkidle"' not in b
    assert "const visibleTruthTimeoutMs = 10000" in b
    assert "const visibleTruthPollMs = 250" in b
    assert "const waitForVisibleTruth = async" in b
    assert "snapshot = await waitForVisibleTruth(page, response)" in b
