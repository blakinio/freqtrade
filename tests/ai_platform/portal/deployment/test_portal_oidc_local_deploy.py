from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT = ROOT / "deploy" / "synology" / "portal-oidc"
WORKFLOW = ROOT / ".github" / "workflows" / "portal-oidc-local-test-deploy.yml"
SPEC = importlib.util.spec_from_file_location("portal_oidc_deploy", DEPLOYMENT / "deploy.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def frozen_request(sha: str) -> dict[str, object]:
    return {
        "request_id": module.REQUEST_ID,
        "environment": "synology-staging",
        "runner": "freqtrade-staging",
        "implementation_sha": sha,
        "authentik_origin": module.AUTHENTIK_ORIGIN,
        "portal_origin": f"http://{module.PORTAL_BIND_ADDRESS}:{module.PORTAL_PORT}",
        "identity_transport": "local_http_test",
        "identity_fixture_mode": "disabled",
        "dry_run_required": True,
        "public_ingress_authorized": False,
        "live_capital_authorized": False,
        "restore_authorized": False,
        "secret_values_in_request": False,
    }


def test_frozen_request_accepts_only_current_implementation_sha(tmp_path: Path) -> None:
    sha = "a" * 40
    request_path = tmp_path / module.REQUEST_RELATIVE_PATH
    request_path.parent.mkdir(parents=True)
    request_path.write_text(json.dumps(frozen_request(sha)), encoding="utf-8")

    assert module._load_request(request_path, sha) == frozen_request(sha)

    request = frozen_request(sha)
    request["live_capital_authorized"] = True
    request_path.write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(module.DeploymentError, match="frozen contract"):
        module._load_request(request_path, sha)


def test_blueprint_has_exact_provider_application_scopes_and_redirect() -> None:
    blueprint = (DEPLOYMENT / "blueprints" / module.BLUEPRINT_NAME).read_text(encoding="utf-8")

    assert "authentik_providers_oauth2.oauth2provider" in blueprint
    assert "authentik_core.application" in blueprint
    assert "client_type: confidential" in blueprint
    assert f"client_id: {module.CLIENT_ID}" in blueprint
    assert f"url: {module.REDIRECT_URI}" in blueprint
    assert "matching_mode: strict" in blueprint
    assert "scope_name, openid" in blueprint
    assert "scope_name, profile" in blueprint
    assert "scope_name, email" in blueprint
    assert "client_secret:" not in blueprint
    assert "return bool(request.user and request.user.is_authenticated and request.user.is_active)" in blueprint


def test_images_are_pinned_by_exact_version_and_digest() -> None:
    web = (ROOT / "deploy" / "synology" / "portal" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    control = (DEPLOYMENT / "Dockerfile.control-plane").read_text(encoding="utf-8")

    assert web.count("node:22.23.1-bookworm-slim@sha256:") == 3
    assert "python:3.13.13-slim-bookworm@sha256:" in control
    assert ":latest" not in web
    assert ":latest" not in control
    assert "USER portal" in control
    assert "--no-access-log" in control


def test_deployer_preserves_secrets_and_forbids_unsafe_runtime_controls() -> None:
    source = (DEPLOYMENT / "deploy.py").read_text(encoding="utf-8")

    assert "0o600" in source
    assert "refusing rotation" in source
    assert '"secret_values_recorded": False' in source
    assert '"live_capital_authorized": False' in source
    assert "PORTAL_IDENTITY_FIXTURE_MODE=disabled" in source
    assert "PORTAL_IDENTITY_TRANSPORT_MODE=local_http_test" in source
    assert "--cap-drop" in source
    assert "no-new-privileges:true" in source
    assert "--read-only" in source
    assert "--network" in source
    assert "--privileged" not in source
    assert "network_mode: host" not in source
    assert "/var/run/docker.sock" not in source
    assert "POSTGRES" not in source or "--publish" not in source


def test_control_plane_is_internal_and_portal_is_the_only_published_service() -> None:
    source = (DEPLOYMENT / "deploy.py").read_text(encoding="utf-8")

    control_section = source[source.index("def _start_control_candidate") : source.index("def _promote_control")]
    web_section = source[source.index("def _web_run_args") : source.index("def _probe_web_login")]
    assert "--publish" not in control_section
    assert "--publish" in web_section
    assert f"{module.PORTAL_BIND_ADDRESS}" in source
    assert str(module.PORTAL_PORT) in source


def test_workflow_is_exact_one_request_secret_free_and_sha_pinned() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: [freqtrade-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert "git diff --name-status" in workflow
    assert "implementation_sha must equal the current develop base SHA" in workflow
    assert "secret_values_in_request" in workflow
    assert "if: always()" in workflow
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in workflow
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in workflow
    assert "actions/checkout@v" not in workflow
    assert "actions/upload-artifact@v" not in workflow


def test_report_contract_contains_no_secret_values() -> None:
    source = (DEPLOYMENT / "deploy.py").read_text(encoding="utf-8")
    report_slice = source[source.index("report: dict[str, Any]") :]

    assert "client_secret" not in report_slice
    assert "SESSION_HMAC_KEY" not in report_slice
    assert "FLOW_ENCRYPTION_KEY" not in report_slice
    assert '"secret_values_recorded": False' in report_slice
