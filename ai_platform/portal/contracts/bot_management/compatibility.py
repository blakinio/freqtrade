from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, model_validator

from ai_platform.portal.contracts.bot_management.templates import (
    CatalogVersionRef,
    MarketType,
    PolicyFamily,
    TradeDirection,
)
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex, UtcDateTime
from ai_platform.portal.contracts.environment import ExecutionMode


class CompatibilityStatus(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    REJECTED = "REJECTED"


class CompatibilityReasonCode(StrEnum):
    TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
    TEMPLATE_REVISION_STALE = "TEMPLATE_REVISION_STALE"
    STRATEGY_UNSUPPORTED = "STRATEGY_UNSUPPORTED"
    MODEL_UNSUPPORTED = "MODEL_UNSUPPORTED"
    MODEL_REQUIRED = "MODEL_REQUIRED"
    EXCHANGE_PROFILE_UNSUPPORTED = "EXCHANGE_PROFILE_UNSUPPORTED"
    MARKET_TYPE_UNSUPPORTED = "MARKET_TYPE_UNSUPPORTED"
    DIRECTION_UNSUPPORTED = "DIRECTION_UNSUPPORTED"
    EXECUTION_MODE_UNSUPPORTED = "EXECUTION_MODE_UNSUPPORTED"
    POLICY_FAMILY_MISSING = "POLICY_FAMILY_MISSING"
    POLICY_FAMILY_UNSUPPORTED = "POLICY_FAMILY_UNSUPPORTED"
    RUNTIME_VERSION_UNSUPPORTED = "RUNTIME_VERSION_UNSUPPORTED"
    RISK_POLICY_UNSUPPORTED = "RISK_POLICY_UNSUPPORTED"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    EVIDENCE_STALE = "EVIDENCE_STALE"


class CompatibilityEvidenceType(StrEnum):
    TEMPLATE = "template"
    STRATEGY = "strategy"
    MODEL = "model"
    EXCHANGE_PROFILE = "exchange_profile"
    RUNTIME = "runtime"
    RISK_POLICY = "risk_policy"


class CompatibilityEvidenceRef(ContractModel):
    evidence_type: CompatibilityEvidenceType
    evidence_id: NonEmptyStr
    version: NonEmptyStr
    sha256: Sha256Hex


class CompatibilitySelection(ContractModel):
    tenant_id: NonEmptyStr
    template_ref: CatalogVersionRef
    strategy_version: NonEmptyStr
    model_version: NonEmptyStr | None = None
    exchange_profile_version: NonEmptyStr
    market_type: MarketType
    direction: TradeDirection
    execution_mode: ExecutionMode
    runtime_version: NonEmptyStr
    risk_policy_version: NonEmptyStr
    policy_families: Annotated[tuple[PolicyFamily, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_policy_families(self) -> Self:
        values = [item.value for item in self.policy_families]
        if len(values) != len(set(values)):
            raise ValueError("policy_families must not contain duplicates")
        if values != sorted(values):
            raise ValueError("policy_families must use deterministic sorted order")
        return self


class BotCompatibilityDecision(ContractModel):
    decision_id: NonEmptyStr
    tenant_id: NonEmptyStr
    selection: CompatibilitySelection
    status: CompatibilityStatus
    reason_codes: tuple[CompatibilityReasonCode, ...] = ()
    evidence_refs: Annotated[tuple[CompatibilityEvidenceRef, ...], Field(min_length=1)]
    decided_at: UtcDateTime

    @model_validator(mode="after")
    def validate_decision(self) -> Self:
        if self.selection.tenant_id != self.tenant_id:
            raise ValueError("compatibility selection must belong to the decision tenant")
        reasons = [reason.value for reason in self.reason_codes]
        if len(reasons) != len(set(reasons)):
            raise ValueError("reason_codes must not contain duplicates")
        if reasons != sorted(reasons):
            raise ValueError("reason_codes must use deterministic sorted order")
        if self.status == CompatibilityStatus.COMPATIBLE and self.reason_codes:
            raise ValueError("compatible decision must not contain rejection reason codes")
        if self.status == CompatibilityStatus.REJECTED and not self.reason_codes:
            raise ValueError("rejected decision must contain at least one reason code")
        evidence_keys = [
            (item.evidence_type.value, item.evidence_id, item.version, item.sha256)
            for item in self.evidence_refs
        ]
        if len(evidence_keys) != len(set(evidence_keys)):
            raise ValueError("evidence_refs must not contain duplicates")
        if evidence_keys != sorted(evidence_keys):
            raise ValueError("evidence_refs must use deterministic sorted order")
        return self
