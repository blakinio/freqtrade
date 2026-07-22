from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, model_validator

from ai_platform.portal.contracts.common import (
    ContractModel,
    CorrelationContext,
    NonEmptyStr,
    Sha256Hex,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import Environment


PositiveDecimal = Annotated[Decimal, Field(gt=0)]


class RiskPolicyLifecycleState(StrEnum):
    DRAFT = "DRAFT"
    PROMOTED = "PROMOTED"
    DEPRECATED = "DEPRECATED"


class RiskPolicyVersion(ContractModel):
    risk_policy_version_id: NonEmptyStr
    tenant_id: NonEmptyStr
    policy_hash: Sha256Hex
    state: RiskPolicyLifecycleState
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime


class TradeSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class RiskDecisionOutcome(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Prediction(ContractModel):
    prediction_id: UUID
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    model_version: NonEmptyStr
    value: Decimal
    created_at: UtcDateTime
    context: CorrelationContext


class TradeIntent(ContractModel):
    trade_intent_id: UUID
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    prediction_id: UUID | None = None
    source_actor_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: PositiveDecimal
    environment: Environment
    created_at: UtcDateTime
    context: CorrelationContext


class RiskLimitEvaluation(ContractModel):
    limit_name: NonEmptyStr
    configured_value: NonEmptyStr
    observed_value: NonEmptyStr
    passed: bool


class RiskDecision(ContractModel):
    risk_decision_id: UUID
    tenant_id: NonEmptyStr
    trade_intent_id: UUID
    risk_policy_version: NonEmptyStr
    decision: RiskDecisionOutcome
    reason_codes: tuple[NonEmptyStr, ...]
    evaluated_limits: tuple[RiskLimitEvaluation, ...]
    occurred_at: UtcDateTime
    context: CorrelationContext

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        if not self.reason_codes:
            raise ValueError("risk decision requires at least one reason code")
        if not self.evaluated_limits:
            raise ValueError("risk decision requires evaluated limits")
        return self


class ApprovedExecutionIntent(ContractModel):
    execution_intent_id: UUID
    tenant_id: NonEmptyStr
    trade_intent: TradeIntent
    risk_decision: RiskDecision
    created_at: UtcDateTime
    context: CorrelationContext

    @model_validator(mode="after")
    def validate_approval(self) -> Self:
        if self.risk_decision.decision is not RiskDecisionOutcome.APPROVED:
            raise ValueError("approved execution intent requires an approved risk decision")
        if self.trade_intent.tenant_id != self.tenant_id or self.risk_decision.tenant_id != self.tenant_id:
            raise ValueError("trade intent and risk decision must belong to the execution tenant")
        if self.risk_decision.trade_intent_id != self.trade_intent.trade_intent_id:
            raise ValueError("risk decision must reference the same trade intent")
        if self.trade_intent.context.correlation_id != self.context.correlation_id:
            raise ValueError("trade intent correlation_id must propagate to approved execution")
        if self.risk_decision.context.correlation_id != self.context.correlation_id:
            raise ValueError("risk decision correlation_id must propagate to approved execution")
        return self


class RejectedExecutionIntent(ContractModel):
    rejection_id: UUID
    tenant_id: NonEmptyStr
    trade_intent: TradeIntent
    risk_decision: RiskDecision
    created_at: UtcDateTime
    context: CorrelationContext

    @model_validator(mode="after")
    def validate_rejection(self) -> Self:
        if self.risk_decision.decision is not RiskDecisionOutcome.REJECTED:
            raise ValueError("rejected execution intent requires a rejected risk decision")
        if self.trade_intent.tenant_id != self.tenant_id or self.risk_decision.tenant_id != self.tenant_id:
            raise ValueError("trade intent and risk decision must belong to the rejection tenant")
        if self.risk_decision.trade_intent_id != self.trade_intent.trade_intent_id:
            raise ValueError("risk decision must reference the same trade intent")
        if self.trade_intent.context.correlation_id != self.context.correlation_id:
            raise ValueError("trade intent correlation_id must propagate to rejection")
        if self.risk_decision.context.correlation_id != self.context.correlation_id:
            raise ValueError("risk decision correlation_id must propagate to rejection")
        return self
