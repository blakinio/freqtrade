from __future__ import annotations

from uuid import uuid4

import pytest

from ai_platform.portal.quality_agent.schema import (
    DiagnosisConfidence,
    FailureClassification,
    RepairRejectionReason,
)
from ai_platform.portal.quality_agent.service import SimulationFirstRepairService
from ai_platform.portal.simulator.schema import ScenarioFailureEvidence


OWNED_PATHS = (
    "ai_platform/portal/simulator/",
    "tests/ai_platform/portal/simulator/",
)
REGRESSION_TEST = "tests/ai_platform/portal/simulator/test_universal_scenario.py"
PRODUCT_PATH = "ai_platform/portal/simulator/runner.py"


def _failure(*, stage: str = "scenario_assertion", reason: str) -> ScenarioFailureEvidence:
    return ScenarioFailureEvidence(
        scenario_id="scenario-seeded-repair",
        correlation_id=uuid4(),
        stage=stage,
        reason_code=reason,
    )


@pytest.mark.parametrize(
    ("stage", "reason", "classification", "layer", "confidence"),
    [
        (
            "scenario_assertion",
            "learning workflow mutated active model assignment",
            FailureClassification.PRODUCT_DEFECT,
            "learning_control",
            DiagnosisConfidence.HIGH,
        ),
        (
            "scenario_assertion",
            "scenario context lacks required portal permissions",
            FailureClassification.TEST_DEFECT,
            "test_harness",
            DiagnosisConfidence.HIGH,
        ),
        (
            "environment",
            "connection refused",
            FailureClassification.ENVIRONMENT_DEFECT,
            "environment",
            DiagnosisConfidence.MEDIUM,
        ),
        (
            "dependency",
            "service unavailable",
            FailureClassification.DEPENDENCY_OUTAGE,
            "dependency",
            DiagnosisConfidence.MEDIUM,
        ),
        (
            "scenario_assertion",
            "unexpected deterministic mismatch",
            FailureClassification.FLAKY_OR_AMBIGUOUS,
            "unknown",
            DiagnosisConfidence.LOW,
        ),
    ],
)
def test_failure_classification_is_deterministic(
    stage: str,
    reason: str,
    classification: FailureClassification,
    layer: str,
    confidence: DiagnosisConfidence,
) -> None:
    diagnosis = SimulationFirstRepairService().diagnose(
        _failure(stage=stage, reason=reason),
        reproduced=True,
    )

    assert diagnosis.classification is classification
    assert diagnosis.likely_layer == layer
    assert diagnosis.confidence is confidence
    assert diagnosis.evidence_kind == "simulated"


def test_safe_simulation_first_repair_proposal_is_allowed() -> None:
    service = SimulationFirstRepairService()
    bundle = service.propose(
        _failure(reason="simulated trade did not close after opening"),
        reproduced=True,
        task_id="FTAI-20260723-seeded-simulator-repair",
        owned_paths=OWNED_PATHS,
        regression_test_paths=(REGRESSION_TEST,),
        proposed_changed_paths=(REGRESSION_TEST, PRODUCT_PATH),
        validation_commands=(
            "pytest -q tests/ai_platform/portal/simulator/test_universal_scenario.py",
        ),
        pr_summary=(
            "Repair the seeded deterministic simulator close-order defect with regression coverage."
        ),
        evidence_refs=("e2e-artifacts/scenario-seeded-repair/first-failure.json",),
    )

    assert bundle.decision.allowed is True
    assert bundle.decision.reason_codes == ()
    assert bundle.plan.branch_name.startswith("agent/ftai-20260723-seeded-simulator-repair-")
    assert bundle.plan.evidence_kind == "simulated"
    assert bundle.plan.claims_real_p11_acceptance is False


def test_non_reproduced_failure_cannot_authorize_repair() -> None:
    bundle = SimulationFirstRepairService().propose(
        _failure(reason="unexpected deterministic mismatch"),
        reproduced=False,
        task_id="FTAI-20260723-ambiguous-repair",
        owned_paths=OWNED_PATHS,
        regression_test_paths=(REGRESSION_TEST,),
        proposed_changed_paths=(REGRESSION_TEST, PRODUCT_PATH),
        validation_commands=("pytest -q tests/ai_platform/portal/simulator",),
        pr_summary="Investigate an ambiguous simulator failure.",
    )

    assert bundle.decision.allowed is False
    assert RepairRejectionReason.EVIDENCE_NOT_REPRODUCED in bundle.decision.reason_codes


