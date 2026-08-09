from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SCRIPT = REPO_ROOT / "deploy" / "synology" / "portal-oidc" / "deploy.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "portal-oidc-public-deploy.yml"
STRATEGY_LAB_API = REPO_ROOT / "ai_platform" / "portal" / "web" / "lib" / "strategy-lab-api.ts"
BLUEPRINT = (
    REPO_ROOT
    / "deploy"
    / "synology"
    / "portal-oidc"
    / "blueprints"
    / "freqtrade-portal-public.yaml"
)


def test_deploy_probe_requires_public_https_authorization_boundary() -> None:
    script = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert 'PORTAL_ORIGIN = "https://quant.molehill.cloud"' in script
    assert 'AUTHENTIK_ORIGIN = "https://auth.molehill.cloud"' in script
    assert "def _probe_web_login" in script
    assert "def _probe_public_portal" in script
    assert "class NoRedirect" in script
    assert 'parsed.scheme != "https"' in script
    assert 'parsed.netloc != "auth.molehill.cloud"' in script
    assert "public Portal login did not redirect to public Authen­tik" in script


def test_deploy_disables_fixture_and_keeps_control_plane_internal() -> None:
    script = DEPLOY_SCRIPT.read_text(encoding="utf-8")
    control_section = script[
        script.index("def _control_run_args") : script.index("def _start_control_candidate")
    ]
    web_section = script[script.index("def _web_run_args") : script.index("def _probe_web_login")]

    assert "PORTAL_IDENTITY_FIXTURE_MODE=disabled" in script
    assert "PORTAL_IDENTITY_TRANSPORT_MODE=https" in script
    assert 'PORTAL_DATA_DIR = Path("/volume1/docker/freqtrade-portal-oidc/data")' in script
    assert "PORTAL_UID = 10001" in script
    assert "PORTAL_GID = 10001" in script
    assert "os.getuid()" not in script
    assert "os.getgid()" not in script
    assert "PORTAL_CONTROL_PLANE_URL=http://" in script
    assert "--publish" not in control_section
    assert "--publish" in web_section
    assert '"--read-only"' in script
    assert '"--cap-drop"' in script
    assert "no-new-privileges:true" in script
    assert "dst={LIQUIDATIONS_CONTAINER_ROOT},readonly" in script
    assert '"unless-stopped"' in script


def test_strategy_lab_mutations_forward_identity_csrf() -> None:
    script = STRATEGY_LAB_API.read_text(encoding="utf-8")

    assert 'const CSRF_COOKIE_NAME = "__Host-portal_csrf"' in script
    assert 'const CSRF_HEADER_NAME = "x-csrf-token"' in script
    assert 'const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"])' in script
    assert "...csrfHeaders(cookieHeader, init)" in script
    assert "STRATEGY_LAB_CSRF_MISSING" in script


def test_workflow_and_blueprint_enforce_public_secret_free_oidc() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    blueprint = BLUEPRINT.read_text(encoding="utf-8")

    assert "runs-on: [freqtrade-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert "git diff --name-status" in workflow
    assert "public-oidc-20260801-v1.json" in workflow
    assert '"bootstrap_membership_authorized": False' in workflow
    assert '"secret_values_in_request": False' in workflow
    assert '"live_capital_authorized": False' in workflow
    assert "if: always()" in workflow
    assert "https://quant.molehill.cloud/api/identity/callback" in blueprint
    assert "client_secret:" not in blueprint
    assert "PORTAL_IDENTITY_FIXTURE_MODE=enabled" not in workflow
