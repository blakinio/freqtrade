from __future__ import annotations

from decimal import Decimal

from ai_platform.portal.contracts.audit import AuditEvent
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.execution import OrderState, TradeState
from ai_platform.portal.contracts.risk import RiskDecision, TradeSide
from ai_platform.portal.execution.private_read import RuntimeReadFreshness, RuntimeReadKind
from ai_platform.portal.intelligence.schema import ReconciliationStatus


class OperationalOrder(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    order_id: NonEmptyStr
    execution_intent_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    state: OrderState
    amount: Decimal
    created_at: UtcDateTime
    source_order_id: NonEmptyStr | None = None
    source_trade_id: NonEmptyStr | None = None
    source_updated_at: UtcDateTime | None = None
    observed_at: UtcDateTime | None = None
    last_reconciled_at: UtcDateTime | None = None
    freshness: RuntimeReadFreshness = RuntimeReadFreshness.CURRENT
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.SYNCED
    reason_code: NonEmptyStr | None = None


class OperationalPosition(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    position_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: Decimal
    opened_at: UtcDateTime
    source_position_id: NonEmptyStr | None = None
    source_updated_at: UtcDateTime | None = None
    observed_at: UtcDateTime | None = None
    last_reconciled_at: UtcDateTime | None = None
    freshness: RuntimeReadFreshness = RuntimeReadFreshness.CURRENT
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.SYNCED
    reason_code: NonEmptyStr | None = None


class OperationalTrade(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    trade_id: NonEmptyStr
    source_trade_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    state: TradeState
    amount: Decimal
    opened_at: UtcDateTime
    closed_at: UtcDateTime | None = None
    realized_pnl: Decimal | None = None
    fees: Decimal | None = None
    exit_reason: NonEmptyStr | None = None
    source_updated_at: UtcDateTime
    observed_at: UtcDateTime
    last_reconciled_at: UtcDateTime
    freshness: RuntimeReadFreshness
    reconciliation_status: ReconciliationStatus
    reason_code: NonEmptyStr | None = None


class OperationalSourceStatus(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    kind: RuntimeReadKind
    source_observed_at: UtcDateTime | None = None
    observed_at: UtcDateTime
    last_reconciled_at: UtcDateTime
    freshness: RuntimeReadFreshness
    reconciliation_status: ReconciliationStatus
    complete: bool
    record_count: int
    reason_code: NonEmptyStr | None = None


class RuntimeEvidenceSnapshot(ContractModel):
    positions: tuple[OperationalPosition, ...]
    orders: tuple[OperationalOrder, ...]
    trades: tuple[OperationalTrade, ...]
    source_statuses: tuple[OperationalSourceStatus, ...]


class TradeHistoryEntry(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    trade_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: Decimal
    realized_pnl: Decimal
    fees: Decimal
    exit_reason: NonEmptyStr
    opened_at: UtcDateTime
    closed_at: UtcDateTime
    reconciliation_status: ReconciliationStatus
    analysis_id: NonEmptyStr


class PerformanceSummary(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    realized_pnl: Decimal
    fees: Decimal
    net_pnl: Decimal
    trade_count: int
    winning_trades: int
    losing_trades: int
    reconciliation_gaps: int


class ExecutionActivityEntry(ContractModel):
    audit: AuditEvent


class OperationalSnapshot(ContractModel):
    positions: tuple[OperationalPosition, ...]
    orders: tuple[OperationalOrder, ...]
    trades: tuple[TradeHistoryEntry, ...]
    performance: tuple[PerformanceSummary, ...]
    risk_events: tuple[RiskDecision, ...]
    execution_activity: tuple[ExecutionActivityEntry, ...]
