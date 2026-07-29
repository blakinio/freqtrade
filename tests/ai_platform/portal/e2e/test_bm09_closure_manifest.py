from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path("ai_platform/portal/e2e/scenarios/bot_management_closure.json")
EXPECTED_FAMILIES = {
    "ambiguous_execution_reconciliation",
    "bot_creation",
    "bot_lifecycle",
    "bot_revision_conflict",
    "cross_tenant_denial",
    "grid_configuration_and_runtime",
    "position_and_order_management",
    "private_dry_run_submission",
    "risk_approved_and_rejected_commands",
    "session_revocation_and_step_up",
    "signal_authentication_and_replay",
    "source_unavailable_and_stale",
}


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_bm09_manifest_covers_every_required_scenario_family_once() -> None:
    manifest = _manifest()
    scenarios = manifest["scenarios"]
    assert isinstance(scenarios, list)

    families = [scenario["family"] for scenario in scenarios]
    assert set(families) == EXPECTED_FAMILIES
    assert len(families) == len(set(families))


def test_bm09_manifest_references_existing_repository_evidence() -> None:
    scenarios = _manifest()["scenarios"]
    assert isinstance(scenarios, list)

    for scenario in scenarios:
        assert isinstance(scenario, dict)
        references = scenario["test_refs"]
        assert isinstance(references, list)
        assert references
        for reference in references:
            assert isinstance(reference, str)
            assert Path(reference).exists(), reference


def test_bm09_repository_acceptance_preserves_external_and_capital_gates() -> None:
    manifest = _manifest()

    assert manifest["repository_acceptance_only"] is True
    assert manifest["real_target_acceptance"] is False
    assert manifest["live_capital_authorized"] is False

    serialized = json.dumps(manifest, sort_keys=True).casefold()
    assert "production accepted" not in serialized
    assert "real target accepted" not in serialized
    assert "live execution enabled" not in serialized


def test_universal_e2e_workflow_runs_bm09_backend_and_browser_closure() -> None:
    workflow = Path(".github/workflows/portal-universal-e2e.yml").read_text(
        encoding="utf-8"
    )

    assert '"ai_platform/portal/e2e/**"' in workflow
    assert '"tests/ai_platform/portal/e2e/**"' in workflow
    assert "tests/ai_platform/portal/e2e" in workflow
    assert "npm run test:e2e:critical" in workflow
