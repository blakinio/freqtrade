from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast


class AutomatedScenario(TypedDict):
    id: str
    evidence: str


class ManualOwnerScenario(TypedDict):
    id: str
    required: bool
    secret_free_evidence: bool


class AcceptanceContract(TypedDict):
    schema_version: int
    package: str
    claim: str
    automated_scenarios: list[AutomatedScenario]
    manual_owner_scenarios: list[ManualOwnerScenario]
    forbidden_claims: list[str]


ROOT = Path(__file__).resolve().parents[4]
DEPLOYMENT_ROOT = ROOT / "deploy" / "synology" / "portal-authentik"
CONTRACT = DEPLOYMENT_ROOT / "emulated-acceptance-contract-v1.json"
WORKFLOW = ROOT / ".github" / "workflows" / "portal-pi06-emulated-target-acceptance.yml"
RUNBOOK = (
    ROOT / "docs" / "ai_platform" / "portal" / "runbooks" / "PI06_EMULATED_TARGET_ACCEPTANCE.md"
)


def load_contract() -> AcceptanceContract:
    return cast(AcceptanceContract, json.loads(CONTRACT.read_text(encoding="utf-8")))


def test_contract_has_exact_emulated_and_manual_scenario_families() -> None:
    contract = load_contract()

    automated = {scenario["id"] for scenario in contract["automated_scenarios"]}
    manual = {scenario["id"] for scenario in contract["manual_owner_scenarios"]}

    assert automated == {
        "runtime_health",
        "network_and_secret_boundary",
        "persistent_storage_restart",
        "portal_mfa_fail_closed_policy",
    }
    assert manual == {
        "totp_enrollment_google_authenticator",
        "totp_challenge_after_new_login",
        "encrypted_backup_and_isolated_restore",
    }


def test_every_repository_evidence_path_exists() -> None:
    contract = load_contract()

    for scenario in contract["automated_scenarios"]:
        evidence = ROOT / scenario["evidence"]
        assert evidence.is_file(), evidence


def test_contract_never_upgrades_emulation_to_real_target_acceptance() -> None:
    contract = load_contract()

    assert contract["claim"] == "emulated_non_production_acceptance_only"
    assert set(contract["forbidden_claims"]) == {
        "real_synology_target_accepted",
        "real_mfa_accepted",
        "real_oidc_portal_callback_accepted",
        "real_restore_accepted",
        "p11_accepted",
        "live_capital_authorized",
    }
    assert all(
        scenario["required"] and scenario["secret_free_evidence"]
        for scenario in contract["manual_owner_scenarios"]
    )


def test_emulation_uses_isolated_resources_and_real_containers() -> None:
    script = (DEPLOYMENT_ROOT / "emulated_acceptance.sh").read_text(encoding="utf-8")
    override = (DEPLOYMENT_ROOT / "compose.emulated.yml").read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "compose.emulated.yml" in script
    assert "down --volumes --remove-orphans" in script
    assert "emulation refuses the default target port" in script
    assert "docker compose" in script
    assert "up -d --pull always postgresql server worker" in script
    assert "PI06_EMULATED_RESOURCE_PREFIX" in override
    assert "internal: true" in override
    assert "Run real-container emulation" in workflow
    assert "identity-session.spec.ts" in workflow


def test_runbook_requires_owner_totp_without_recording_secrets() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")

    assert "Google Authenticator" in runbook
    assert "Do not capture the QR code" in runbook
    assert "does not prove real target acceptance" in runbook
    assert "SSH port forwarding" in runbook
