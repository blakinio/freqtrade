from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.operations.models import (
    OperationalOrderRow,
    OperationalPositionRow,
    OperationalSourceStatusRow,
    OperationalTradeRow,
)
from ai_platform.portal.operations.schema import (
    OperationalOrder,
    OperationalPosition,
    OperationalSourceStatus,
    OperationalTrade,
)


class OperationalRepository:
    def upsert_order(self, session: Session, order: OperationalOrder) -> None:
        row = session.get(OperationalOrderRow, (order.tenant_id, order.order_id))
        if row is None:
            session.add(
                OperationalOrderRow(
                    tenant_id=order.tenant_id,
                    order_id=order.order_id,
                    bot_id=order.bot_id,
                    source_runtime_id=order.source_runtime_id,
                    created_at=order.created_at,
                    order_json=order.canonical_json(),
                )
            )
            return
        row.bot_id = order.bot_id
        row.source_runtime_id = order.source_runtime_id
        row.created_at = order.created_at
        row.order_json = order.canonical_json()

    def upsert_position(self, session: Session, position: OperationalPosition) -> None:
        row = session.get(OperationalPositionRow, (position.tenant_id, position.position_id))
        if row is None:
            session.add(
                OperationalPositionRow(
                    tenant_id=position.tenant_id,
                    position_id=position.position_id,
                    bot_id=position.bot_id,
                    source_runtime_id=position.source_runtime_id,
                    opened_at=position.opened_at,
                    position_json=position.canonical_json(),
                )
            )
            return
        row.bot_id = position.bot_id
        row.source_runtime_id = position.source_runtime_id
        row.opened_at = position.opened_at
        row.position_json = position.canonical_json()

    def upsert_trade(self, session: Session, trade: OperationalTrade) -> None:
        row = session.get(OperationalTradeRow, (trade.tenant_id, trade.trade_id))
        if row is None:
            session.add(
                OperationalTradeRow(
                    tenant_id=trade.tenant_id,
                    trade_id=trade.trade_id,
                    bot_id=trade.bot_id,
                    source_runtime_id=trade.source_runtime_id,
                    opened_at=trade.opened_at,
                    trade_json=trade.canonical_json(),
                )
            )
            return
        row.bot_id = trade.bot_id
        row.source_runtime_id = trade.source_runtime_id
        row.opened_at = trade.opened_at
        row.trade_json = trade.canonical_json()

    def upsert_source_status(
        self,
        session: Session,
        status: OperationalSourceStatus,
    ) -> None:
        key = (status.tenant_id, status.bot_id, status.source_runtime_id, status.kind.value)
        row = session.get(OperationalSourceStatusRow, key)
        if row is None:
            session.add(
                OperationalSourceStatusRow(
                    tenant_id=status.tenant_id,
                    bot_id=status.bot_id,
                    source_runtime_id=status.source_runtime_id,
                    kind=status.kind.value,
                    observed_at=status.observed_at,
                    status_json=status.canonical_json(),
                )
            )
            return
        row.observed_at = status.observed_at
        row.status_json = status.canonical_json()

    def delete_position(self, session: Session, tenant_id: str, position_id: str) -> None:
        row = session.get(OperationalPositionRow, (tenant_id, position_id))
        if row is not None:
            session.delete(row)

    def list_orders(self, session: Session, tenant_id: str) -> tuple[OperationalOrder, ...]:
        rows = session.scalars(
            select(OperationalOrderRow)
            .where(OperationalOrderRow.tenant_id == tenant_id)
            .order_by(OperationalOrderRow.created_at, OperationalOrderRow.order_id)
        ).all()
        return tuple(OperationalOrder.model_validate_json(row.order_json) for row in rows)

    def list_positions(
        self,
        session: Session,
        tenant_id: str,
    ) -> tuple[OperationalPosition, ...]:
        rows = session.scalars(
            select(OperationalPositionRow)
            .where(OperationalPositionRow.tenant_id == tenant_id)
            .order_by(OperationalPositionRow.opened_at, OperationalPositionRow.position_id)
        ).all()
        return tuple(OperationalPosition.model_validate_json(row.position_json) for row in rows)

    def list_trades(self, session: Session, tenant_id: str) -> tuple[OperationalTrade, ...]:
        rows = session.scalars(
            select(OperationalTradeRow)
            .where(OperationalTradeRow.tenant_id == tenant_id)
            .order_by(OperationalTradeRow.opened_at, OperationalTradeRow.trade_id)
        ).all()
        return tuple(OperationalTrade.model_validate_json(row.trade_json) for row in rows)

    def list_source_statuses(
        self,
        session: Session,
        tenant_id: str,
    ) -> tuple[OperationalSourceStatus, ...]:
        rows = session.scalars(
            select(OperationalSourceStatusRow)
            .where(OperationalSourceStatusRow.tenant_id == tenant_id)
            .order_by(
                OperationalSourceStatusRow.bot_id,
                OperationalSourceStatusRow.source_runtime_id,
                OperationalSourceStatusRow.kind,
            )
        ).all()
        return tuple(
            OperationalSourceStatus.model_validate_json(row.status_json) for row in rows
        )

    def list_orders_for_runtime(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
    ) -> tuple[OperationalOrder, ...]:
        rows = session.scalars(
            select(OperationalOrderRow)
            .where(
                OperationalOrderRow.tenant_id == tenant_id,
                OperationalOrderRow.bot_id == bot_id,
                OperationalOrderRow.source_runtime_id == source_runtime_id,
            )
            .order_by(OperationalOrderRow.created_at, OperationalOrderRow.order_id)
        ).all()
        return tuple(OperationalOrder.model_validate_json(row.order_json) for row in rows)

    def list_positions_for_runtime(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
    ) -> tuple[OperationalPosition, ...]:
        rows = session.scalars(
            select(OperationalPositionRow)
            .where(
                OperationalPositionRow.tenant_id == tenant_id,
                OperationalPositionRow.bot_id == bot_id,
                OperationalPositionRow.source_runtime_id == source_runtime_id,
            )
            .order_by(OperationalPositionRow.opened_at, OperationalPositionRow.position_id)
        ).all()
        return tuple(OperationalPosition.model_validate_json(row.position_json) for row in rows)

    def list_trades_for_runtime(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        source_runtime_id: str,
    ) -> tuple[OperationalTrade, ...]:
        rows = session.scalars(
            select(OperationalTradeRow)
            .where(
                OperationalTradeRow.tenant_id == tenant_id,
                OperationalTradeRow.bot_id == bot_id,
                OperationalTradeRow.source_runtime_id == source_runtime_id,
            )
            .order_by(OperationalTradeRow.opened_at, OperationalTradeRow.trade_id)
        ).all()
        return tuple(OperationalTrade.model_validate_json(row.trade_json) for row in rows)
