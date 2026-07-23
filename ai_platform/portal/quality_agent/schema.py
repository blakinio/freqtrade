from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr


class FailureClassification(StrEnum):
    PRODUCT_DEFECT = "product_defect"
    TEST_DEFECT = "test_defect"
    ENVIRONMENT_DEFECT = "environment_defect"
    DEPENDENCY_OUTAGE = "dependency_outage"
    FLAKY_OR_AMBIGUOUS = "flaky_or_ambiguous"


class DiagnosisConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RepairRejectionReason(StrEnum):
    EVIDENCE_NOT_REPRODUCED = "evidence_not_reproduced"
    MISSING_REGRESSION_TEST = "missing_regression_test"
    PATH_OUTSIDE_OWNERSHIP = "path_outside_ownership"
    INVALID_BRANCH = "invalid_branch"
    MISSING_VALIDATION = "missing_validation"
    SAFETY_ASSERTION_WEAKENING = "safety_assertion_weakening"
    PRODUCTION_DEPLOYMENT = "production_deployment"
    PRODUCTION_CREDENTIAL_ACCESS = "production_credential_access"
    LIVE_CAPITAL_ENABLEMENT = "live_capital_enablement"
    REAL_P11_ACCEPTANCE_CLAIM = "real_p11_acceptance_claim"


class DiagnosisRecord(ContractModel):
    scenario_id: NonEmptyStr
    correlation_id: UUID
    first_failure_stage: NonEmptyStr
    reason_code: NonEmptyStr
    classification: FailureClassification
    likely_layer: NonEmptyStr
    reproducible: bool
    confidence: DiagnosisConfidence
    evidence_kind: Literal["simulated"] = "simulated"
    evidence_refs: tuple[NonEmptyStr, ...] = ()


class RepairPlan(ContractModel):
    task_id: NonEmptyStr
    branch_name: NonEmptyStr
    regression_test_paths: tuple[NonEmptyStr, ...]
    proposed_changed_paths: tuple[NonEmptyStr, ...]
    validation_commands: tuple[NonEmptyStr, ...]
    pr_summary: NonEmptyStr
    evidence_kind: Literal["simulated"] = "simulated"
    weakens_safety_assertion: bool = False
    deploys_production: bool = False
    requires_production_secret: bool = False
    enables_live_capital: bool = False
    claims_real_p11_acceptance: bool = False


class RepairDecision(ContractModel):
    allowed: bool
    reason_codes: tuple[RepairRejectionReason, ...] = ()


class RepairProposalBundle(ContractModel):
    diagnosis: DiagnosisRecord
    plan: RepairPlan
    decision: RepairDecision
