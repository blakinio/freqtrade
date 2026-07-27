from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SCRIPT = REPO_ROOT / "deploy" / "synology" / "portal" / "deploy-preview.sh"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "portal-synology-lan-preview.yml"


def test_deploy_probe_requires_page_and_protected_api_boundary() -> None:
    script = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert 'fetch("http://127.0.0.1:3000/market/liquidations")' in script
    assert 'response.status !== 401 || payload?.code !== "SESSION_MISSING"' in script
    assert (
        'wait_http "$bind_address" "$portal_port" "/api/market/liquidations/health"'
        not in script
    )
    assert "authenticated Liquid20 boundary" in script


def test_workflow_does_not_require_unauthenticated_api_success() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "Verify LAN Liquid20 surface and session boundary" in workflow
    assert (
        'response.status !== 401 || payload?.code !== "SESSION_MISSING"' in workflow
    )
    assert '"http://192.168.1.2:3031/market/liquidations"' in workflow
    assert "if (!response.ok) process.exit(1);" not in workflow
