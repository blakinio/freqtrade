from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.audit import AuditEvent
from ai_platform.portal.contracts.bots import (
    BotConfigRevision,
    BotDesiredState,
    BotInstance,
    BotSpec,
)
from ai_platform.portal.contracts.events import EventEnvelope
from ai_platform.portal.control_plane.models import (
    AuditEventRow,
    BotConfigRevisionRow,
    BotRow,
    OutboxEventRow,
)


class BotRepository:
    def add_bot(self, session: Session, bot: BotInstance) -> None:
        session.add(
            BotRow(
                tenant_id=bot.tenant_id,
                bot_id=bot.bot_id,
                name=bot.name,
                spec_json=bot.spec.canonical_json(),
                desired_state=bot.desired_state.value,
                observed_state=bot.observed_state.value,
                current_revision=bot.spec.config_revision,
            )
        )

    def get_bot(self, session: Session, tenant_id: str, bot_id: str) -> BotInstance | None:
        row = session.get(BotRow, (tenant_id, bot_id))
        return self._bot_from_row(row) if row is not None else None

    def list_bots(self, session: Session, tenant_id: str) -> tuple[BotInstance, ...]:
        rows = session.scalars(
            select(BotRow).where(BotRow.tenant_id == tenant_id).order_by(BotRow.bot_id)
        ).all()
        return tuple(self._bot_from_row(row) for row in rows)

    def set_current_revision(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        spec: BotSpec,
    ) -> BotInstance | None:
        row = session.get(BotRow, (tenant_id, bot_id))
        if row is None:
            return None
        row.spec_json = spec.canonical_json()
        row.current_revision = spec.config_revision
        session.flush()
        return self._bot_from_row(row)

    def set_desired_state(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        desired_state: BotDesiredState,
    ) -> BotInstance | None:
        row = session.get(BotRow, (tenant_id, bot_id))
        if row is None:
            return None
        row.desired_state = desired_state.value
        session.flush()
        return self._bot_from_row(row)

    def add_revision(self, session: Session, revision: BotConfigRevision) -> None:
        session.add(
            BotConfigRevisionRow(
                tenant_id=revision.tenant_id,
                bot_id=revision.bot_id,
                revision=revision.revision,
                revision_id=revision.revision_id,
                revision_json=revision.canonical_json(),
                created_by_actor_id=revision.created_by_actor_id,
                created_at=revision.created_at,
            )
        )

    def get_revision(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        revision: int,
    ) -> BotConfigRevision | None:
        row = session.get(BotConfigRevisionRow, (tenant_id, bot_id, revision))
        return BotConfigRevision.model_validate_json(row.revision_json) if row is not None else None

    def list_revisions(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
    ) -> tuple[BotConfigRevision, ...]:
        rows = session.scalars(
            select(BotConfigRevisionRow)
            .where(
                BotConfigRevisionRow.tenant_id == tenant_id,
                BotConfigRevisionRow.bot_id == bot_id,
            )
            .order_by(BotConfigRevisionRow.revision)
        ).all()
        return tuple(BotConfigRevision.model_validate_json(row.revision_json) for row in rows)

    def add_audit_event(self, session: Session, event: AuditEvent) -> None:
        session.add(
            AuditEventRow(
                audit_id=str(event.audit_id),
                tenant_id=event.tenant_id,
                actor_id=event.actor_id,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                action=event.action.value,
                result=event.result.value,
                occurred_at=event.occurred_at,
                event_json=event.canonical_json(),
            )
        )

    def list_audit_events(
        self,
        session: Session,
        tenant_id: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> tuple[AuditEvent, ...]:
        statement = select(AuditEventRow).where(AuditEventRow.tenant_id == tenant_id)
        if resource_type is not None:
            statement = statement.where(AuditEventRow.resource_type == resource_type)
        if resource_id is not None:
            statement = statement.where(AuditEventRow.resource_id == resource_id)
        rows = session.scalars(statement.order_by(AuditEventRow.occurred_at, AuditEventRow.audit_id)).all()
        return tuple(AuditEvent.model_validate_json(row.event_json) for row in rows)

    def add_outbox_event(self, session: Session, event: EventEnvelope) -> None:
        session.add(
            OutboxEventRow(
                event_id=str(event.event_id),
                tenant_id=event.tenant_id,
                event_type=event.event_type.value,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                occurred_at=event.occurred_at,
                event_json=event.canonical_json(),
                published_at=None,
            )
        )

    def list_outbox_events(
        self,
        session: Session,
        tenant_id: str,
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
    ) -> tuple[EventEnvelope, ...]:
        statement = select(OutboxEventRow).where(OutboxEventRow.tenant_id == tenant_id)
        if aggregate_type is not None:
            statement = statement.where(OutboxEventRow.aggregate_type == aggregate_type)
        if aggregate_id is not None:
            statement = statement.where(OutboxEventRow.aggregate_id == aggregate_id)
        rows = session.scalars(
            statement.order_by(OutboxEventRow.occurred_at, OutboxEventRow.event_id)
        ).all()
        return tuple(EventEnvelope.model_validate_json(row.event_json) for row in rows)

    @staticmethod
    def _bot_from_row(row: BotRow) -> BotInstance:
        return BotInstance(
            bot_id=row.bot_id,
            tenant_id=row.tenant_id,
            name=row.name,
            spec=BotSpec.model_validate_json(row.spec_json),
            desired_state=row.desired_state,
            observed_state=row.observed_state,
        )
