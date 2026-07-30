from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.simulator.costs import ExecutionCostBreakdown, ExecutionCostModel
from ai_platform.portal.simulator.funding import FundingAccrual, FundingEvent
from ai_platform.portal.simulator.gap_stop import GapStopModel, GapStopResolution
from ai_platform.portal.simulator.latency import LatencyModel, LatencyResolution


PositiveDecimal = Annotated[Decimal, Field(gt=0)]
NonNegativeSeed = Annotated[int, Field(ge=0)]


class MarketTick(ContractModel):
    occurred_at: UtcDateTime
    pair: NonEmptyStr
    price: PositiveDecimal


class ScenarioManifest(ContractModel):
    scenario_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: PositiveDecimal
    environment: Environment
    initial_equity: PositiveDecimal
    entry_tick: MarketTick
    exit_tick: MarketTick
    seed: NonNegativeSeed = 0
    cost_model: ExecutionCostModel = Field(default_factory=ExecutionCostModel)
    latency_model: LatencyModel = Field(default_factory=LatencyModel)
    gap_stop_model: GapStopModel = Field(default_factory=GapStopModel)
    funding_events: tuple[FundingEvent, ...] = ()
    market_ticks: tuple[MarketTick, ...] = ()

    @model_validator(mode="after")
    def validate_scenario_timeline(self) -> Self:
        if self.entry_tick.pair != self.pair or self.exit_tick.pair != self.pair:
            raise ValueError("scenario entry and exit ticks must match the manifest pair")
        if self.exit_tick.occurred_at <= self.entry_tick.occurred_at:
            raise ValueError("scenario exit tick must occur after the entry tick")

        reserved_times = {self.entry_tick.occurred_at, self.exit_tick.occurred_at}
        previous_tick_at = None
        for tick in self.market_ticks:
            if tick.pair != self.pair:
                raise ValueError("all scenario market ticks must match the manifest pair")
            if tick.occurred_at in reserved_times:
                raise ValueError(
                    "additional market ticks cannot duplicate entry or exit timestamps"
                )
            if previous_tick_at is not None and tick.occurred_at <= previous_tick_at:
                raise ValueError("additional market ticks must be strictly ordered")
            previous_tick_at = tick.occurred_at

        previous_funding_at = None
        for event in self.funding_events:
            if previous_funding_at is not None and event.occurred_at <= previous_funding_at:
                raise ValueError("funding events must be strictly ordered")
            previous_funding_at = event.occurred_at

        stop_price = self.gap_stop_model.stop_price
        if stop_price is not None:
            if self.side is TradeSide.BUY and stop_price >= self.entry_tick.price:
                raise ValueError("BUY stop price must be below the entry market price")
            if self.side is TradeSide.SELL and stop_price <= self.entry_tick.price:
                raise ValueError("SELL stop price must be above the entry market price")
        return self


class SimulationEvidence(ContractModel):
    scenario_id: NonEmptyStr
    seed: NonNegativeSeed
    order_id: NonEmptyStr
    trade_id: NonEmptyStr
    outcome_id: UUID
    entry_latency: LatencyResolution
    exit_latency: LatencyResolution
    costs: ExecutionCostBreakdown
    funding_accruals: tuple[FundingAccrual, ...]
    funding_cash_flow: Decimal
    gross_pnl: Decimal
    realized_pnl: Decimal
    exit_reason: NonEmptyStr
    stop_resolution: GapStopResolution

    def canonical_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


class SimulatorEvidenceBundle(ContractModel):
    scenario_id: NonEmptyStr
    correlation_id: UUID
    order_id: NonEmptyStr
    trade_id: NonEmptyStr
    analysis_id: UUID
    insight_id: UUID
    hypothesis_id: UUID
    experiment_id: UUID
    candidate_id: UUID
    active_model_before: NonEmptyStr
    active_model_after: NonEmptyStr
    candidate_model_version_id: NonEmptyStr
    realized_pnl: Decimal


class ScenarioFailureEvidence(ContractModel):
    scenario_id: NonEmptyStr
    correlation_id: UUID
    stage: NonEmptyStr
    reason_code: NonEmptyStr


class ScenarioRunReport(ContractModel):
    passed: bool
    evidence: SimulatorEvidenceBundle | None = None
    failure: ScenarioFailureEvidence | None = None
