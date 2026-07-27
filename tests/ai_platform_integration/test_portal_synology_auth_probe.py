from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SCRIPT = REPO_ROOT / "deploy" / "synology" / "portal" / "deploy-preview.sh"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "portal-synology-lan-preview.yml"


def test_deploy_probe_requires_page_and_protected_api_boundary() -> None:
    script = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert 'fetch("http://127.0.0.1:3000/market/liquidations")' in script
    assert 'response.status !== 401 || payload?.code !== "SESSION_MISSING"' in script
    assert (
        'wait_http "$bind_address" "$portal_port" "/api/market/liquidations/health"' not in script
    )
    assert "authenticated Liquid20 boundary" in script


def test_deploy_enables_and_verifies_bounded_fixture_identity() -> None:
    script = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert "--env PORTAL_WEB_DATA_MODE=fixture" in script
    assert "--env PORTAL_ENVIRONMENT=test" in script
    assert "--env PORTAL_IDENTITY_FIXTURE_MODE=enabled" in script
    assert "--env PORTAL_CONTROL_PLANE_URL" not in script
    assert "wait_fixture_identity_internal" in script
    assert "/api/identity/login?return_to=%2Fplatform%2Fadmin" in script
    assert "login.status !== 303" in script
    assert "session.status !== 200" in script
    assert "admin.status !== 200" in script
    assert "Fixture preview must not declare a control-plane URL" in script
    assert "real Authentik/control plane remains disabled" in script


def test_workflow_verifies_liquidations_and_fixture_identity() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "Verify LAN Liquid20 surface and fixture identity boundary" in workflow
    assert 'response.status !== 401 || payload?.code !== "SESSION_MISSING"' in workflow
    assert '"http://192.168.1.2:3031/market/liquidations"' in workflow
    assert "/api/identity/login?return_to=%2Fplatform%2Fadmin" in workflow
    assert "login.status !== 303" in workflow
    assert "session.status !== 200" in workflow
    assert "admin.status !== 200" in workflow
    assert "fixture-identity-probe" in workflow
    assert "if (!response.ok) process.exit(1);" not in workflow
