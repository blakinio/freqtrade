from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StrictBool
from sqlalchemy import select

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent, AuditResult
from ai_platform.portal.contracts.bots import BotInstance, BotObservedState
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.runtime_generation import (
    ReconciliationCompletenessStatus,
    ReconciliationFreshnessStatus,
    RuntimeGeneration,
    RuntimeGenerationObservation,
    RuntimeIdentityStatus,
)
from ai_platform.portal.control_plane._service_core import (
    BotNotFoundError,
    ControlPlaneConflictError,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.models import (
    BotRolloutRow,
    BotRow,
    RuntimeGenerationObservationRow,
)
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.security.authorization import require_permission


EXTERNAL_ADOPTION_REASON = "EXTERNAL_RUNTIME_ADOPTED"
_PENDING_ADOPTION_ROLLOUT_STATES = {
    "REQUESTED",
    "PRECHECK",
    "PROVISIONING",
    "STARTING",
    "VERIFYING",
}


class RuntimeObservationReconciliation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot: BotInstance
    generation: RuntimeGeneration
    observation: RuntimeGenerationObservation
    adopted_external_runtime: StrictBool = True


def _restore_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _observation_from_row(row: RuntimeGenerationObservationRow) -> RuntimeGenerationObservation:
    return RuntimeGenerationObservation(
        observation_id=row.observation_id,
        generation_id=row.generation_id,
        runtime_instance_id=row.runtime_instance_id,
        reconciliation_epoch=row.reconciliation_epoch,
        reconciliation_attempt=row.reconciliation_attempt,
        observed_state=row.observed_state,
        observed_generation_spec_digest=row.observed_generation_spec_digest,
        observed_image_digest=row.observed_image_digest,
        observed_config_digest=row.observed_config_digest,
        source_sequence=row.source_sequence,
        source_version=row.source_version,
        source_observed_at=_restore_utc(row.source_observed_at),
        reconciled_at=_restore_utc(row.reconciled_at),
        identity_status=row.identity_status,
        freshness_status=row.freshness_status,
        completeness_status=row.completeness_status,
        evidence_hash=row.evidence_hash,
        reason_code=row.reason_code,
    )


def _add_observation(session: object, observation: RuntimeGenerationObservation) -> None:
    session.add(
        RuntimeGenerationObservationRow(
            observation_id=observation.observation_id,
            generation_id=observation.generation_id,
            runtime_instance_id=observation.runtime_instance_id,
            reconciliation_epoch=observation.reconciliation_epoch,
            reconciliation_attempt=observation.reconciliation_attempt,
            observed_state=observation.observed_state,
            observed_generation_spec_digest=observation.observed_generation_spec_digest,
            observed_image_digest=observation.observed_image_digest,
            observed_config_digest=observation.observed_config_digest,
            source_sequence=observation.source_sequence,
            source_version=observation.source_version,
            source_observed_at=observation.source_observed_at,
            reconciled_at=observation.reconciled_at,
            identity_status=observation.identity_status.value,
            freshness_status=observation.freshness_status.value,
            completeness_status=observation.completeness_status.value,
            evidence_hash=observation.evidence_hash,
            reason_code=observation.reason_code,
        )
    )


def _validate_exact_observation(
    *, generation: RuntimeGeneration, observation: RuntimeGenerationObservation
) -> BotObservedState:
    if observation.generation_id != generation.generation_id:
        raise ControlPlaneConflictError("runtime observation generation mismatch")
    if observation.observed_generation_spec_digest != generation.generation_spec_digest:
        raise ControlPlaneConflictError("runtime generation spec digest mismatch")
    if observation.observed_image_digest != generation.runtime_image_digest:
        raise ControlPlaneConflictError("runtime image digest mismatch")
    if observation.observed_config_digest != generation.normalized_runtime_config_digest:
        raise ControlPlaneConflictError("runtime config digest mismatch")
    if observation.identity_status is not RuntimeIdentityStatus.MATCHED:
        raise ControlPlaneConflictError("runtime identity is not matched")
    if observation.freshness_status is not ReconciliationFreshnessStatus.CURRENT:
        raise ControlPlaneConflictError("runtime observation is not current")
    if observation.completeness_status is not ReconciliationCompletenessStatus.COMPLETE:
        raise ControlPlaneConflictError("runtime observation is incomplete")
    try:
        observed_state = BotObservedState(observation.observed_state)
    except ValueError as exc:
        raise ControlPlaneConflictError("runtime observed state is unsupported") from exc
    if observed_state is not BotObservedState.RUNNING:
        raise ControlPlaneConflictError("external runtime adoption requires RUNNING observation")
    return observed_state


class RuntimeAdoptionService:
    """Trusted system reconciliation for a runtime that already exists outside Portal.

    This service never creates, starts, stops, restarts or replaces a runtime. It only
    converges a canonical desired RuntimeGeneration to observed after exact immutable
    identity evidence is supplied by the host-side reconciler.
    """

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory
        self._repository = BotRepository()

    def adopt_external_runtime(
        self,
        context: RequestContext,
        bot_id: str,
        observation: RuntimeGenerationObservation,
    ) -> RuntimeObservationReconciliation:
        require_permission(context.permissions, Permission.ADMIN_MANAGE)

        with self._session_factory() as session, session.begin():
            bot = self._repository.get_bot(session, context.tenant_id, bot_id)
            if bot is None:
                raise BotNotFoundError("bot not found")
            if bot.desired_runtime_generation_id != observation.generation_id:
                raise ControlPlaneConflictError(
                    "external runtime may only adopt the canonical desired generation"
                )
            if (
                bot.observed_runtime_generation_id is not None
                and bot.observed_runtime_generation_id != observation.generation_id
            ):
                raise ControlPlaneConflictError(
                    "bot is already bound to a different observed RuntimeGeneration"
                )
            generation = self._repository.get_runtime_generation(
                session, context.tenant_id, observation.generation_id
            )
            if generation is None or generation.bot_id != bot_id:
                raise ControlPlaneConflictError("runtime generation does not belong to bot")

            observed_state = _validate_exact_observation(
                generation=generation,
                observation=observation,
            )

            existing = session.get(RuntimeGenerationObservationRow, observation.observation_id)
            if existing is not None:
                persisted = _observation_from_row(existing)
                if persisted != observation:
                    raise ControlPlaneConflictError(
                        "runtime observation id already has different immutable evidence"
                    )
                current = self._repository.get_bot(session, context.tenant_id, bot_id)
                if current is None:
                    raise BotNotFoundError("bot not found")
                if current.observed_runtime_generation_id != generation.generation_id:
                    raise ControlPlaneConflictError(
                        "persisted observation does not match current observed generation"
                    )
                return RuntimeObservationReconciliation(
                    bot=current,
                    generation=generation,
                    observation=persisted,
                )

            latest = session.scalar(
                select(RuntimeGenerationObservationRow)
                .where(RuntimeGenerationObservationRow.generation_id == generation.generation_id)
                .order_by(
                    RuntimeGenerationObservationRow.reconciled_at.desc(),
                    RuntimeGenerationObservationRow.observation_id.desc(),
                )
                .limit(1)
            )
            if latest is not None and latest.runtime_instance_id != observation.runtime_instance_id:
                raise ControlPlaneConflictError(
                    "runtime instance changed within immutable RuntimeGeneration"
                )

            rollout = session.scalar(
                select(BotRolloutRow)
                .where(
                    BotRolloutRow.tenant_id == context.tenant_id,
                    BotRolloutRow.bot_id == bot_id,
                    BotRolloutRow.to_generation_id == generation.generation_id,
                )
                .order_by(BotRolloutRow.updated_at.desc(), BotRolloutRow.rollout_id.desc())
                .limit(1)
            )
            if rollout is None:
                raise ControlPlaneConflictError(
                    "external runtime adoption requires a canonical rollout"
                )
            if rollout.status == "SUCCEEDED":
                if rollout.reason_code != EXTERNAL_ADOPTION_REASON:
                    raise ControlPlaneConflictError(
                        "successful rollout was not established by external adoption"
                    )
            elif rollout.status not in _PENDING_ADOPTION_ROLLOUT_STATES:
                raise ControlPlaneConflictError(
                    "rollout state does not permit external runtime adoption"
                )

            _add_observation(session, observation)
            row = session.get(BotRow, (context.tenant_id, bot_id))
            if row is None:
                raise BotNotFoundError("bot not found")
            row.observed_runtime_generation_id = generation.generation_id
            row.observed_state = observed_state.value
            row.state_version = (row.state_version or 0) + 1

            if rollout.status != "SUCCEEDED":
                rollout.status = "SUCCEEDED"
                rollout.reason_code = EXTERNAL_ADOPTION_REASON
                rollout.updated_at = observation.reconciled_at
                rollout.completed_at = observation.reconciled_at

            self._repository.add_audit_event(
                session,
                AuditEvent(
                    audit_id=uuid4(),
                    occurred_at=observation.reconciled_at,
                    actor_type=context.actor_type,
                    actor_id=context.actor_id,
                    tenant_id=context.tenant_id,
                    resource_type="bot",
                    resource_id=bot_id,
                    action=AuditAction.BOT_RUNTIME_ADOPTED,
                    result=AuditResult.SUCCEEDED,
                    request_id=context.request_id,
                    correlation_id=context.correlation_id,
                    causation_id=context.causation_id,
                    reason_code=EXTERNAL_ADOPTION_REASON,
                    details={
                        "generation_id": generation.generation_id,
                        "runtime_instance_id": observation.runtime_instance_id,
                        "observation_id": observation.observation_id,
                        "evidence_hash": observation.evidence_hash,
                        "provenance": EXTERNAL_ADOPTION_REASON,
                    },
                ),
            )
            session.flush()
            updated = self._repository.get_bot(session, context.tenant_id, bot_id)
            if updated is None:
                raise BotNotFoundError("bot not found")

        return RuntimeObservationReconciliation(
            bot=updated,
            generation=generation,
            observation=observation,
        )


def reconcile_external_runtime_observation(
    session_factory: SessionFactory,
    context: RequestContext,
    bot_id: str,
    observation: RuntimeGenerationObservation,
) -> RuntimeObservationReconciliation:
    return RuntimeAdoptionService(session_factory).adopt_external_runtime(
        context,
        bot_id,
        observation,
    )


def latest_runtime_observation(
    session_factory: SessionFactory,
    context: RequestContext,
    bot_id: str,
) -> RuntimeGenerationObservation | None:
    require_permission(context.permissions, Permission.BOT_READ)
    repository = BotRepository()
    with session_factory() as session:
        bot = repository.get_bot(session, context.tenant_id, bot_id)
        if bot is None:
            raise BotNotFoundError("bot not found")
        if bot.observed_runtime_generation_id is None:
            return None
        row = session.scalar(
            select(RuntimeGenerationObservationRow)
            .where(
                RuntimeGenerationObservationRow.generation_id
                == bot.observed_runtime_generation_id
            )
            .order_by(
                RuntimeGenerationObservationRow.reconciled_at.desc(),
                RuntimeGenerationObservationRow.observation_id.desc(),
            )
            .limit(1)
        )
        return _observation_from_row(row) if row is not None else None


def build_router(
    session_factory: SessionFactory,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(tags=["runtime-generation"])

    @router.get(
        "/v1/bots/{bot_id}/runtime-observations/latest",
        response_model=RuntimeGenerationObservation | None,
    )
    def get_latest_runtime_observation(
        bot_id: str,
        context: RequestContext = Depends(context_dependency),
    ) -> RuntimeGenerationObservation | None:
        return latest_runtime_observation(session_factory, context, bot_id)

    return router