def test_repair_requires_regression_test_first() -> None:
    bundle = SimulationFirstRepairService().propose(
        _failure(reason="simulated trade did not close after opening"),
        reproduced=True,
        task_id="FTAI-20260723-missing-regression",
        owned_paths=OWNED_PATHS,
        regression_test_paths=(),
        proposed_changed_paths=(PRODUCT_PATH,),
        validation_commands=("pytest -q tests/ai_platform/portal/simulator",),
        pr_summary="Attempt a repair without regression coverage.",
    )

    assert bundle.decision.allowed is False
    assert RepairRejectionReason.MISSING_REGRESSION_TEST in bundle.decision.reason_codes


def test_repair_outside_declared_ownership_is_rejected() -> None:
    bundle = SimulationFirstRepairService().propose(
        _failure(reason="simulated trade did not close after opening"),
        reproduced=True,
        task_id="FTAI-20260723-path-escape",
        owned_paths=OWNED_PATHS,
        regression_test_paths=(REGRESSION_TEST,),
        proposed_changed_paths=(REGRESSION_TEST, "freqtrade/rpc/api_server/api_v1.py"),
        validation_commands=("pytest -q tests/ai_platform/portal/simulator",),
        pr_summary="Attempt a repair outside the bounded portal task.",
    )

    assert bundle.decision.allowed is False
    assert RepairRejectionReason.PATH_OUTSIDE_OWNERSHIP in bundle.decision.reason_codes


@pytest.mark.parametrize(
    ("flag", "reason"),
    [
        ("weakens_safety_assertion", RepairRejectionReason.SAFETY_ASSERTION_WEAKENING),
        ("deploys_production", RepairRejectionReason.PRODUCTION_DEPLOYMENT),
        ("requires_production_secret", RepairRejectionReason.PRODUCTION_CREDENTIAL_ACCESS),
        ("enables_live_capital", RepairRejectionReason.LIVE_CAPITAL_ENABLEMENT),
        ("claims_real_p11_acceptance", RepairRejectionReason.REAL_P11_ACCEPTANCE_CLAIM),
    ],
)
def test_high_risk_or_false_evidence_repair_actions_are_rejected(
    flag: str,
    reason: RepairRejectionReason,
) -> None:
    kwargs = {flag: True}
    bundle = SimulationFirstRepairService().propose(
        _failure(reason="simulated trade did not close after opening"),
        reproduced=True,
        task_id="FTAI-20260723-unsafe-repair",
        owned_paths=OWNED_PATHS,
        regression_test_paths=(REGRESSION_TEST,),
        proposed_changed_paths=(REGRESSION_TEST, PRODUCT_PATH),
        validation_commands=("pytest -q tests/ai_platform/portal/simulator",),
        pr_summary="Unsafe repair proposal used to prove fail-closed policy.",
        **kwargs,
    )

    assert bundle.decision.allowed is False
    assert reason in bundle.decision.reason_codes


def test_parent_path_escape_is_rejected_even_when_prefix_looks_owned() -> None:
    bundle = SimulationFirstRepairService().propose(
        _failure(reason="simulated trade did not close after opening"),
        reproduced=True,
        task_id="FTAI-20260723-parent-path-escape",
        owned_paths=OWNED_PATHS,
        regression_test_paths=(REGRESSION_TEST,),
        proposed_changed_paths=(
            REGRESSION_TEST,
            "ai_platform/portal/simulator/../execution/adapter.py",
        ),
        validation_commands=("pytest -q tests/ai_platform/portal/simulator",),
        pr_summary="Attempt a path traversal outside simulator ownership.",
    )

    assert bundle.decision.allowed is False
    assert RepairRejectionReason.PATH_OUTSIDE_OWNERSHIP in bundle.decision.reason_codes
