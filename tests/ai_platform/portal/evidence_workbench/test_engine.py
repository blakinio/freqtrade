from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ai_platform.portal.evidence_workbench import (
    EligibilityPolicy,
    EligibilityRequest,
    EvidenceClassification,
    EvidenceRecord,
    EvidenceRequirement,
    PaperEligibilityOutcome,
    RealismAssumption,
    ReasonCode,
    RuntimeMode,
    evaluate_paper_eligibility,
)
from ai_platform.portal.evidence_workbench.models import ProvenanceReference


NOW = datetime(2026, 8, 12, 8, tzinfo=UTC)
TENANT = "tenant-a"
BOT = "bot-a"
GENERATION = UUID("00000000-0000-0000-0000-000000000010")
RUN = UUID("00000000-0000-0000-0000-000000000020")
PROFILE = "1" * 64


def _policy(**overrides: object) -> EligibilityPolicy:
    values: dict[str, object] = {
        "policy_id": UUID("00000000-0000-0000-0000-000000000030"),
        "policy_version": 1,
        "tenant_id": TENANT,
        "paper_execution_profile_digest": PROFILE,
        "requirements": (
            EvidenceRequirement(
                evidence_type="walk_forward",
                max_age_seconds=3600,
                mandatory_validation=True,
                require_complete_run=True,
                require_supported_realism=True,
            ),
        ),
    }
    values.update(overrides)
    return EligibilityPolicy(**values)


def _request(policy: EligibilityPolicy, **overrides: object) -> EligibilityRequest:
    values: dict[str, object] = {
        "request_id": UUID("00000000-0000-0000-0000-000000000040"),
        "evaluated_at": NOW,
        "mode": RuntimeMode.PAPER,
        "tenant_id": TENANT,
        "bot_id": BOT,
        "generation_id": GENERATION,
        "run_id": RUN,
        "policy_digest": policy.identity(),
        "paper_execution_profile_digest": PROFILE,
    }
    values.update(overrides)
    return EligibilityRequest(**values)


def _evidence(**overrides: object) -> EvidenceRecord:
    values: dict[str, object] = {
        "slot_id": "walk-forward-primary",
        "evidence_type": "walk_forward",
        "producer_id": "validator",
        "producer_version": "1.0.0",
        "tenant_id": TENANT,
        "bot_id": BOT,
        "generation_id": GENERATION,
        "run_id": RUN,
        "generated_at": NOW - timedelta(minutes=10),
        "observed_at": NOW - timedelta(minutes=5),
        "available_at": NOW - timedelta(minutes=4),
        "classification": EvidenceClassification.AVAILABLE,
        "realism_assumption": RealismAssumption.SUPPORTED,
        "validation_passed": True,
        "run_complete": True,
        "profile_digest": PROFILE,
        "payload_digest": "2" * 64,
        "provenance": (
            ProvenanceReference(
                source_type="artifact", source_identity="run/20", source_digest="3" * 64
            ),
        ),
    }
    values.update(overrides)
    return EvidenceRecord(**values)


def _evaluate(evidence: tuple[EvidenceRecord, ...], **request_overrides: object):
    policy = _policy()
    return evaluate_paper_eligibility(_request(policy, **request_overrides), policy, evidence)


def test_identical_replay_is_byte_and_semantically_deterministic() -> None:
    record = _evidence()
    first = _evaluate((record,))
    second = _evaluate((record,))
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.outcome is PaperEligibilityOutcome.ELIGIBLE


@pytest.mark.parametrize(
    ("evidence", "reason"),
    [
        ((), ReasonCode.MISSING_EVIDENCE),
        ((_evidence(classification=EvidenceClassification.STALE),), ReasonCode.STALE_EVIDENCE),
        (
            (
                _evidence(
                    generated_at=NOW - timedelta(hours=3),
                    observed_at=NOW - timedelta(hours=2),
                    available_at=NOW - timedelta(hours=1),
                ),
            ),
            ReasonCode.STALE_EVIDENCE,
        ),
        ((_evidence(validation_passed=False),), ReasonCode.FAILED_MANDATORY_VALIDATION),
        ((_evidence(run_complete=False),), ReasonCode.INCOMPLETE_RUN),
        ((_evidence(provenance=()),), ReasonCode.INSUFFICIENT_PROVENANCE),
        (
            (_evidence(realism_assumption=RealismAssumption.UNKNOWN),),
            ReasonCode.UNSUPPORTED_REALISM_ASSUMPTION,
        ),
    ],
)
def test_fail_closed_evidence_states(
    evidence: tuple[EvidenceRecord, ...], reason: ReasonCode
) -> None:
    decision = _evaluate(evidence)
    assert decision.outcome is PaperEligibilityOutcome.INELIGIBLE
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    ("field", "value"),
    [("tenant_id", "tenant-b"), ("bot_id", "bot-b"), ("bot_id", None), ("run_id", None)],
)
def test_foreign_or_missing_identity_is_rejected(field: str, value: object) -> None:
    assert ReasonCode.IDENTITY_MISMATCH in _evaluate((_evidence(**{field: value}),)).reason_codes


def test_cross_generation_is_rejected() -> None:
    other = UUID("00000000-0000-0000-0000-000000000099")
    assert (
        ReasonCode.GENERATION_MISMATCH in _evaluate((_evidence(generation_id=other),)).reason_codes
    )


@pytest.mark.parametrize("mode", [RuntimeMode.SHADOW, RuntimeMode.LIVE])
def test_shadow_and_live_are_never_accepted_as_paper(mode: RuntimeMode) -> None:
    assert ReasonCode.NON_PAPER_MODE in _evaluate((_evidence(),), mode=mode).reason_codes


def test_policy_and_profile_identity_mismatch_fail_closed() -> None:
    policy = _policy()
    request = _request(policy, policy_digest="4" * 64, paper_execution_profile_digest="5" * 64)
    decision = evaluate_paper_eligibility(request, policy, (_evidence(),))
    assert ReasonCode.IDENTITY_MISMATCH in decision.reason_codes
    assert ReasonCode.POLICY_PROFILE_MISMATCH in decision.reason_codes


def test_reason_codes_are_stably_sorted() -> None:
    decision = _evaluate((), mode=RuntimeMode.LIVE)
    assert decision.reason_codes == tuple(sorted(decision.reason_codes, key=str))


def test_exact_duplicate_is_idempotent() -> None:
    record = _evidence()
    assert _evaluate((record, record)) == _evaluate((record,))


def test_conflicting_duplicate_is_not_silently_deduplicated() -> None:
    first = _evidence()
    second = _evidence(payload_digest="9" * 64)
    decision = _evaluate((first, second))
    assert ReasonCode.CONFLICTING_EVIDENCE in decision.reason_codes


def test_material_evidence_mutation_changes_decision_identity() -> None:
    first = _evaluate((_evidence(),))
    second = _evaluate((_evidence(payload_digest="9" * 64),))
    assert first.decision_id != second.decision_id
