from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.audit import AuditEvent
from ai_platform.portal.contracts.bots import (
    BotConfigRevision,
    BotDesiredState,
    BotInstance,
    BotObservedState,
    BotSpec,
)
from ai_platform.portal.contracts.events import EventEnvelope
from ai_platform.portal.contracts.runtime_generation import BotRollout, RuntimeGeneration
from ai_platform.portal.control_plane.models import (
    AuditEventRow,
    BotConfigRevisionRow,
    BotRolloutRow,
    BotRow,
    CommandIdempotencyRow,
    OutboxEventRow,
    RuntimeGenerationRow,
)


def _restore_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True)
class CommandIdempotencyRecord:
    tenant_id: str
    bot_id: str
    idempotency_key: str
    operation: str
    semantic_request_digest: str
    generation_id: str
    rollout_id: str


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
                latest_authored_revision_id=bot.latest_authored_revision_id,
                desired_revision_id=bot.desired_revision_id,
                desired_runtime_generation_id=bot.desired_runtime_generation_id,
                observed_runtime_generation_id=bot.observed_runtime_generation_id,
                state_version=bot.state_version,
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

    def set_latest_authored_revision(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        spec: BotSpec,
        revision_id: str,
    ) -> BotInstance | None:
        row = session.get(BotRow, (tenant_id, bot_id))
        if row is None:
            return None
        row.spec_json = spec.canonical_json()
        row.current_revision = spec.config_revision
        row.latest_authored_revision_id = revision_id
        row.state_version = (row.state_version or 0) + 1
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
        row.state_version = (row.state_version or 0) + 1
        session.flush()
        return self._bot_from_row(row)

    def set_desired_generation(
        self,
        session: Session,
        *,
        tenant_id: str,
        bot_id: str,
        revision_id: str,
        generation_id: str,
        expected_state_version: int,
    ) -> BotInstance | None:
        result = cast(
            CursorResult[Any],
            session.execute(
                update(BotRow)
                .where(
                    BotRow.tenant_id == tenant_id,
                    BotRow.bot_id == bot_id,
                    BotRow.state_version == expected_state_version,
                )
                .values(
                    desired_revision_id=revision_id,
                    desired_runtime_generation_id=generation_id,
                    state_version=expected_state_version + 1,
                )
            ),
        )
        if result.rowcount != 1:
            return None
        session.flush()
        return self.get_bot(session, tenant_id, bot_id)

    def bump_state_version(
        self,
        session: Session,
        *,
        tenant_id: str,
        bot_id: str,
        expected_state_version: int,
    ) -> BotInstance | None:
        result = cast(
            CursorResult[Any],
            session.execute(
                update(BotRow)
                .where(
                    BotRow.tenant_id == tenant_id,
                    BotRow.bot_id == bot_id,
                    BotRow.state_version == expected_state_version,
                )
                .values(state_version=expected_state_version + 1)
            ),
        )
        if result.rowcount != 1:
            return None
        session.flush()
        return self.get_bot(session, tenant_id, bot_id)

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

    def replace_revision(self, session: Session, revision: BotConfigRevision) -> None:
        row = session.get(
            BotConfigRevisionRow,
            (revision.tenant_id, revision.bot_id, revision.revision),
        )
        if row is None or row.revision_id != revision.revision_id:
            raise LookupError("bot revision not found")
        row.revision_json = revision.canonical_json()
        session.flush()

    def get_revision(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        revision: int,
    ) -> BotConfigRevision | None:
        row = session.get(BotConfigRevisionRow, (tenant_id, bot_id, revision))
        return BotConfigRevision.model_validate_json(row.revision_json) if row is not None else None

    def get_revision_by_id(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        revision_id: str,
    ) -> BotConfigRevision | None:
        row = session.scalar(
            select(BotConfigRevisionRow).where(
                BotConfigRevisionRow.tenant_id == tenant_id,
                BotConfigRevisionRow.bot_id == bot_id,
                BotConfigRevisionRow.revision_id == revision_id,
            )
        )
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

    def next_generation_ordinal(self, session: Session, tenant_id: str, bot_id: str) -> int:
        current = session.scalar(
            select(func.max(RuntimeGenerationRow.generation_ordinal)).where(
                RuntimeGenerationRow.tenant_id == tenant_id,
                RuntimeGenerationRow.bot_id == bot_id,
            )
        )
        return int(current or 0) + 1

    def add_runtime_generation(self, session: Session, generation: RuntimeGeneration) -> None:
        session.add(
            RuntimeGenerationRow(
                generation_id=generation.generation_id,
                generation_ordinal=generation.generation_ordinal,
                tenant_id=generation.tenant_id,
                bot_id=generation.bot_id,
                config_revision_id=generation.config_revision_id,
                config_revision_number=generation.config_revision_number,
                config_revision_digest=generation.config_revision_digest,
                normalized_runtime_config_digest=generation.normalized_runtime_config_digest,
                runtime_image_digest=generation.runtime_image_digest,
                strategy_version=generation.strategy_version,
                strategy_artifact_digest=generation.strategy_artifact_digest,
                model_version=generation.model_version,
                model_artifact_digest=generation.model_artifact_digest,
                feature_schema_version=generation.feature_schema_version,
                risk_policy_version=generation.risk_policy_version,
                risk_policy_digest=generation.risk_policy_digest,
                execution_mode=generation.execution_mode.value,
                managed_mode=generation.managed_mode.value,
                managed_mode_request_digest=generation.managed_mode_request_digest,
                managed_mode_resolution_digest=generation.managed_mode_resolution_digest,
                paper_authorization_digest=generation.paper_authorization_digest,
                exchange_mode=generation.exchange_mode,
                exchange_connection_revision=generation.exchange_connection_revision,
                isolation_profile_version=generation.isolation_profile_version,
                isolation_profile_digest=generation.isolation_profile_digest,
                isolation_plan_digest=generation.isolation_plan_digest,
                gateway_artifact_digest=generation.gateway_artifact_digest,
                gateway_contract_version=generation.gateway_contract_version,
                gateway_contract_digest=generation.gateway_contract_digest,
                market_data_egress_policy_version=generation.market_data_egress_policy_version,
                market_data_egress_policy_digest=generation.market_data_egress_policy_digest,
                generation_spec_version=generation.generation_spec_version,
                generation_spec_digest=generation.generation_spec_digest,
                created_by_actor_id=generation.created_by_actor_id,
                created_at=generation.created_at,
                request_id=str(generation.request_id),
                correlation_id=str(generation.correlation_id),
                causation_id=(str(generation.causation_id) if generation.causation_id else None),
            )
        )
        session.flush()

    def get_runtime_generation(
        self,
        session: Session,
        tenant_id: str,
        generation_id: str,
    ) -> RuntimeGeneration | None:
        row = session.get(RuntimeGenerationRow, generation_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return RuntimeGeneration(
            generation_id=row.generation_id,
            generation_ordinal=row.generation_ordinal,
            tenant_id=row.tenant_id,
            bot_id=row.bot_id,
            config_revision_id=row.config_revision_id,
            config_revision_number=row.config_revision_number,
            config_revision_digest=row.config_revision_digest,
            normalized_runtime_config_digest=row.normalized_runtime_config_digest,
            runtime_image_digest=row.runtime_image_digest,
            strategy_version=row.strategy_version,
            strategy_artifact_digest=row.strategy_artifact_digest,
            model_version=row.model_version,
            model_artifact_digest=row.model_artifact_digest,
            feature_schema_version=row.feature_schema_version,
            risk_policy_version=row.risk_policy_version,
            risk_policy_digest=row.risk_policy_digest,
            execution_mode=row.execution_mode,
            managed_mode=row.managed_mode,
            managed_mode_request_digest=row.managed_mode_request_digest,
            managed_mode_resolution_digest=row.managed_mode_resolution_digest,
            paper_authorization_digest=row.paper_authorization_digest,
            exchange_mode=row.exchange_mode,
            exchange_connection_revision=row.exchange_connection_revision,
            isolation_profile_version=row.isolation_profile_version,
            isolation_profile_digest=row.isolation_profile_digest,
            isolation_plan_digest=row.isolation_plan_digest,
            gateway_artifact_digest=row.gateway_artifact_digest,
            gateway_contract_version=row.gateway_contract_version,
            gateway_contract_digest=row.gateway_contract_digest,
            market_data_egress_policy_version=row.market_data_egress_policy_version,
            market_data_egress_policy_digest=row.market_data_egress_policy_digest,
            generation_spec_version=row.generation_spec_version,
            generation_spec_digest=row.generation_spec_digest,
            created_by_actor_id=row.created_by_actor_id,
            created_at=_restore_utc(row.created_at),
            request_id=row.request_id,
            correlation_id=row.correlation_id,
            causation_id=row.causation_id,
        )

    def add_rollout(self, session: Session, rollout: BotRollout) -> None:
        session.add(
            BotRolloutRow(
                rollout_id=rollout.rollout_id,
                tenant_id=rollout.tenant_id,
                bot_id=rollout.bot_id,
                from_generation_id=rollout.from_generation_id,
                to_generation_id=rollout.to_generation_id,
                status=rollout.status.value,
                reason_code=rollout.reason_code,
                requested_by_actor_id=rollout.requested_by_actor_id,
                idempotency_key=rollout.idempotency_key,
                attempt=rollout.attempt,
                created_at=rollout.created_at,
                updated_at=rollout.updated_at,
                completed_at=rollout.completed_at,
            )
        )

    def get_rollout(self, session: Session, tenant_id: str, rollout_id: str) -> BotRollout | None:
        row = session.get(BotRolloutRow, rollout_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return BotRollout(
            rollout_id=row.rollout_id,
            tenant_id=row.tenant_id,
            bot_id=row.bot_id,
            from_generation_id=row.from_generation_id,
            to_generation_id=row.to_generation_id,
            status=row.status,
            reason_code=row.reason_code,
            requested_by_actor_id=row.requested_by_actor_id,
            idempotency_key=row.idempotency_key,
            attempt=row.attempt,
            created_at=_restore_utc(row.created_at),
            updated_at=_restore_utc(row.updated_at),
            completed_at=_restore_utc(row.completed_at),
        )

    def add_idempotency_record(
        self,
        session: Session,
        *,
        tenant_id: str,
        bot_id: str,
        idempotency_key: str,
        operation: str,
        semantic_request_digest: str,
        generation_id: str,
        rollout_id: str,
        created_at: datetime,
    ) -> None:
        session.add(
            CommandIdempotencyRow(
                tenant_id=tenant_id,
                bot_id=bot_id,
                idempotency_key=idempotency_key,
                operation=operation,
                semantic_request_digest=semantic_request_digest,
                generation_id=generation_id,
                rollout_id=rollout_id,
                created_at=created_at,
            )
        )

    def get_idempotency_record(
        self,
        session: Session,
        tenant_id: str,
        bot_id: str,
        idempotency_key: str,
    ) -> CommandIdempotencyRecord | None:
        row = session.get(CommandIdempotencyRow, (tenant_id, bot_id, idempotency_key))
        if row is None:
            return None
        return CommandIdempotencyRecord(
            tenant_id=row.tenant_id,
            bot_id=row.bot_id,
            idempotency_key=row.idempotency_key,
            operation=row.operation,
            semantic_request_digest=row.semantic_request_digest,
            generation_id=row.generation_id,
            rollout_id=row.rollout_id,
        )

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
        rows = session.scalars(
            statement.order_by(AuditEventRow.occurred_at, AuditEventRow.audit_id)
        ).all()
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
            desired_state=BotDesiredState(row.desired_state),
            observed_state=BotObservedState(row.observed_state),
            latest_authored_revision_id=row.latest_authored_revision_id,
            desired_revision_id=row.desired_revision_id,
            desired_runtime_generation_id=row.desired_runtime_generation_id,
            observed_runtime_generation_id=row.observed_runtime_generation_id,
            state_version=row.state_version or 1,
        )
