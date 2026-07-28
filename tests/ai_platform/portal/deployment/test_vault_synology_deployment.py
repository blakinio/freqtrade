from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "deploy" / "synology" / "portal-vault"


def load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "portal_vault_validate",
        PACKAGE / "validate.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_vault_package_passes_fail_closed_validation() -> None:
    validator = load_validator()
    errors = validator.validate(PACKAGE, PACKAGE / ".env.example", example=True)
    assert errors == []


def test_vault_compose_has_no_public_or_privileged_surface() -> None:
    text = (PACKAGE / "compose.yml").read_text(encoding="utf-8")
    assert "ports:" not in text
    assert "network_mode: host" not in text
    assert "privileged: true" not in text
    assert "docker.sock" not in text
    assert "internal: true" in text
    assert text.count("read_only: true") == 3
    assert text.count("cap_drop:\n      - ALL") == 3
    assert text.count("no-new-privileges:true") == 3


def test_vault_image_is_exactly_tagged_and_digest_pinned() -> None:
    values = load_validator().read_env(PACKAGE / ".env.example")
    assert values["VAULT_IMAGE"] == (
        "docker.io/hashicorp/vault:2.0.3@"
        "sha256:a296a888b118615dc01d5f1a6846e6d4a7277946caaed5b447008fff5fe06b54"
    )


def test_vault_configuration_enforces_tls_13_and_raft() -> None:
    text = (PACKAGE / "vault.hcl").read_text(encoding="utf-8")
    assert 'storage "raft"' in text
    assert 'tls_min_version = "tls13"' in text
    assert 'tls_max_version = "tls13"' in text
    assert "tls_disable" not in text
    assert 'default_lease_ttl = "10m"' in text
    assert 'max_lease_ttl = "15m"' in text
    assert "ui = false" in text


def test_broker_policy_is_read_only_and_tenant_scoped() -> None:
    text = (PACKAGE / "broker-policy.hcl").read_text(encoding="utf-8")
    assert text.count('capabilities = ["read"]') == 3
    assert "portal-secrets/data/tenants/+/exchange-connections/+" in text
    assert "portal-secrets/metadata/tenants/+/exchange-connections/+" in text
    for forbidden in ('"create"', '"update"', '"delete"', '"sudo"', '"list"'):
        assert forbidden not in text


def test_bootstrap_requires_dual_audit_and_short_approle_tokens() -> None:
    text = (PACKAGE / "bootstrap.sh").read_text(encoding="utf-8")
    assert "audit-primary" in text
    assert "audit-secondary" in text
    assert "token_ttl=10m" in text
    assert "token_max_ttl=15m" in text
    assert "secret_id_ttl=24h" in text
    assert "set -x" not in text
    assert "echo $VAULT_TOKEN" not in text


def test_deployment_contract_preserves_owner_and_capital_boundaries() -> None:
    contract = json.loads((PACKAGE / "deployment-contract-v1.json").read_text(encoding="utf-8"))
    assert contract["status"] == "repository_validated_target_not_accepted"
    assert contract["execution_mode"] == "dry_run"
    assert contract["withdrawals_enabled"] is False
    assert contract["live_capital_authorized"] is False
    assert contract["target_acceptance_required"] is True
