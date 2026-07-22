from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from ai_platform.portal.contracts.bots import BotInstance, BotObservedState
from ai_platform.portal.contracts.common import (
    ContractModel,
    CorrelationContext,
    NonEmptyStr,
    UtcDateTime,
)
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent, TradeSide


class RuntimeHealthState(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class OrderState(StrEnum):
    SUBMITTED = "SUBMITTED"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


class TradeState(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class RuntimeStatus(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    runtime_id: NonEmptyStr
    observed_state: BotObservedState
    observed_at: UtcDateTime


class ExecutionHealth(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    runtime_id: NonEmptyStr
    health: RuntimeHealthState
    observed_at: UtcDateTime
    reason_code: NonEmptyStr | None = None


class OpenPosition(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    position_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: Decimal
    opened_at: UtcDateTime


class OrderRecord(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    order_id: NonEmptyStr
    execution_intent_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    state: OrderState
    amount: Decimal
    created_at: UtcDateTime


class TradeRecord(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    trade_id: NonEmptyStr
    pair: NonEmptyStr
    state: TradeState
    opened_at: UtcDateTime
    closed_at: UtcDateTime | None = None


class ExecutionAdapter(Protocol):
    """Private execution boundary; never implemented directly by browser-facing code."""

    def provision_bot(self, bot: BotInstance, context: CorrelationContext) -> RuntimeStatus: ...

    def start_bot(self, bot: BotInstance, context: CorrelationContext) -> RuntimeStatus: ...

    def pause_bot(
        self, tenant_id: NonEmptyStr, bot_id: NonEmptyStr, context: CorrelationContext
    ) -> RuntimeStatus: ...

    def stop_bot(
        self, tenant_id: NonEmptyStr, bot_id: NonEmptyStr, context: CorrelationContext
    ) -> RuntimeStatus: ...

    def get_health(
        self, tenant_id: NonEmptyStr, bot_id: NonEmptyStr, context: CorrelationContext
    ) -> ExecutionHealth: ...

    def get_runtime_status(
        self, tenant_id: NonEmptyStr, bot_id: NonEmptyStr, context: CorrelationContext
    ) -> RuntimeStatus: ...

    def submit_approved_intent(
        self, intent: ApprovedExecutionIntent, context: CorrelationContext
    ) -> OrderRecord: ...

    def get_open_positions(
        self, tenant_id: NonEmptyStr, bot_id: NonEmptyStr, context: CorrelationContext
    ) -> tuple[OpenPosition, ...]: ...

    def get_orders(
        self, tenant_id: NonEmptyStr, bot_id: NonEmptyStr, context: CorrelationContext
    ) -> tuple[OrderRecord, ...]: ...

    def get_trades(
        self, tenant_id: NonEmptyStr, bot_id: NonEmptyStr, context: CorrelationContext
    ) -> tuple[TradeRecord, ...]: ...
