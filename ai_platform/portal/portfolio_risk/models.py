from __future__ import annotations

import hashlib
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.risk import TradeSide


NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]
PositiveDecimal = Annotated[Decimal, Field(gt=0)]
UnitDecimal = Annotated[Decimal, Field(ge=0, le=1)]
PositiveInt = Annotated[int, Field(gt=0, strict=True)]


def _digest(model: ContractModel) -> str:
    return hashlib.sha256(model.canonical_json().encode()).hexdigest()


class PortfolioRiskOutcome(StrEnum):
    ALLOW = "ALLOW"
    REJECT = "REJECT"
    SUSPEND = "SUSPEND"
    UNAVAILABLE = "UNAVAILABLE"


class SnapshotSourceHealth(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class BotBudgetAllocation(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    amount: NonNegativeDecimal


class PortfolioRiskPolicy(ContractModel):
    policy_id: UUID
    tenant_id: NonEmptyStr
    version: Annotated[int, Field(ge=1)]
    effective_at: UtcDateTime
    expires_at: UtcDateTime | None = None
    max_snapshot_age_seconds: PositiveInt
    max_gross_exposure: PositiveDecimal
    max_net_exposure: PositiveDecimal
    max_symbol_exposure: PositiveDecimal
    max_concentration: UnitDecimal
    max_correlation: UnitDecimal
    max_drawdown: UnitDecimal
    max_turnover: PositiveDecimal
    min_liquidity: PositiveDecimal

    @model_validator(mode="after")
    def validate_window(self) -> Self:
        if self.expires_at is not None and self.expires_at <= self.effective_at:
            raise ValueError("policy expiry must follow effective_at")
        return self

    def digest(self) -> str:
        return _digest(self)


class PortfolioBudget(ContractModel):
    budget_id: UUID
    tenant_id: NonEmptyStr
    revision: Annotated[int, Field(ge=1)]
    virtual_capital: PositiveDecimal
    allocations: tuple[BotBudgetAllocation, ...]
    effective_at: UtcDateTime
    expires_at: UtcDateTime | None = None

    @model_validator(mode="after")
    def validate_allocations(self) -> Self:
        identities = [(item.tenant_id, item.bot_id) for item in self.allocations]
        if identities != sorted(identities):
            raise ValueError("budget allocations must use deterministic tenant/bot ordering")
        if len(identities) != len(set(identities)):
            raise ValueError("budget allocations must be unique")
        if any(item.tenant_id != self.tenant_id for item in self.allocations):
            raise ValueError("budget allocation tenant must match budget tenant")
        if sum((item.amount for item in self.allocations), Decimal(0)) > self.virtual_capital:
            raise ValueError("bot allocations cannot exceed virtual capital")
        if self.expires_at is not None and self.expires_at <= self.effective_at:
            raise ValueError("budget expiry must follow effective_at")
        return self

    def digest(self) -> str:
        return _digest(self)

    def allocation_for(self, bot_id: str) -> Decimal | None:
        return next((item.amount for item in self.allocations if item.bot_id == bot_id), None)


class PortfolioPosition(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    symbol: NonEmptyStr
    signed_notional: Decimal


class CorrelationEvidence(ContractModel):
    left_symbol: NonEmptyStr
    right_symbol: NonEmptyStr
    correlation: Annotated[Decimal, Field(ge=-1, le=1)]

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.left_symbol >= self.right_symbol:
            raise ValueError("correlation symbols must be distinct and sorted")
        return self


class PortfolioRiskSnapshot(ContractModel):
    snapshot_id: UUID
    tenant_id: NonEmptyStr
    observed_at: UtcDateTime
    source_health: SnapshotSourceHealth
    drift_detected: bool
    positions: tuple[PortfolioPosition, ...]
    correlations: tuple[CorrelationEvidence, ...] | None
    drawdown: UnitDecimal | None
    turnover: NonNegativeDecimal | None
    liquidity_by_symbol: tuple[tuple[NonEmptyStr, NonNegativeDecimal], ...] | None
    portfolio_suspended: bool
    suspended_bot_ids: tuple[NonEmptyStr, ...]

    @model_validator(mode="after")
    def validate_order_and_tenant(self) -> Self:
        position_keys = [(p.bot_id, p.symbol) for p in self.positions]
        if position_keys != sorted(position_keys) or len(position_keys) != len(set(position_keys)):
            raise ValueError("positions must use unique deterministic bot/symbol ordering")
        if any(position.tenant_id != self.tenant_id for position in self.positions):
            raise ValueError("position tenant must match snapshot tenant")
        if tuple(sorted(self.suspended_bot_ids)) != self.suspended_bot_ids:
            raise ValueError("suspended bots must use deterministic ordering")
        if self.correlations is not None:
            keys = [(c.left_symbol, c.right_symbol) for c in self.correlations]
            if keys != sorted(keys) or len(keys) != len(set(keys)):
                raise ValueError("correlations must use unique deterministic ordering")
        if self.liquidity_by_symbol is not None:
            keys = [item[0] for item in self.liquidity_by_symbol]
            if keys != sorted(keys) or len(keys) != len(set(keys)):
                raise ValueError("liquidity must use unique deterministic symbol ordering")
        return self

    def digest(self) -> str:
        return _digest(self)


class AllocationRequest(ContractModel):
    request_id: UUID
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    symbol: NonEmptyStr
    side: TradeSide
    notional: PositiveDecimal
    policy_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    budget_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    requested_at: UtcDateTime
    ai_suggested_outcome: NonEmptyStr | None = None

    def digest(self) -> str:
        return _digest(self)


class PortfolioRiskDecision(ContractModel):
    decision_id: UUID
    outcome: PortfolioRiskOutcome
    reason_codes: tuple[NonEmptyStr, ...]
    request_id: UUID
    request_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    policy_id: UUID
    policy_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    budget_id: UUID
    budget_revision: Annotated[int, Field(ge=1)]
    budget_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    snapshot_id: UUID
    snapshot_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    evaluated_at: UtcDateTime
    metrics: tuple[tuple[NonEmptyStr, str], ...]

    @model_validator(mode="after")
    def validate_explanation(self) -> Self:
        if not self.reason_codes:
            raise ValueError("portfolio decision requires reason codes")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise ValueError("reason codes must be unique and deterministically ordered")
        keys = [item[0] for item in self.metrics]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("metrics must use unique deterministic ordering")
        return self

    def digest(self) -> str:
        return _digest(self)
