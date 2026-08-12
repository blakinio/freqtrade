from __future__ import annotations

import hashlib
import json

from ai_platform.portal.evidence_workbench.models import (
    EligibilityDecision,
    EligibilityPolicy,
    EligibilityRequest,
    EvidenceClassification,
    EvidenceRecord,
    PaperEligibilityOutcome,
    RealismAssumption,
    ReasonCode,
    RuntimeMode,
)


EVALUATOR_VERSION = "paper-evidence-eligibility-v2"


def _classification_reason(item: EvidenceRecord) -> ReasonCode | None:
    if item.classification is EvidenceClassification.AVAILABLE:
        return None
    return {
        EvidenceClassification.STALE: ReasonCode.STALE_EVIDENCE,
        EvidenceClassification.CONFLICTING: ReasonCode.CONFLICTING_EVIDENCE,
    }.get(item.classification, ReasonCode.INVALID_EVIDENCE)


def _record_reasons(
    item: EvidenceRecord,
    request: EligibilityRequest,
    policy: EligibilityPolicy,
    *,
    max_age_seconds: int | None,
    mandatory_validation: bool,
    require_complete_run: bool,
    require_supported_realism: bool,
) -> set[ReasonCode]:
    reasons: set[ReasonCode] = set()
    if item.tenant_id != request.tenant_id or item.bot_id != request.bot_id:
        reasons.add(ReasonCode.IDENTITY_MISMATCH)
    if item.generation_id != request.generation_id:
        reasons.add(ReasonCode.GENERATION_MISMATCH)
    if item.run_id != request.run_id:
        reasons.add(ReasonCode.IDENTITY_MISMATCH)
    if not item.provenance:
        reasons.add(ReasonCode.INSUFFICIENT_PROVENANCE)
    if item.profile_digest != policy.paper_execution_profile_digest:
        reasons.add(ReasonCode.POLICY_PROFILE_MISMATCH)
    classification_reason = _classification_reason(item)
    if classification_reason is not None:
        reasons.add(classification_reason)
    if max_age_seconds is not None:
        age = (request.evaluated_at - item.observed_at).total_seconds()
        if age < 0 or age > max_age_seconds:
            reasons.add(ReasonCode.STALE_EVIDENCE)
    if mandatory_validation and item.validation_passed is not True:
        reasons.add(ReasonCode.FAILED_MANDATORY_VALIDATION)
    if require_complete_run and item.run_complete is not True:
        reasons.add(ReasonCode.INCOMPLETE_RUN)
    if require_supported_realism and item.realism_assumption is not RealismAssumption.SUPPORTED:
        reasons.add(ReasonCode.UNSUPPORTED_REALISM_ASSUMPTION)
    return reasons


def _decision_identity(
    request_digest: str,
    policy_digest: str,
    evidence_digests: tuple[str, ...],
    evaluator_version: str = EVALUATOR_VERSION,
) -> str:
    canonical = json.dumps(
        {
            "evaluator_version": evaluator_version,
            "evidence_digests": evidence_digests,
            "policy_digest": policy_digest,
            "request_digest": request_digest,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def evaluate_paper_eligibility(
    request: EligibilityRequest,
    policy: EligibilityPolicy,
    evidence: tuple[EvidenceRecord, ...],
) -> EligibilityDecision:
    reasons: set[ReasonCode] = set()
    request_digest = request.identity()
    policy_digest = policy.identity()

    if request.mode is not RuntimeMode.PAPER:
        reasons.add(ReasonCode.NON_PAPER_MODE)
    if request.policy_digest != policy_digest:
        reasons.add(ReasonCode.IDENTITY_MISMATCH)
    if request.tenant_id != policy.tenant_id:
        reasons.add(ReasonCode.IDENTITY_MISMATCH)
    if request.paper_execution_profile_digest != policy.paper_execution_profile_digest:
        reasons.add(ReasonCode.POLICY_PROFILE_MISMATCH)

    by_slot: dict[str, list[EvidenceRecord]] = {}
    exact: dict[str, EvidenceRecord] = {}
    for item in evidence:
        exact.setdefault(item.identity(), item)
        by_slot.setdefault(item.slot_id, []).append(item)
    if any(len({item.identity() for item in items}) > 1 for items in by_slot.values()):
        reasons.add(ReasonCode.CONFLICTING_EVIDENCE)

    records = tuple(exact[key] for key in sorted(exact))

    # Every supplied record participates in the decision identity, so every record must first
    # satisfy the common scope/provenance/profile/classification fence. Requirement-specific
    # freshness and validation rules are layered on top below.
    for item in records:
        reasons.update(
            _record_reasons(
                item,
                request,
                policy,
                max_age_seconds=None,
                mandatory_validation=False,
                require_complete_run=False,
                require_supported_realism=False,
            )
        )

    for requirement in policy.requirements:
        matches = tuple(item for item in records if item.evidence_type == requirement.evidence_type)
        if not matches:
            reasons.add(ReasonCode.MISSING_EVIDENCE)
            continue
        for item in matches:
            reasons.update(
                _record_reasons(
                    item,
                    request,
                    policy,
                    max_age_seconds=requirement.max_age_seconds,
                    mandatory_validation=requirement.mandatory_validation,
                    require_complete_run=requirement.require_complete_run,
                    require_supported_realism=requirement.require_supported_realism,
                )
            )

    evidence_digests = tuple(sorted(exact))
    ordered_reasons = tuple(sorted(reasons, key=str))
    return EligibilityDecision(
        decision_id=_decision_identity(request_digest, policy_digest, evidence_digests),
        evaluator_version=EVALUATOR_VERSION,
        outcome=(
            PaperEligibilityOutcome.INELIGIBLE
            if ordered_reasons
            else PaperEligibilityOutcome.ELIGIBLE
        ),
        reason_codes=ordered_reasons,
        request_id=request.request_id,
        request_digest=request_digest,
        policy_id=policy.policy_id,
        policy_digest=policy_digest,
        evidence_digests=evidence_digests,
    )
