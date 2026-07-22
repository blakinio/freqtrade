from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.risk import TradeSide


class MarketTick(ContractModel):
    occurred_at: UtcDateTime
    pair: NonEmptyStr
    price: Decimal


class ScenarioManifest(ContractModel):
    scenario_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: Decimal
    environment: Environment
    initial_equity: Decimal
    entry_tick: MarketTick
    exit_tick: MarketTick


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
