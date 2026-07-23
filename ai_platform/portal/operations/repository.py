from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.operations.models import OperationalOrderRow, OperationalPositionRow
from ai_platform.portal.operations.schema import OperationalOrder, OperationalPosition


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

    def list_positions(self, session: Session, tenant_id: str) -> tuple[OperationalPosition, ...]:
        rows = session.scalars(
            select(OperationalPositionRow)
            .where(OperationalPositionRow.tenant_id == tenant_id)
            .order_by(OperationalPositionRow.opened_at, OperationalPositionRow.position_id)
        ).all()
        return tuple(OperationalPosition.model_validate_json(row.position_json) for row in rows)
