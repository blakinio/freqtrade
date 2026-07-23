from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent
from ai_platform.portal.contracts.execution import OrderRecord
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.risk import RiskDecision
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.intelligence.service import TradeIntelligenceService
from ai_platform.portal.operations.repository import OperationalRepository
from ai_platform.portal.operations.schema import (
    ExecutionActivityEntry,
    OperationalOrder,
    OperationalPosition,
    PerformanceSummary,
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
        )
        with self._session_factory() as session, session.begin():
            self._repository.upsert_order(session, operational_order)
            self._repository.upsert_position(session, position)
        return position

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

    @staticmethod
    def _require_tenant(context: RequestContext, tenant_id: str) -> None:
        if context.tenant_id != tenant_id:
            raise PermissionDeniedError("tenant scope mismatch")
