from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends

from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
    CommandHistoryEntry,
    IdempotencyConflictRecord,
)
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    CommandOutcome,
    OrderCommand,
    PositionCommand,
)
from ai_platform.portal.contracts.common import ContractModel
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.control_plane.bot_management import (
    actor_from_request,
    capabilities_from_request,
)
from ai_platform.portal.control_plane.context import RequestContext


class LifecycleCommandRequest(ContractModel):
    command: BotLifecycleCommand
    runtime: AuthoritativeBotRuntimeState


class PositionCommandRequest(ContractModel):
    command: PositionCommand
    runtime: AuthoritativeBotRuntimeState


class OrderCommandRequest(ContractModel):
    command: OrderCommand
    runtime: AuthoritativeBotRuntimeState


def build_router(
    service: BotCommandService,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(prefix="/v1/bot-management/commands", tags=["bot-management"])

    def command_context(
        context: RequestContext,
        environment: Environment,
    ) -> BotCommandContext:
        return BotCommandContext(
            tenant_id=context.tenant_id,
            actor=actor_from_request(context),
            environment=environment,
            capabilities=capabilities_from_request(context),
        )

    @router.post("/lifecycle", response_model=CommandOutcome)
    def submit_lifecycle(
        request: LifecycleCommandRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> CommandOutcome:
        return service.submit_lifecycle(
            command_context(context, request.command.environment),
            request.command,
            request.runtime,
        )

    @router.post("/position", response_model=CommandOutcome)
    def submit_position(
        request: PositionCommandRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> CommandOutcome:
        return service.submit_position(
            command_context(context, request.command.environment),
            request.command,
            request.runtime,
        )

    @router.post("/order", response_model=CommandOutcome)
    def submit_order(
        request: OrderCommandRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> CommandOutcome:
        return service.submit_order(
            command_context(context, request.command.environment),
            request.command,
            request.runtime,
        )

    @router.get("/{command_id}/history", response_model=list[CommandHistoryEntry])
    def list_history(
        command_id: str,
        environment: Environment,
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[CommandHistoryEntry, ...]:
        return service.list_history(command_context(context, environment), command_id)

    @router.get("/idempotency/conflicts", response_model=list[IdempotencyConflictRecord])
    def list_idempotency_conflicts(
        environment: Environment,
        idempotency_key: str | None = None,
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[IdempotencyConflictRecord, ...]:
        return service.list_idempotency_conflicts(
            command_context(context, environment),
            idempotency_key,
        )

    return router
