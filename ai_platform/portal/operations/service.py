from __future__ import annotations

import hashlib
from collections import defaultdict
from decimal import Decimal

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent
from ai_platform.portal.contracts.execution import OrderRecord, TradeState
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.risk import RiskDecision
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.execution.private_read import (
    OrderReadResult,
    PositionReadResult,
    PrivateRuntimeSnapshot,
    RuntimeReadFreshness,
    RuntimeReadKind,
    RuntimeReadReconciliationStatus,
    RuntimeReadStatus,
    TradeReadResult,
)
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.intelligence.service import TradeIntelligenceService
from ai_platform.portal.operations.repository import OperationalRepository
from ai_platform.portal.operations.schema import (
    ExecutionActivityEntry,
    OperationalOrder,
    OperationalPosition,
    OperationalSourceStatus,
    OperationalTrade,
    PerformanceSummary,
    RuntimeEvidenceSnapshot,
    TradeHistoryEntry,
)
from ai_platform.portal.risk.repository import RiskRepository
from ai_platform.portal.security.authorization import PermissionDeniedError, require_permission


_EXECUTION_AUDIT_ACTIONS = {
    AuditAction.BOT_START_REQUESTED,
    AuditAction.BOT_PAUSE_REQUESTED,
    AuditAction.BOT_STOP_REQUESTED,
    AuditAction.BOT_STARTED,
    AuditAction.BOT_STOPPED,
    AuditAction.MANUAL_TRADE_INTENT,
    AuditAction.KILL_SWITCH_ACTIVATED,
    AuditAction.KILL_SWITCH_RELEASED,
}


class OperationalReconciliationConflictError(RuntimeError):
    pass


