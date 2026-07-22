from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import JsonValue
from sqlalchemy.exc import IntegrityError

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent, AuditResult
from ai_platform.portal.contracts.bots import BotConfigRevision
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.models import ModelLifecycleState, ModelVersion
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.model_control.repository import ModelControlRepository
from ai_platform.portal.model_control.schema import (
    ModelPromotionAction,
    ModelPromotionSlot,
    ModelPromotionTransition,
)
from ai_platform.portal.security.authorization import PermissionDeniedError, require_permission


class ModelNotFoundError(LookupError):
    pass


class ModelControlConflictError(RuntimeError):
    pass


class ModelNotAssignableError(RuntimeError):
    pass


Clock = Callable[[], datetime]

ASSIGNABLE_MODEL_STATES = frozenset(
    {
        ModelLifecycleState.VALIDATED,
        ModelLifecycleState.PROMOTED,
        ModelLifecycleState.DRY_RUN,
        ModelLifecycleState.SHADOW,
    }
)


class ModelControlService:
    def __init__(
        self,
        session_factory: SessionFactory,
        repository: ModelControlRepository | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or ModelControlRepository()
        self._clock = clock or (lambda: datetime.now(UTC))

    def register_model(self, context: RequestContext, model: ModelVersion) -> ModelVersion:
        require_permission(context.permissions, Permission.MODEL_TRAIN)
        self._require_tenant(context, model.tenant_id)
        occurred_at = self._clock()
        audit = self._audit_event(
            context,
            model.model_version_id,
            AuditAction.MODEL_REGISTERED,
            occurred_at,
            details={
                "model_family_id": model.model_family_id,
                "lifecycle_state": model.lifecycle_state.value,
            },
        )
        event = self._domain_event(
            context,
            model.model_version_id,
            EventType.MODEL_REGISTERED,
            occurred_at,
            payload={
                "model_family_id": model.model_family_id,
                "lifecycle_state": model.lifecycle_state.value,
            },
        )

        try:
            with self._session_factory() as session, session.begin():
                if (
                    self._repository.get_model(
                        session,
                        context.tenant_id,
                        model.model_version_id,
                    )
                    is not None
                ):
                    raise ModelControlConflictError("model version identity already exists")
                self._repository.add_model(session, model, context.actor_id, occurred_at)
                self._repository.add_audit_event(session, audit)
                self._repository.add_outbox_event(session, event)
        except IntegrityError as exc:
            raise ModelControlConflictError("model version identity already exists") from exc
        return model

    def get_model(self, context: RequestContext, model_version_id: str) -> ModelVersion:
        require_permission(context.permissions, Permission.MODEL_READ)
        with self._session_factory() as session:
            model = self._repository.get_model(session, context.tenant_id, model_version_id)
        if model is None:
            raise ModelNotFoundError("model version not found")
        return model

    def list_models(self, context: RequestContext) -> tuple[ModelVersion, ...]:
        require_permission(context.permissions, Permission.MODEL_READ)
        with self._session_factory() as session:
            return self._repository.list_models(session, context.tenant_id)

    def get_promotion_slot(
        self,
        context: RequestContext,
        model_family_id: str,
        environment: Environment,
    ) -> ModelPromotionSlot | None:
        require_permission(context.permissions, Permission.MODEL_READ)
        with self._session_factory() as session:
            return self._repository.get_slot(
                session,
                context.tenant_id,
                model_family_id,
                environment,
            )

    def list_promotion_history(
        self,
        context: RequestContext,
        model_family_id: str,
        environment: Environment,
    ) -> tuple[ModelPromotionTransition, ...]:
        require_permission(context.permissions, Permission.MODEL_READ)
        with self._session_factory() as session:
            return self._repository.list_transitions(
                session,
                context.tenant_id,
                model_family_id,
                environment,
            )

    def promote_model(
        self,
        context: RequestContext,
        model_version_id: str,
        environment: Environment,
    ) -> ModelPromotionSlot:
        require_permission(context.permissions, Permission.MODEL_PROMOTE)
        occurred_at = self._clock()

        try:
            with self._session_factory() as session, session.begin():
                model = self._repository.get_model(session, context.tenant_id, model_version_id)
                if model is None:
                    raise ModelNotFoundError("model version not found")
                self._require_assignable_state(model)

                current = self._repository.get_slot(
                    session,
                    context.tenant_id,
                    model.model_family_id,
                    environment,
                )
                if current is not None and current.model_version_id == model.model_version_id:
                    raise ModelControlConflictError(
                        "model version is already promoted in this slot"
                    )

                previous_model_version_id = (
                    current.model_version_id if current is not None else None
                )
                slot = self._repository.set_slot(
                    session,
                    context.tenant_id,
                    model.model_family_id,
                    environment,
                    model.model_version_id,
                    occurred_at,
                    context.actor_id,
                )
                self._repository.add_transition(
                    session,
                    ModelPromotionTransition(
                        transition_id=uuid4(),
                        tenant_id=context.tenant_id,
                        model_family_id=model.model_family_id,
                        environment=environment,
                        from_model_version_id=previous_model_version_id,
                        to_model_version_id=model.model_version_id,
                        action=ModelPromotionAction.PROMOTE,
                        actor_id=context.actor_id,
                        occurred_at=occurred_at,
                    ),
                )
                details: dict[str, JsonValue] = {
                    "model_family_id": model.model_family_id,
                    "environment": environment.value,
                    "from_model_version_id": previous_model_version_id,
                    "to_model_version_id": model.model_version_id,
                }
                self._repository.add_audit_event(
                    session,
                    self._audit_event(
                        context,
                        model.model_version_id,
                        AuditAction.MODEL_PROMOTED,
                        occurred_at,
                        details,
                    ),
                )
                self._repository.add_outbox_event(
                    session,
                    self._domain_event(
                        context,
                        model.model_version_id,
                        EventType.MODEL_PROMOTED,
                        occurred_at,
                        details,
                    ),
                )
        except IntegrityError as exc:
            raise ModelControlConflictError("model promotion persistence conflict") from exc
        return slot

    def rollback_model(
        self,
        context: RequestContext,
        model_family_id: str,
        environment: Environment,
        target_model_version_id: str,
    ) -> ModelPromotionSlot:
        require_permission(context.permissions, Permission.MODEL_PROMOTE)
        occurred_at = self._clock()

        try:
            with self._session_factory() as session, session.begin():
                current = self._repository.get_slot(
                    session,
                    context.tenant_id,
                    model_family_id,
                    environment,
                )
                if current is None:
                    raise ModelControlConflictError("promotion slot has no active model")
                if current.model_version_id == target_model_version_id:
                    raise ModelControlConflictError("rollback target is already active")

                target = self._repository.get_model(
                    session,
                    context.tenant_id,
                    target_model_version_id,
                )
                if target is None:
                    raise ModelNotFoundError("rollback target model version not found")
                if target.model_family_id != model_family_id:
                    raise ModelControlConflictError(
                        "rollback target belongs to a different model family"
                    )
                self._require_assignable_state(target)
                if not self._repository.was_previously_promoted(
                    session,
                    context.tenant_id,
                    model_family_id,
                    environment,
                    target_model_version_id,
                ):
                    raise ModelControlConflictError(
                        "rollback target was not previously promoted in this slot"
                    )

                slot = self._repository.set_slot(
                    session,
                    context.tenant_id,
                    model_family_id,
                    environment,
                    target_model_version_id,
                    occurred_at,
                    context.actor_id,
                )
                self._repository.add_transition(
                    session,
                    ModelPromotionTransition(
                        transition_id=uuid4(),
                        tenant_id=context.tenant_id,
                        model_family_id=model_family_id,
                        environment=environment,
                        from_model_version_id=current.model_version_id,
                        to_model_version_id=target_model_version_id,
                        action=ModelPromotionAction.ROLLBACK,
                        actor_id=context.actor_id,
                        occurred_at=occurred_at,
                    ),
                )
                details: dict[str, JsonValue] = {
                    "model_family_id": model_family_id,
                    "environment": environment.value,
                    "from_model_version_id": current.model_version_id,
                    "to_model_version_id": target_model_version_id,
                }
                self._repository.add_audit_event(
                    session,
                    self._audit_event(
                        context,
                        target_model_version_id,
                        AuditAction.MODEL_ROLLED_BACK,
                        occurred_at,
                        details,
                    ),
                )
                self._repository.add_outbox_event(
                    session,
                    self._domain_event(
                        context,
                        target_model_version_id,
                        EventType.MODEL_ROLLED_BACK,
                        occurred_at,
                        details,
                    ),
                )
        except IntegrityError as exc:
            raise ModelControlConflictError("model rollback persistence conflict") from exc
        return slot

    def validate_new_assignment(
        self,
        context: RequestContext,
        revision: BotConfigRevision,
    ) -> ModelVersion:
        require_permission(context.permissions, Permission.MODEL_READ)
        self._require_tenant(context, revision.tenant_id)
        with self._session_factory() as session:
            model = self._repository.get_model(
                session,
                context.tenant_id,
                revision.model_version,
            )
            if model is None:
                raise ModelNotFoundError("assigned model version not found")
            slot = self._repository.get_slot(
                session,
                context.tenant_id,
                model.model_family_id,
                revision.environment,
            )
        if slot is None or slot.model_version_id != revision.model_version:
            raise ModelNotAssignableError(
                "bot config revision model is not the promoted model for this family/environment"
            )
        return model

    @staticmethod
    def _require_tenant(context: RequestContext, tenant_id: str) -> None:
        if tenant_id != context.tenant_id:
            raise PermissionDeniedError("tenant scope mismatch")

    @staticmethod
    def _require_assignable_state(model: ModelVersion) -> None:
        if model.lifecycle_state not in ASSIGNABLE_MODEL_STATES:
            raise ModelNotAssignableError(
                f"model lifecycle state is not assignable in P5: {model.lifecycle_state.value}"
            )

    @staticmethod
    def _audit_event(
        context: RequestContext,
        model_version_id: str,
        action: AuditAction,
        occurred_at: datetime,
        details: dict[str, JsonValue],
    ) -> AuditEvent:
        return AuditEvent(
            audit_id=uuid4(),
            occurred_at=occurred_at,
            actor_type=context.actor_type,
            actor_id=context.actor_id,
            tenant_id=context.tenant_id,
            resource_type="model",
            resource_id=model_version_id,
            action=action,
            result=AuditResult.SUCCEEDED,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            details=details,
        )

    @staticmethod
    def _domain_event(
        context: RequestContext,
        model_version_id: str,
        event_type: EventType,
        occurred_at: datetime,
        payload: dict[str, JsonValue],
    ) -> EventEnvelope:
        return EventEnvelope(
            event_id=uuid4(),
            event_type=event_type,
            event_version=1,
            occurred_at=occurred_at,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            aggregate_type="model",
            aggregate_id=model_version_id,
            payload=payload,
        )
