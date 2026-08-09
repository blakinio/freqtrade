from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, PositiveInt
from sqlalchemy import select

from ai_platform.portal.contracts.bots import BotConfigRevision, BotInstance
from ai_platform.portal.contracts.common import NonEmptyStr
from ai_platform.portal.contracts.runtime_generation import BotRollout, RuntimeGeneration
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.models import BotRolloutRow
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.service import (
    ControlPlaneService,
    RuntimeGenerationMaterialUnavailableError,
)
from ai_platform.wickhunter.runtime_mode import RuntimeModeResolutionError


class RevisionStateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_state_version: PositiveInt


class ActivateRevisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: NonEmptyStr
    expected_state_version: PositiveInt
    idempotency_key: NonEmptyStr


class RuntimeGenerationActivation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot: BotInstance
    generation: RuntimeGeneration
    rollout: BotRollout


class BotRuntimeTruth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot: BotInstance
    revisions: tuple[BotConfigRevision, ...]
    desired_generation: RuntimeGeneration | None
    observed_generation: RuntimeGeneration | None
    latest_rollout: BotRollout | None
    pending_rollout: bool


def _restore_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _rollout_from_row(row: BotRolloutRow | None) -> BotRollout | None:
    if row is None:
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


def _activation_response(
    service: ControlPlaneService,
    operation: str,
    request: ActivateRevisionRequest,
    context: RequestContext,
    bot_id: str,
) -> RuntimeGenerationActivation:
    try:
        if operation == "APPLY":
            result = service.apply_revision(
                context,
                bot_id,
                request.revision_id,
                request.expected_state_version,
                request.idempotency_key,
            )
        elif operation == "RESTART":
            result = service.restart_with_revision(
                context,
                bot_id,
                request.revision_id,
                request.expected_state_version,
                request.idempotency_key,
            )
        elif operation == "ROLLBACK":
            result = service.rollback_to_revision(
                context,
                bot_id,
                request.revision_id,
                request.expected_state_version,
                request.idempotency_key,
            )
        else:  # pragma: no cover - closed local call set
            raise ValueError("unsupported activation operation")
    except RuntimeModeResolutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.reason.value,
        ) from exc
    except RuntimeGenerationMaterialUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    bot, generation, rollout = result
    return RuntimeGenerationActivation(
        bot=bot,
        generation=generation,
        rollout=rollout,
    )


def build_router(
    service: ControlPlaneService,
    session_factory: SessionFactory,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(tags=["runtime-generation"])
    repository = BotRepository()

    @router.get("/v1/bots/{bot_id}/runtime-truth", response_model=BotRuntimeTruth)
    def runtime_truth(
        bot_id: str,
        context: RequestContext = Depends(context_dependency),
    ) -> BotRuntimeTruth:
        bot = service.get_bot(context, bot_id)
        with session_factory() as session:
            revisions = repository.list_revisions(session, context.tenant_id, bot_id)
            desired_generation = (
                repository.get_runtime_generation(
                    session,
                    context.tenant_id,
                    bot.desired_runtime_generation_id,
                )
                if bot.desired_runtime_generation_id is not None
                else None
            )
            observed_generation = (
                repository.get_runtime_generation(
                    session,
                    context.tenant_id,
                    bot.observed_runtime_generation_id,
                )
                if bot.observed_runtime_generation_id is not None
                else None
            )
            rollout_row = session.scalar(
                select(BotRolloutRow)
                .where(
                    BotRolloutRow.tenant_id == context.tenant_id,
                    BotRolloutRow.bot_id == bot_id,
                )
                .order_by(BotRolloutRow.updated_at.desc(), BotRolloutRow.rollout_id.desc())
                .limit(1)
            )
        return BotRuntimeTruth(
            bot=bot,
            revisions=revisions,
            desired_generation=desired_generation,
            observed_generation=observed_generation,
            latest_rollout=_rollout_from_row(rollout_row),
            pending_rollout=(
                bot.desired_runtime_generation_id != bot.observed_runtime_generation_id
            ),
        )

    @router.post(
        "/v1/bots/{bot_id}/revisions/{revision_id}/promote",
        response_model=BotConfigRevision,
    )
    def promote_revision(
        bot_id: str,
        revision_id: str,
        request: RevisionStateRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> BotConfigRevision:
        return service.promote_revision(
            context,
            bot_id,
            revision_id,
            request.expected_state_version,
        )

    @router.post(
        "/v1/bots/{bot_id}/revisions/{revision_id}/deprecate",
        response_model=BotConfigRevision,
    )
    def deprecate_revision(
        bot_id: str,
        revision_id: str,
        request: RevisionStateRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> BotConfigRevision:
        return service.deprecate_revision(
            context,
            bot_id,
            revision_id,
            request.expected_state_version,
        )

    @router.post(
        "/v1/bots/{bot_id}/apply",
        response_model=RuntimeGenerationActivation,
    )
    def apply_revision(
        bot_id: str,
        request: ActivateRevisionRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> RuntimeGenerationActivation:
        return _activation_response(service, "APPLY", request, context, bot_id)

    @router.post(
        "/v1/bots/{bot_id}/restart",
        response_model=RuntimeGenerationActivation,
    )
    def restart_with_revision(
        bot_id: str,
        request: ActivateRevisionRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> RuntimeGenerationActivation:
        return _activation_response(service, "RESTART", request, context, bot_id)

    @router.post(
        "/v1/bots/{bot_id}/rollback",
        response_model=RuntimeGenerationActivation,
    )
    def rollback_to_revision(
        bot_id: str,
        request: ActivateRevisionRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> RuntimeGenerationActivation:
        return _activation_response(service, "ROLLBACK", request, context, bot_id)

    return router
