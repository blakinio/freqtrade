from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.audit import AuditEvent
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.events import EventEnvelope
from ai_platform.portal.contracts.models import ModelVersion
from ai_platform.portal.control_plane.models import AuditEventRow, OutboxEventRow
from ai_platform.portal.model_control.models import (
    ModelPromotionHistoryRow,
    ModelPromotionSlotRow,
    ModelVersionRow,
)
from ai_platform.portal.model_control.schema import (
    ModelPromotionAction,
    ModelPromotionSlot,
    ModelPromotionTransition,
)


class ModelControlRepository:
    def add_model(
        self,
        session: Session,
        model: ModelVersion,
        registered_by_actor_id: str,
        registered_at: datetime,
    ) -> None:
        session.add(
            ModelVersionRow(
                tenant_id=model.tenant_id,
                model_version_id=model.model_version_id,
                model_family_id=model.model_family_id,
                model_json=model.canonical_json(),
                registered_by_actor_id=registered_by_actor_id,
                registered_at=registered_at,
            )
        )

    def get_model(
        self,
        session: Session,
        tenant_id: str,
        model_version_id: str,
    ) -> ModelVersion | None:
        row = session.get(ModelVersionRow, (tenant_id, model_version_id))
        return ModelVersion.model_validate_json(row.model_json) if row is not None else None

    def list_models(self, session: Session, tenant_id: str) -> tuple[ModelVersion, ...]:
        rows = session.scalars(
            select(ModelVersionRow)
            .where(ModelVersionRow.tenant_id == tenant_id)
            .order_by(ModelVersionRow.model_family_id, ModelVersionRow.model_version_id)
        ).all()
        return tuple(ModelVersion.model_validate_json(row.model_json) for row in rows)

    def get_slot(
        self,
        session: Session,
        tenant_id: str,
        model_family_id: str,
        environment: Environment,
    ) -> ModelPromotionSlot | None:
        row = session.get(
            ModelPromotionSlotRow,
            (tenant_id, model_family_id, environment.value),
        )
        return self._slot_from_row(row) if row is not None else None

    def set_slot(
        self,
        session: Session,
        tenant_id: str,
        model_family_id: str,
        environment: Environment,
        model_version_id: str,
        updated_at: datetime,
        updated_by_actor_id: str,
    ) -> ModelPromotionSlot:
        row = session.get(
            ModelPromotionSlotRow,
            (tenant_id, model_family_id, environment.value),
        )
        if row is None:
            row = ModelPromotionSlotRow(
                tenant_id=tenant_id,
                model_family_id=model_family_id,
                environment=environment.value,
                current_model_version_id=model_version_id,
                updated_at=updated_at,
                updated_by_actor_id=updated_by_actor_id,
            )
            session.add(row)
        else:
            row.current_model_version_id = model_version_id
            row.updated_at = updated_at
            row.updated_by_actor_id = updated_by_actor_id
        session.flush()
        return self._slot_from_row(row)

    def add_transition(self, session: Session, transition: ModelPromotionTransition) -> None:
        session.add(
            ModelPromotionHistoryRow(
                transition_id=str(transition.transition_id),
                tenant_id=transition.tenant_id,
                model_family_id=transition.model_family_id,
                environment=transition.environment.value,
                from_model_version_id=transition.from_model_version_id,
                to_model_version_id=transition.to_model_version_id,
                action=transition.action.value,
                actor_id=transition.actor_id,
                occurred_at=transition.occurred_at,
            )
        )

    def list_transitions(
        self,
        session: Session,
        tenant_id: str,
        model_family_id: str,
        environment: Environment,
    ) -> tuple[ModelPromotionTransition, ...]:
        rows = session.scalars(
            select(ModelPromotionHistoryRow)
            .where(
                ModelPromotionHistoryRow.tenant_id == tenant_id,
                ModelPromotionHistoryRow.model_family_id == model_family_id,
                ModelPromotionHistoryRow.environment == environment.value,
            )
            .order_by(
                ModelPromotionHistoryRow.occurred_at,
                ModelPromotionHistoryRow.transition_id,
            )
        ).all()
        return tuple(self._transition_from_row(row) for row in rows)

    def was_previously_promoted(
        self,
        session: Session,
        tenant_id: str,
        model_family_id: str,
        environment: Environment,
        model_version_id: str,
    ) -> bool:
        transition_id = session.scalar(
            select(ModelPromotionHistoryRow.transition_id)
            .where(
                ModelPromotionHistoryRow.tenant_id == tenant_id,
                ModelPromotionHistoryRow.model_family_id == model_family_id,
                ModelPromotionHistoryRow.environment == environment.value,
                ModelPromotionHistoryRow.to_model_version_id == model_version_id,
                ModelPromotionHistoryRow.action == ModelPromotionAction.PROMOTE.value,
            )
            .limit(1)
        )
        return transition_id is not None

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

    @staticmethod
    def _slot_from_row(row: ModelPromotionSlotRow) -> ModelPromotionSlot:
        return ModelPromotionSlot(
            tenant_id=row.tenant_id,
            model_family_id=row.model_family_id,
            environment=Environment(row.environment),
            model_version_id=row.current_model_version_id,
            updated_at=row.updated_at,
            updated_by_actor_id=row.updated_by_actor_id,
        )

    @staticmethod
    def _transition_from_row(row: ModelPromotionHistoryRow) -> ModelPromotionTransition:
        return ModelPromotionTransition(
            transition_id=row.transition_id,
            tenant_id=row.tenant_id,
            model_family_id=row.model_family_id,
            environment=Environment(row.environment),
            from_model_version_id=row.from_model_version_id,
            to_model_version_id=row.to_model_version_id,
            action=ModelPromotionAction(row.action),
            actor_id=row.actor_id,
            occurred_at=row.occurred_at,
        )
