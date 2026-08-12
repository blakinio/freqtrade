"""Deterministic, PAPER-only evidence eligibility producer."""

from ai_platform.portal.evidence_workbench.engine import evaluate_paper_eligibility
from ai_platform.portal.evidence_workbench.models import (
    EligibilityDecision,
    EligibilityPolicy,
    EligibilityRequest,
    EvidenceClassification,
    EvidenceRecord,
    EvidenceRequirement,
    PaperEligibilityOutcome,
    RealismAssumption,
    ReasonCode,
    RuntimeMode,
)


__all__ = [
    "EligibilityDecision",
    "EligibilityPolicy",
    "EligibilityRequest",
    "EvidenceClassification",
    "EvidenceRecord",
    "EvidenceRequirement",
    "PaperEligibilityOutcome",
    "ReasonCode",
    "RealismAssumption",
    "RuntimeMode",
    "evaluate_paper_eligibility",
]
