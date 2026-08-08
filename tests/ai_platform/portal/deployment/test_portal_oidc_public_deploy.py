from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT = ROOT / "deploy" / "synology" / "portal-oidc"
WORKFLOW = ROOT / ".github" / "workflows" / "portal-oidc-public-deploy.yml"
SPEC = importlib.util.spec_from_file_location("portal_oidc_deploy", DEPLOYMENT / "deploy.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
DIAGNOSTIC_SPEC = importlib.util.spec_from_file_location(
    "portal_oidc_discovery",
    DEPLOYMENT / "diagnose_discovery.py",
)
assert DIAGNOSTIC_SPEC and DIAGNOSTIC_SPEC.loader
diagnostic = importlib.util.module_from_spec(DIAGNOSTIC_SPEC)
DIAGNOSTIC_SPEC.loader.exec_module(diagnostic)


def frozen_request(sha: str) -> dict[str, object]:
    return {
        "request_id": module.REQUEST_ID,
        "environment": "synology-staging",
        "runner": "freqtrade-staging",
        "implementation_sha": sha,
        "portal_origin": module.PORTAL_ORIGIN,
        "authentik_origin": module.AUTHENTIK_ORIGIN,
        "identity_transport": "https",
        "identity_fixture_mode": "disabled",
        "bootstrap_membership_authorized": False,
        "dry_run_required": True,
        "public_ingress_authorized": True,
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
    request["bootstrap_membership_authorized"] = True
    request_path.write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(module.DeploymentError, match="frozen contract"):
        module._load_request(request_path, sha)


def test_run_preserves_actionable_nonsensitive_error(monkeypatch) -> None:
    def fake_run(*_args, **_kwargs):
        return module.subprocess.CompletedProcess(
            args=["docker", "run"],
            returncode=125,
            stdout="",
            stderr=(
                "docker: invalid mount config for type bind: source path does not exist\n"
                "Run 'docker run --help' for more information\n"
            ),
        )

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    with pytest.raises(module.DeploymentError, match="source path does not exist"):
        module._run(["docker", "run", "redacted-image"])


def test_run_preserves_tail_of_long_build_error(monkeypatch) -> None:
    build_lines = [f"# {index} intermediate build output" for index in range(20)]
    build_lines.append("ERROR: failed to solve: required build input is missing")

    def fake_run(*_args, **_kwargs):
        return module.subprocess.CompletedProcess(
            args=["docker", "build"],
            returncode=1,
            stdout="\n".join(build_lines),
            stderr="",
        )

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    with pytest.raises(module.DeploymentError, match="required build input is missing"):
        module._run(["docker", "build", "redacted-context"])


def test_blueprint_has_exact_public_provider_scopes_and_redirect() -> None:
    blueprint = (DEPLOYMENT / "blueprints" / module.BLUEPRINT_NAME).read_text(encoding="utf-8")

    assert "authentik_providers_oauth2.oauth2provider" in blueprint
    assert "authentik_core.application" in blueprint
    assert "client_type: confidential" in blueprint
    assert f"client_id: {module.CLIENT_ID}" in blueprint
    assert f"slug: {module.APPLICATION_SLUG}" in blueprint
    assert f"url: {module.REDIRECT_URI}" in blueprint
    assert "matching_mode: strict" in blueprint
    assert "scope_name, openid" in blueprint
    assert "scope_name, profile" in blueprint
    assert "scope_name, email" in blueprint
    assert "client_secret:" not in blueprint
    assert "http://192.168." not in blueprint
    assert "auth.quant.molehill.cloud" not in blueprint


def test_public_runtime_composes_full_control_plane_without_automatic_membership() -> None:
    runtime = (ROOT / "ai_platform" / "portal" / "identity" / "public_runtime.py").read_text(
        encoding="utf-8"
    )
    bootstrap = (
        ROOT / "ai_platform" / "portal" / "identity" / "bootstrap_membership.py"
    ).read_text(encoding="utf-8")

    assert 'identity_config.transport_mode != "secure_https"' in runtime
    assert "create_identity_enabled_app" in runtime
    assert "_REQUIRED_COMPOSED_ROUTES" in runtime
    assert "public_runtime_unprivileged" in runtime
    assert '"/v1/bots"' in runtime
    assert '"/v1/positions"' in runtime
    assert '"/v1/terminal/intents"' in runtime
    assert "_ensure_local_owner_membership" not in runtime
    assert "--confirm-exact-principal" in bootstrap
    assert "identity.membership_bootstrapped" in bootstrap
    assert "subject_sha256" in bootstrap
    assert '"secret_values_recorded": False' in bootstrap
    assert '"live_capital_authorized": False' in bootstrap


def test_images_are_pinned_and_control_plane_runs_authenticated_public_runtime() -> None:
    web = (ROOT / "deploy" / "synology" / "portal" / "Dockerfile").read_text(encoding="utf-8")
    control = (DEPLOYMENT / "Dockerfile.control-plane").read_text(encoding="utf-8")
    web_base = (
        "node:22.23.1-bookworm-slim@sha256:"
        "6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3"
    )
    control_base = (
        "python:3.13.14-slim-bookworm@sha256:"
        "9d7f287598e1a5a978c015ee176d8216435aaf335ed69ac3c38dd1bbb10e8d64"
    )

    assert f"FROM {web_base} AS dependencies" in web
    assert f"FROM {web_base} AS builder" in web
    assert f"FROM {web_base} AS node-security-runtime" in web
    assert f"FROM {web_base} AS runtime" in web
    assert web.count(f"FROM {web_base}") == 4
    assert "PORTAL_WEB_DATA_MODE=api" in web
    assert "fixture Portal data mode is forbidden in staging/production" in web
    assert 'ENTRYPOINT ["/usr/local/bin/portal-web-entrypoint"]' in web
    assert f"FROM {control_base}" in control
    assert "ai_platform.portal.identity.public_runtime:app" in control
    assert "127.0.0.1:8000/readyz" in control
    assert ":latest" not in web
    assert ":latest" not in control
    assert "USER portal" in control
    assert "--no-access-log" in control


def test_deployer_is_public_secret_free_and_hardened() -> None:
    source = (DEPLOYMENT / "deploy.py").read_text(encoding="utf-8")

    assert module.PORTAL_ORIGIN == "https://quant.molehill.cloud"
    assert module.AUTHENTIK_ORIGIN == "https://auth.molehill.cloud"
    assert module.ISSUER == "https://auth.molehill.cloud/application/o/freqtrade-portal/"
    assert module.PORTAL_DATA_DIR == Path("/volume1/docker/freqtrade-portal-oidc/data")
    assert module.PORTAL_UID == 10001
    assert module.PORTAL_GID == 10001
    assert "os.chown(PORTAL_DATA_DIR, PORTAL_UID, PORTAL_GID)" in source
    assert 'f"{PORTAL_UID}:{PORTAL_GID}"' in source
    assert "os.getuid()" not in source
    assert "os.getgid()" not in source
    assert 'detail = " | ".join([*lines[:2], "...", *lines[-5:]])' in source
    assert "0o600" in source
    assert "refusing rotation" in source
    assert '"secret_values_recorded": False' in source
    assert '"live_capital_authorized": False' in source
    assert "PORTAL_IDENTITY_FIXTURE_MODE=disabled" in source
    assert "PORTAL_IDENTITY_TRANSPORT_MODE=https" in source
    assert "_discovery_from_identity_container" in source
    assert "--cap-drop" in source
    assert "no-new-privileges:true" in source
    assert "--read-only" in source
    assert "--privileged" not in source
    assert "network_mode: host" not in source
    assert "auth.quant.molehill.cloud" not in source


def test_control_bind_mount_uses_valid_default_read_write_syntax() -> None:
    args = module._control_run_args("image", "candidate")
    mount_index = args.index("--mount")
    assert args[mount_index + 1] == f"type=bind,src={module.PORTAL_DATA_DIR},dst=/state"
    assert not args[mount_index + 1].endswith(",rw")


def test_control_plane_is_internal_and_only_web_is_published() -> None:
    source = (DEPLOYMENT / "deploy.py").read_text(encoding="utf-8")

    control_section = source[
        source.index("def _control_run_args") : source.index("def _start_control_candidate")
    ]
    web_section = source[source.index("def _web_run_args") : source.index("def _probe_web_login")]
    assert "--publish" not in control_section
    assert "--publish" in web_section
    assert f"{module.PORTAL_BIND_ADDRESS}" in source
    assert str(module.PORTAL_PORT) in source


def test_discovery_probe_uses_explicit_machine_user_agent() -> None:
    script = diagnostic._probe_script()

    assert diagnostic.OIDC_HTTP_USER_AGENT == "Freqtrade-Portal-OIDC/1.0"
    assert "'Accept': 'application/json'" in script
    assert "'User-Agent': 'Freqtrade-Portal-OIDC/1.0'" in script
    assert "urllib.request.Request(url, headers=headers)" in script
    assert "urllib.request.urlopen(request, timeout=15)" in script
    assert "urllib.request.urlopen(discovery_url" not in script
    assert "urllib.request.urlopen(discovery['jwks_uri']" not in script


def test_deployment_entrypoint_installs_repaired_discovery_probe() -> None:
    entrypoint = (DEPLOYMENT / "deploy_entrypoint.py").read_text(encoding="utf-8")

    assert 'DEPLOYMENT_DIR / "deploy.py"' in entrypoint
    assert 'DEPLOYMENT_DIR / "diagnose_discovery.py"' in entrypoint
    assert "deploy._discovery_from_identity_container = lambda:" in entrypoint
    assert "discovery.deployment_probe" in entrypoint


def test_workflow_is_exact_one_request_secret_free_and_sha_pinned() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: [freqtrade-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert "git diff --name-status" in workflow
    assert "public-oidc-20260801-v1.json" in workflow
    assert "bootstrap_membership_authorized" in workflow
    assert "secret_values_in_request" in workflow
    assert "public_ingress_authorized" in workflow
    assert "if: always()" in workflow
    assert "python3 deploy/synology/portal-oidc/deploy_entrypoint.py" in workflow
    assert "python3 deploy/synology/portal-oidc/deploy.py" not in workflow
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
