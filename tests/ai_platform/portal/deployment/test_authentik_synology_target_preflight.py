from __future__ import annotations

import base64
import importlib.util
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[4]
DEPLOY_ROOT = ROOT / "deploy" / "synology" / "portal-authentik"
WORKFLOW = ROOT / ".github" / "workflows" / "portal-authentik-synology-target-preflight.yml"
MODULE_PATH = DEPLOY_ROOT / "target_preflight.py"
REQUEST_PATH = (
    "deploy/synology/portal-authentik/run-requests/target-preflight-20260727-v1.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("target_preflight", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_environment() -> dict[str, str]:
    key = base64.b64encode(b"k" * 32).decode()
    return {
        "PI06_AUTHENTIK_POSTGRES_PASSWORD": "p" * 40,
        "PI06_AUTHENTIK_SECRET_KEY": "s" * 60,
        "PI06_AUTHENTIK_BOOTSTRAP_PASSWORD_HASH": "pbkdf2_sha256$1000$salt$hash",
        "PI06_PORTAL_OIDC_CLIENT_SECRET": "o" * 32,
        "PI06_PORTAL_SESSION_HMAC_KEY_B64": key,
        "PI06_PORTAL_FLOW_ENCRYPTION_KEY_B64": key,
        "PI06_AUTHENTIK_AGE_RECIPIENT": "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq",
        "PI06_AUTHENTIK_PUBLIC_BASE_URL": "https://auth.example.test",
        "PI06_PORTAL_PUBLIC_BASE_URL": "https://portal.example.test",
        "PI06_PORTAL_IDENTITY_CLIENT_ID": "portal",
    }


def test_workflow_is_exact_request_gated_and_self_hosted() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert f'- "{REQUEST_PATH}"' in text
    assert "runs-on: [self-hosted, Linux, oteryn-staging]" in text
    assert "environment: synology-staging" in text
    assert "permissions:\n  contents: read" in text
    assert "workflow_dispatch:" not in text
    assert "schedule:" not in text
    assert "push:" not in text
    assert "Validate exact-one-file request scope" in text
    assert "github.event.pull_request.head.repo.full_name == github.repository" in text


def test_workflow_maps_only_declared_identity_material() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    required = {
        "PI06_AUTHENTIK_POSTGRES_PASSWORD",
        "PI06_AUTHENTIK_SECRET_KEY",
        "PI06_AUTHENTIK_BOOTSTRAP_PASSWORD_HASH",
        "PI06_PORTAL_OIDC_CLIENT_SECRET",
        "PI06_PORTAL_SESSION_HMAC_KEY_B64",
        "PI06_PORTAL_FLOW_ENCRYPTION_KEY_B64",
        "PI06_AUTHENTIK_AGE_RECIPIENT",
        "PI06_AUTHENTIK_PUBLIC_BASE_URL",
        "PI06_PORTAL_PUBLIC_BASE_URL",
        "PI06_PORTAL_IDENTITY_CLIENT_ID",
    }
    for name in required:
        assert name in text
    assert "secrets.PI06_" in text
    assert "vars.PI06_" in text
    assert "Recognized trading credential environment is present" in text


def test_preflight_has_no_container_mutation_commands() -> None:
    combined = WORKFLOW.read_text(encoding="utf-8") + MODULE_PATH.read_text(encoding="utf-8")
    forbidden = {
        "docker compose up",
        "docker compose down",
        "docker run",
        "docker stop",
        "docker rm",
        "docker exec",
        "docker pull",
        "docker restart",
        "bootstrap.sh",
        "restore.sh",
    }
    for snippet in forbidden:
        assert snippet not in combined
    assert '"container_changes_executed": False' in combined
    assert '"bootstrap_executed": False' in combined
    assert '"restore_executed": False' in combined


def test_frozen_request_forbids_deployment_bootstrap_and_restore() -> None:
    module = load_module()
    request = module.EXPECTED_REQUEST
    assert request["expected_runner_name"] == "oteryn-synology-staging"
    assert request["expected_environment"] == "synology-staging"
    assert request["expected_state_dir"] == "/var/lib/oteryn-staging-state"
    assert request["bounded_storage_probe_authorized"] is True
    assert request["deployment_mutation_authorized"] is False
    assert request["bootstrap_authorized"] is False
    assert request["restore_authorized"] is False
    assert len({request["target_root"], request["backup_root"], request["restore_root"]}) == 3


def test_secret_validation_accepts_strong_values_without_returning_them() -> None:
    module = load_module()
    env = valid_environment()
    missing, invalid = module.valid_secret_material(env)
    assert missing == []
    assert invalid == []
    result_text = repr((missing, invalid))
    for name in module.SENSITIVE_ENV:
        assert env[name] not in result_text


def test_secret_validation_reports_names_only() -> None:
    module = load_module()
    env = valid_environment()
    env["PI06_AUTHENTIK_POSTGRES_PASSWORD"] = "short"
    env["PI06_PORTAL_SESSION_HMAC_KEY_B64"] = "not-base64"
    del env["PI06_AUTHENTIK_AGE_RECIPIENT"]
    missing, invalid = module.valid_secret_material(env)
    assert missing == ["PI06_AUTHENTIK_AGE_RECIPIENT"]
    assert invalid == [
        "PI06_AUTHENTIK_POSTGRES_PASSWORD",
        "PI06_PORTAL_SESSION_HMAC_KEY_B64",
    ]
    assert "short" not in repr((missing, invalid))
    assert "not-base64" not in repr((missing, invalid))


def test_public_configuration_requires_https_and_dns() -> None:
    module = load_module()
    env = valid_environment()
    with patch.object(module.socket, "getaddrinfo", return_value=[object()]):
        missing, invalid, dns = module.valid_public_configuration(env)
    assert missing == []
    assert invalid == []
    assert dns == {"authentik_host_resolves": True, "portal_host_resolves": True}
    env["PI06_AUTHENTIK_PUBLIC_BASE_URL"] = "http://auth.example.test"
    with patch.object(module.socket, "getaddrinfo", return_value=[object()]):
        _, invalid, _ = module.valid_public_configuration(env)
    assert invalid == ["PI06_AUTHENTIK_PUBLIC_BASE_URL"]


def test_report_contract_never_records_secret_values() -> None:
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert '"secret_values_recorded": False' in text
    assert '"required_secret_names": sorted(SENSITIVE_ENV)' in text
    assert '"missing_secret_names": missing_secrets' in text
    assert '"invalid_secret_names": invalid_secrets' in text
    assert '"ready_for_controlled_deployment": not unique_blockers' in text
    assert "env.get(name" not in text.split('"configuration":', 1)[-1]