class OperationalReadService:
    def __init__(
        self,
        session_factory: SessionFactory,
        repository: OperationalRepository | None = None,
        bot_repository: BotRepository | None = None,
        risk_repository: RiskRepository | None = None,
        intelligence_service: TradeIntelligenceService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or OperationalRepository()
        self._bot_repository = bot_repository or BotRepository()
        self._risk_repository = risk_repository or RiskRepository()
        self._intelligence = intelligence_service or TradeIntelligenceService(session_factory)

    def record_filled_order(
        self,
        context: RequestContext,
        order: OrderRecord,
        *,
        source_runtime_id: str,
    ) -> OperationalPosition:
        require_permission(context.permissions, Permission.TRADE_MANUAL_EXECUTE)
        self._require_tenant(context, order.tenant_id)
        position = OperationalPosition(
            tenant_id=order.tenant_id,
            bot_id=order.bot_id,
            source_runtime_id=source_runtime_id,
            position_id=f"position:{order.order_id}",
            pair=order.pair,
            side=order.side,
            amount=order.amount,
            opened_at=order.created_at,
            source_position_id=f"position:{order.order_id}",
            source_updated_at=order.created_at,
            observed_at=order.created_at,
            last_reconciled_at=order.created_at,
        )
        operational_order = OperationalOrder(
            tenant_id=order.tenant_id,
            bot_id=order.bot_id,
            source_runtime_id=source_runtime_id,
            order_id=order.order_id,
            execution_intent_id=order.execution_intent_id,
            pair=order.pair,
            side=order.side,
            state=order.state,
            amount=order.amount,
            created_at=order.created_at,
            source_order_id=order.order_id,
            source_updated_at=order.created_at,
            observed_at=order.created_at,
            last_reconciled_at=order.created_at,
        )
        with self._session_factory() as session, session.begin():
            self._repository.upsert_order(session, operational_order)
            self._repository.upsert_position(session, position)
        return position

    def reconcile_private_runtime_snapshot(
        self,
        context: RequestContext,
        snapshot: PrivateRuntimeSnapshot,
        *,
        expected_runtime_id: str,
    ) -> RuntimeEvidenceSnapshot:
        self._require_tenant(context, snapshot.tenant_id)
        if snapshot.source_runtime_id != expected_runtime_id:
            raise PermissionDeniedError("runtime scope mismatch")
        self._validate_snapshot_scope(snapshot)

        with self._session_factory() as session, session.begin():
            if self._bot_repository.get_bot(session, context.tenant_id, snapshot.bot_id) is None:
                raise OperationalReconciliationConflictError("bot does not exist in tenant scope")

            self._reconcile_positions(session, snapshot.positions)
            self._reconcile_orders(session, snapshot.orders)
            self._reconcile_trades(session, snapshot.trades)
            for read_status in (
                snapshot.positions.status,
                snapshot.orders.status,
                snapshot.trades.status,
            ):
                self._repository.upsert_source_status(
                    session,
                    self._source_status(read_status),
                )

        return self.runtime_evidence(context)

    def close_position(self, context: RequestContext, position_id: str) -> None:
        require_permission(context.permissions, Permission.TRADE_MANUAL_EXECUTE)
        with self._session_factory() as session, session.begin():
            self._repository.delete_position(session, context.tenant_id, position_id)

    def list_positions(self, context: RequestContext) -> tuple[OperationalPosition, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            return self._repository.list_positions(session, context.tenant_id)

    def list_orders(self, context: RequestContext) -> tuple[OperationalOrder, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            return self._repository.list_orders(session, context.tenant_id)

    def list_runtime_trades(self, context: RequestContext) -> tuple[OperationalTrade, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            return self._repository.list_trades(session, context.tenant_id)

    def runtime_evidence(self, context: RequestContext) -> RuntimeEvidenceSnapshot:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            return RuntimeEvidenceSnapshot(
                positions=self._repository.list_positions(session, context.tenant_id),
                orders=self._repository.list_orders(session, context.tenant_id),
                trades=self._repository.list_trades(session, context.tenant_id),
                source_statuses=self._repository.list_source_statuses(
                    session,
                    context.tenant_id,
                ),
            )

    def list_trades(self, context: RequestContext) -> tuple[TradeHistoryEntry, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        analyses = self._intelligence.list_analyses(context)
        return tuple(
            TradeHistoryEntry(
                tenant_id=analysis.tenant_id,
                bot_id=analysis.outcome.bot_id,
                trade_id=analysis.outcome.trade_id,
                source_runtime_id=analysis.outcome.source_runtime_id,
                pair=analysis.outcome.pair,
                side=analysis.snapshot.side,
                amount=analysis.snapshot.amount,
                realized_pnl=analysis.outcome.realized_pnl,
                fees=analysis.outcome.fees,
                exit_reason=analysis.outcome.exit_reason,
                opened_at=analysis.outcome.opened_at,
                closed_at=analysis.outcome.closed_at,
                reconciliation_status=analysis.outcome.reconciliation_status,
                analysis_id=str(analysis.analysis_id),
            )
            for analysis in analyses
        )

    def list_performance(self, context: RequestContext) -> tuple[PerformanceSummary, ...]:
        trades = self.list_trades(context)
        realized: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        fees: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        wins: dict[str, int] = defaultdict(int)
        losses: dict[str, int] = defaultdict(int)
        gaps: dict[str, int] = defaultdict(int)
        counts: dict[str, int] = defaultdict(int)
        for trade in trades:
            counts[trade.bot_id] += 1
            realized[trade.bot_id] += trade.realized_pnl
            fees[trade.bot_id] += trade.fees
            if trade.realized_pnl >= 0:
                wins[trade.bot_id] += 1
            else:
                losses[trade.bot_id] += 1
            if trade.reconciliation_status.value != "SYNCED":
                gaps[trade.bot_id] += 1
        return tuple(
            PerformanceSummary(
                tenant_id=context.tenant_id,
                bot_id=bot_id,
                realized_pnl=realized[bot_id],
                fees=fees[bot_id],
                net_pnl=realized[bot_id] - fees[bot_id],
                trade_count=counts[bot_id],
                winning_trades=wins[bot_id],
                losing_trades=losses[bot_id],
                reconciliation_gaps=gaps[bot_id],
            )
            for bot_id in sorted(counts)
        )

    def list_risk_events(self, context: RequestContext) -> tuple[RiskDecision, ...]:
        require_permission(context.permissions, Permission.BOT_READ)
        with self._session_factory() as session:
            return self._risk_repository.list_risk_decisions(session, context.tenant_id)

    def list_audit_events(self, context: RequestContext) -> tuple[AuditEvent, ...]:
        require_permission(context.permissions, Permission.AUDIT_READ)
        with self._session_factory() as session:
            return self._bot_repository.list_audit_events(session, context.tenant_id)

    def list_execution_activity(
        self,
        context: RequestContext,
    ) -> tuple[ExecutionActivityEntry, ...]:
        events = self.list_audit_events(context)
        return tuple(
            ExecutionActivityEntry(audit=event)
            for event in events
            if event.action in _EXECUTION_AUDIT_ACTIONS
        )

    def _reconcile_positions(self, session: object, result: PositionReadResult) -> None:
        status = result.status
        existing = self._repository.list_positions_for_runtime(
            session,
            status.tenant_id,
            status.bot_id,
            status.source_runtime_id,
        )
        incoming_ids: set[str] = set()
        for source in result.records:
            position_id = self._mirror_id(
                RuntimeReadKind.OPEN_POSITIONS,
                status.source_runtime_id,
                source.source_position_id,
            )
            incoming_ids.add(position_id)
            self._repository.upsert_position(
                session,
                OperationalPosition(
                    tenant_id=status.tenant_id,
                    bot_id=status.bot_id,
                    source_runtime_id=status.source_runtime_id,
                    position_id=position_id,
                    source_position_id=source.source_position_id,
                    pair=source.pair,
                    side=source.side,
                    amount=source.amount,
                    opened_at=source.opened_at,
                    source_updated_at=source.source_updated_at,
                    observed_at=status.observed_at,
                    last_reconciled_at=status.last_reconciled_at,
                    freshness=status.freshness,
                    reconciliation_status=self._reconciliation(status),
                    reason_code=status.reason_code,
                ),
            )

        for position in existing:
            if position.position_id in incoming_ids:
                continue
            if self._authoritative_complete(status):
                self._repository.delete_position(
                    session,
                    position.tenant_id,
                    position.position_id,
                )
            else:
                self._repository.upsert_position(
                    session,
                    position.model_copy(update=self._degraded_record_update(status)),
                )

    def _reconcile_orders(self, session: object, result: OrderReadResult) -> None:
        status = result.status
        existing = self._repository.list_orders_for_runtime(
            session,
            status.tenant_id,
            status.bot_id,
            status.source_runtime_id,
        )
        incoming_ids: set[str] = set()
        for source in result.records:
            order_id = self._mirror_id(
                RuntimeReadKind.ORDERS,
                status.source_runtime_id,
                source.source_order_id,
            )
            incoming_ids.add(order_id)
            reconciliation = self._reconciliation(status)
            reason_code = status.reason_code
            if source.execution_intent_id is None:
                reconciliation = ReconciliationStatus.MISMATCH
                reason_code = "RUNTIME_ORDER_ATTRIBUTION_MISSING"
            self._repository.upsert_order(
                session,
                OperationalOrder(
                    tenant_id=status.tenant_id,
                    bot_id=status.bot_id,
                    source_runtime_id=status.source_runtime_id,
                    order_id=order_id,
                    source_order_id=source.source_order_id,
                    source_trade_id=source.source_trade_id,
                    execution_intent_id=source.execution_intent_id,
                    pair=source.pair,
                    side=source.side,
                    state=source.state,
                    amount=source.amount,
                    created_at=source.created_at,
                    source_updated_at=source.source_updated_at,
                    observed_at=status.observed_at,
                    last_reconciled_at=status.last_reconciled_at,
                    freshness=status.freshness,
                    reconciliation_status=reconciliation,
                    reason_code=reason_code,
                ),
            )

        for order in existing:
            if order.order_id in incoming_ids:
                continue
            self._repository.upsert_order(
                session,
                order.model_copy(update=self._missing_history_update(status)),
            )

    def _reconcile_trades(self, session: object, result: TradeReadResult) -> None:
        status = result.status
        existing = self._repository.list_trades_for_runtime(
            session,
            status.tenant_id,
            status.bot_id,
            status.source_runtime_id,
        )
        incoming_ids: set[str] = set()
        for source in result.records:
            trade_id = self._mirror_id(
                RuntimeReadKind.TRADES,
                status.source_runtime_id,
                source.source_trade_id,
            )
            incoming_ids.add(trade_id)
            reconciliation = self._reconciliation(status)
            reason_code = status.reason_code
            if source.state is TradeState.CLOSED and (
                source.closed_at is None
                or source.realized_pnl is None
                or source.fees is None
                or source.exit_reason is None
            ):
                reconciliation = ReconciliationStatus.MISMATCH
                reason_code = "RUNTIME_TRADE_OUTCOME_INCOMPLETE"
            self._repository.upsert_trade(
                session,
                OperationalTrade(
                    tenant_id=status.tenant_id,
                    bot_id=status.bot_id,
                    source_runtime_id=status.source_runtime_id,
                    trade_id=trade_id,
                    source_trade_id=source.source_trade_id,
                    pair=source.pair,
                    side=source.side,
                    state=source.state,
                    amount=source.amount,
                    opened_at=source.opened_at,
                    closed_at=source.closed_at,
                    realized_pnl=source.realized_pnl,
                    fees=source.fees,
                    exit_reason=source.exit_reason,
                    source_updated_at=source.source_updated_at,
                    observed_at=status.observed_at,
                    last_reconciled_at=status.last_reconciled_at,
                    freshness=status.freshness,
                    reconciliation_status=reconciliation,
                    reason_code=reason_code,
                ),
            )

        for trade in existing:
            if trade.trade_id in incoming_ids:
                continue
            self._repository.upsert_trade(
                session,
                trade.model_copy(update=self._missing_history_update(status)),
            )

    @staticmethod
    def _validate_snapshot_scope(snapshot: PrivateRuntimeSnapshot) -> None:
        for status in (
            snapshot.positions.status,
            snapshot.orders.status,
            snapshot.trades.status,
        ):
            if (
                status.tenant_id != snapshot.tenant_id
                or status.bot_id != snapshot.bot_id
                or status.source_runtime_id != snapshot.source_runtime_id
            ):
                raise PermissionDeniedError("runtime snapshot identity mismatch")

    @staticmethod
    def _source_status(status: RuntimeReadStatus) -> OperationalSourceStatus:
        return OperationalSourceStatus(
            tenant_id=status.tenant_id,
            bot_id=status.bot_id,
            source_runtime_id=status.source_runtime_id,
            kind=status.kind,
            source_observed_at=status.source_observed_at,
            observed_at=status.observed_at,
            last_reconciled_at=status.last_reconciled_at,
            freshness=status.freshness,
            reconciliation_status=ReconciliationStatus(status.reconciliation_status.value),
            complete=status.complete,
            record_count=status.record_count,
            reason_code=status.reason_code,
        )

    @staticmethod
    def _reconciliation(status: RuntimeReadStatus) -> ReconciliationStatus:
        return ReconciliationStatus(status.reconciliation_status.value)

    @staticmethod
    def _authoritative_complete(status: RuntimeReadStatus) -> bool:
        return (
            status.complete
            and status.freshness is RuntimeReadFreshness.CURRENT
            and status.reconciliation_status is RuntimeReadReconciliationStatus.SYNCED
        )

    @classmethod
    def _degraded_record_update(cls, status: RuntimeReadStatus) -> dict[str, object]:
        return {
            "observed_at": status.observed_at,
            "last_reconciled_at": status.last_reconciled_at,
            "freshness": status.freshness,
            "reconciliation_status": cls._reconciliation(status),
            "reason_code": status.reason_code,
        }

    @classmethod
    def _missing_history_update(cls, status: RuntimeReadStatus) -> dict[str, object]:
        if cls._authoritative_complete(status):
            return {
                "observed_at": status.observed_at,
                "last_reconciled_at": status.last_reconciled_at,
                "freshness": RuntimeReadFreshness.CURRENT,
                "reconciliation_status": ReconciliationStatus.MISMATCH,
                "reason_code": "RUNTIME_SOURCE_RECORD_MISSING",
            }
        return cls._degraded_record_update(status)

    @staticmethod
    def _mirror_id(kind: RuntimeReadKind, runtime_id: str, source_id: str) -> str:
        digest = hashlib.sha256(f"{kind.value}\0{runtime_id}\0{source_id}".encode()).hexdigest()
        return f"{kind.value.lower()}:{digest[:32]}"

    @staticmethod
    def _require_tenant(context: RequestContext, tenant_id: str) -> None:
        if context.tenant_id != tenant_id:
            raise PermissionDeniedError("tenant scope mismatch")
