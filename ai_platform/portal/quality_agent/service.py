from __future__ import annotations

import re
from pathlib import PurePosixPath

from ai_platform.portal.quality_agent.schema import (
    DiagnosisConfidence,
    DiagnosisRecord,
    FailureClassification,
    RepairDecision,
    RepairPlan,
    RepairProposalBundle,
    RepairRejectionReason,
)
from ai_platform.portal.simulator.schema import ScenarioFailureEvidence


_PRODUCT_FAILURES = {
    "learning workflow mutated active model assignment": "learning_control",
    "simulated trade did not close after opening": "simulator",
}

_TEST_FAILURE_FRAGMENTS = (
    "required portal permissions",
    "scenario tenant does not match trusted request context",
)

_DEPENDENCY_FRAGMENTS = (
    "dependency unavailable",
    "upstream unavailable",
    "service unavailable",
)

_ENVIRONMENT_FRAGMENTS = (
    "connection refused",
    "network unreachable",
    "dns failure",
    "infrastructure unavailable",
)


def _branch_slug(task_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", task_id.casefold()).strip("-")
    return slug or "repair"


def _is_safe_repo_path(path: str) -> bool:
    if not path or "\\" in path:
        return False
    parsed = PurePosixPath(path)
    return not parsed.is_absolute() and ".." not in parsed.parts


def _is_owned(path: str, owned_paths: tuple[str, ...]) -> bool:
    for owned in owned_paths:
        normalized = owned.rstrip("/")
        if path == normalized or path.startswith(f"{normalized}/"):
            return True
    return False


class SimulationFirstRepairService:
    def diagnose(
        self,
        failure: ScenarioFailureEvidence,
        *,
        reproduced: bool,
        evidence_refs: tuple[str, ...] = (),
    ) -> DiagnosisRecord:
        reason = failure.reason_code.casefold()
        stage = failure.stage.casefold()

        if reason in _PRODUCT_FAILURES:
            classification = FailureClassification.PRODUCT_DEFECT
            likely_layer = _PRODUCT_FAILURES[reason]
            confidence = DiagnosisConfidence.HIGH
        elif reason.startswith("scenario risk gate rejected intent:"):
            classification = FailureClassification.PRODUCT_DEFECT
            likely_layer = "risk"
            confidence = DiagnosisConfidence.HIGH
        elif any(fragment in reason for fragment in _TEST_FAILURE_FRAGMENTS):
            classification = FailureClassification.TEST_DEFECT
            likely_layer = "test_harness"
            confidence = DiagnosisConfidence.HIGH
        elif "dependency" in stage or any(fragment in reason for fragment in _DEPENDENCY_FRAGMENTS):
            classification = FailureClassification.DEPENDENCY_OUTAGE
            likely_layer = "dependency"
            confidence = DiagnosisConfidence.MEDIUM
        elif "environment" in stage or any(
            fragment in reason for fragment in _ENVIRONMENT_FRAGMENTS
        ):
            classification = FailureClassification.ENVIRONMENT_DEFECT
            likely_layer = "environment"
            confidence = DiagnosisConfidence.MEDIUM
        elif any(token in stage for token in ("test", "fixture", "locator")):
            classification = FailureClassification.TEST_DEFECT
            likely_layer = "test_harness"
            confidence = DiagnosisConfidence.MEDIUM
        else:
            classification = FailureClassification.FLAKY_OR_AMBIGUOUS
            likely_layer = "unknown"
            confidence = DiagnosisConfidence.LOW

        return DiagnosisRecord(
            scenario_id=failure.scenario_id,
            correlation_id=failure.correlation_id,
            first_failure_stage=failure.stage,
            reason_code=failure.reason_code,
            classification=classification,
            likely_layer=likely_layer,
            reproducible=reproduced,
            confidence=confidence,
            evidence_refs=evidence_refs,
        )

    def build_plan(
        self,
        diagnosis: DiagnosisRecord,
        *,
        task_id: str,
        regression_test_paths: tuple[str, ...],
        proposed_changed_paths: tuple[str, ...],
        validation_commands: tuple[str, ...],
        pr_summary: str,
        weakens_safety_assertion: bool = False,
        deploys_production: bool = False,
        requires_production_secret: bool = False,
        enables_live_capital: bool = False,
        claims_real_p11_acceptance: bool = False,
    ) -> RepairPlan:
        branch_name = f"agent/{_branch_slug(task_id)}-{str(diagnosis.correlation_id)[:8]}"
        return RepairPlan(
            task_id=task_id,
            branch_name=branch_name,
            regression_test_paths=regression_test_paths,
            proposed_changed_paths=proposed_changed_paths,
            validation_commands=validation_commands,
            pr_summary=pr_summary,
            weakens_safety_assertion=weakens_safety_assertion,
            deploys_production=deploys_production,
            requires_production_secret=requires_production_secret,
            enables_live_capital=enables_live_capital,
            claims_real_p11_acceptance=claims_real_p11_acceptance,
        )

    def evaluate(
        self,
        diagnosis: DiagnosisRecord,
        plan: RepairPlan,
        *,
        owned_paths: tuple[str, ...],
    ) -> RepairDecision:
        reasons: list[RepairRejectionReason] = []

        if not diagnosis.reproducible:
            reasons.append(RepairRejectionReason.EVIDENCE_NOT_REPRODUCED)

        regression_tests_valid = bool(plan.regression_test_paths) and all(
            path.startswith("tests/") and path in plan.proposed_changed_paths
            for path in plan.regression_test_paths
        )
        if not regression_tests_valid:
            reasons.append(RepairRejectionReason.MISSING_REGRESSION_TEST)

        changed_paths_valid = bool(plan.proposed_changed_paths) and all(
            _is_safe_repo_path(path) and _is_owned(path, owned_paths)
            for path in plan.proposed_changed_paths
        )
        if not changed_paths_valid:
            reasons.append(RepairRejectionReason.PATH_OUTSIDE_OWNERSHIP)

        if not plan.branch_name.startswith("agent/"):
            reasons.append(RepairRejectionReason.INVALID_BRANCH)
        if not plan.validation_commands:
            reasons.append(RepairRejectionReason.MISSING_VALIDATION)
        if plan.weakens_safety_assertion:
            reasons.append(RepairRejectionReason.SAFETY_ASSERTION_WEAKENING)
        if plan.deploys_production:
            reasons.append(RepairRejectionReason.PRODUCTION_DEPLOYMENT)
        if plan.requires_production_secret:
            reasons.append(RepairRejectionReason.PRODUCTION_CREDENTIAL_ACCESS)
        if plan.enables_live_capital:
            reasons.append(RepairRejectionReason.LIVE_CAPITAL_ENABLEMENT)
        if plan.claims_real_p11_acceptance:
            reasons.append(RepairRejectionReason.REAL_P11_ACCEPTANCE_CLAIM)

        return RepairDecision(allowed=not reasons, reason_codes=tuple(reasons))

    def propose(
        self,
        failure: ScenarioFailureEvidence,
        *,
        reproduced: bool,
        task_id: str,
        owned_paths: tuple[str, ...],
        regression_test_paths: tuple[str, ...],
        proposed_changed_paths: tuple[str, ...],
        validation_commands: tuple[str, ...],
        pr_summary: str,
        evidence_refs: tuple[str, ...] = (),
        weakens_safety_assertion: bool = False,
        deploys_production: bool = False,
        requires_production_secret: bool = False,
        enables_live_capital: bool = False,
        claims_real_p11_acceptance: bool = False,
    ) -> RepairProposalBundle:
        diagnosis = self.diagnose(
            failure,
            reproduced=reproduced,
            evidence_refs=evidence_refs,
        )
        plan = self.build_plan(
            diagnosis,
            task_id=task_id,
            regression_test_paths=regression_test_paths,
            proposed_changed_paths=proposed_changed_paths,
            validation_commands=validation_commands,
            pr_summary=pr_summary,
            weakens_safety_assertion=weakens_safety_assertion,
            deploys_production=deploys_production,
            requires_production_secret=requires_production_secret,
            enables_live_capital=enables_live_capital,
            claims_real_p11_acceptance=claims_real_p11_acceptance,
        )
        decision = self.evaluate(diagnosis, plan, owned_paths=owned_paths)
        return RepairProposalBundle(diagnosis=diagnosis, plan=plan, decision=decision)
