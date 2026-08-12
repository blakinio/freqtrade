from __future__ import annotations

import hashlib
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex, UtcDateTime


PositiveInt = Annotated[int, Field(gt=0)]


def digest(model: ContractModel) -> str:
    return hashlib.sha256(model.canonical_json().encode()).hexdigest()


class RuntimeMode(StrEnum):
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    LIVE = "LIVE"


class EvidenceClassification(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    INVALID = "INVALID"
    CONFLICTING = "CONFLICTING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RealismAssumption(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class PaperEligibilityOutcome(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


class ReasonCode(StrEnum):
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    FAILED_MANDATORY_VALIDATION = "FAILED_MANDATORY_VALIDATION"
    GENERATION_MISMATCH = "GENERATION_MISMATCH"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    INCOMPLETE_RUN = "INCOMPLETE_RUN"
    INSUFFICIENT_PROVENANCE = "INSUFFICIENT_PROVENANCE"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    NON_PAPER_MODE = "NON_PAPER_MODE"
    POLICY_PROFILE_MISMATCH = "POLICY_PROFILE_MISMATCH"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    UNSUPPORTED_REALISM_ASSUMPTION = "UNSUPPORTED_REALISM_ASSUMPTION"


class ProvenanceReference(ContractModel):
    source_type: NonEmptyStr
    source_identity: NonEmptyStr
    source_digest: Sha256Hex


class EvidenceRecord(ContractModel):
    slot_id: NonEmptyStr
    evidence_type: NonEmptyStr
    producer_id: NonEmptyStr
    producer_version: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr | None = None
    generation_id: UUID | None = None
    run_id: UUID | None = None
    generated_at: UtcDateTime
    observed_at: UtcDateTime
    available_at: UtcDateTime
    classification: EvidenceClassification
    realism_assumption: RealismAssumption = RealismAssumption.NOT_APPLICABLE
    validation_passed: bool | None = None
    run_complete: bool | None = None
    profile_digest: Sha256Hex | None = None
    payload_digest: Sha256Hex
    provenance: tuple[ProvenanceReference, ...]

    @model_validator(mode="after")
    def validate_temporal_and_provenance_order(self) -> Self:
        if self.observed_at < self.generated_at or self.available_at < self.observed_at:
            raise ValueError("evidence timestamps must satisfy generated <= observed <= available")
        keys = [
            (item.source_type, item.source_identity, item.source_digest) for item in self.provenance
        ]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("provenance must use unique deterministic ordering")
        return self

    def identity(self) -> str:
        return digest(self)


class EvidenceRequirement(ContractModel):
    evidence_type: NonEmptyStr
    max_age_seconds: PositiveInt | None = None
    mandatory_validation: bool = False
    require_complete_run: bool = False
    require_supported_realism: bool = False


class EligibilityPolicy(ContractModel):
    policy_id: UUID
    policy_version: PositiveInt
    tenant_id: NonEmptyStr
    paper_execution_profile_digest: Sha256Hex
    requirements: tuple[EvidenceRequirement, ...]

    @model_validator(mode="after")
    def validate_requirements(self) -> Self:
        keys = [item.evidence_type for item in self.requirements]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("requirements must use unique deterministic evidence-type ordering")
        return self

    def identity(self) -> str:
        return digest(self)


class EligibilityRequest(ContractModel):
    request_id: UUID
    evaluated_at: UtcDateTime
    mode: RuntimeMode
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    generation_id: UUID
    run_id: UUID
    policy_digest: Sha256Hex
    paper_execution_profile_digest: Sha256Hex

    def identity(self) -> str:
        return digest(self)


class EligibilityDecision(ContractModel):
    decision_id: Sha256Hex
    outcome: PaperEligibilityOutcome
    reason_codes: tuple[ReasonCode, ...]
    request_id: UUID
    request_digest: Sha256Hex
    policy_id: UUID
    policy_digest: Sha256Hex
    evidence_digests: tuple[Sha256Hex, ...]

    @model_validator(mode="after")
    def validate_deterministic_order(self) -> Self:
        if self.reason_codes != tuple(sorted(set(self.reason_codes), key=str)):
            raise ValueError("reason codes must be unique and deterministically ordered")
        if self.evidence_digests != tuple(sorted(set(self.evidence_digests))):
            raise ValueError("evidence digests must be unique and deterministically ordered")
        return self
