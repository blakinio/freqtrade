from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import PositiveInt

from ai_platform.portal.bot_operations.lifecycle import lifecycle_command_policy
from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
)
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    CommandConfirmationRequirement,
    CommandOutcomeStatus,
    CommandReasonCode,
    CommandTarget,
    ConfirmationMethod,
    LifecycleAction,
)
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr


class AuthoritativeBotRuntimeStateProvider(Protocol):
    def resolve(
        self,
        *,
        tenant_id: str,
        bot_id: str,
    ) -> AuthoritativeBotRuntimeState | None: ...


class UnavailableBotRuntimeStateProvider:
    """Fail closed until an authoritative revisioned runtime source is injected."""

    def resolve(
        self,
        *,
        tenant_id: str,
        bot_id: str,
    ) -> AuthoritativeBotRuntimeState | None:
        del tenant_id, bot_id
        return None


class LifecycleIntentRequest(ContractModel):
    bot_id: NonEmptyStr
    action: LifecycleAction
    expected_config_revision: PositiveInt
    idempotency_key: NonEmptyStr


class LifecycleIntentResult(ContractModel):
    command_id: NonEmptyStr | None = None
    bot_id: NonEmptyStr
    action: LifecycleAction
    status: CommandOutcomeStatus
    reason_codes: tuple[CommandReasonCode, ...] = ()
    command_persisted: bool
    execution_submission_performed: bool = False


class LifecycleCommandIntentService:
    """Prepare and persist BM-03 lifecycle intent without executing it."""

    def __init__(
        self,
        commands: BotCommandService,
        runtime_states: AuthoritativeBotRuntimeStateProvider,
    ) -> None:
        self._commands = commands
        self._runtime_states = runtime_states

    def submit(
        self,
        context: BotCommandContext,
        request: LifecycleIntentRequest,
    ) -> LifecycleIntentResult:
        runtime = self._runtime_states.resolve(
            tenant_id=context.tenant_id,
            bot_id=request.bot_id,
        )
        if runtime is None:
            return LifecycleIntentResult(
                bot_id=request.bot_id,
                action=request.action,
                status=CommandOutcomeStatus.BLOCKED,
                reason_codes=(CommandReasonCode.RUNTIME_UNAVAILABLE,),
                command_persisted=False,
            )

        policy = lifecycle_command_policy(request.action)
        command_id = str(uuid4())
        command = BotLifecycleCommand(
            command_id=command_id,
            tenant_id=context.tenant_id,
            actor=context.actor,
            environment=runtime.environment,
            correlation={
                "request_id": uuid4(),
                "correlation_id": uuid4(),
                "causation_id": None,
            },
            idempotency_key=request.idempotency_key,
            target=CommandTarget(
                tenant_id=context.tenant_id,
                bot_id=request.bot_id,
                config_revision=request.expected_config_revision,
                runtime_id=runtime.runtime_id,
                runtime_revision=runtime.runtime_revision,
            ),
            capability=policy.capability,
            confirmation=CommandConfirmationRequirement(
                required=True,
                method=ConfirmationMethod.USER_CONFIRMATION,
                confirmation_reference=f"portal-request:{command_id}",
            ),
            submitted_at=datetime.now(UTC),
            action=request.action,
        )
        command_context = BotCommandContext(
            tenant_id=context.tenant_id,
            actor=context.actor,
            environment=runtime.environment,
            capabilities=context.capabilities,
        )
        outcome = self._commands.submit_lifecycle(command_context, command, runtime)
        return LifecycleIntentResult(
            command_id=command_id,
            bot_id=request.bot_id,
            action=request.action,
            status=outcome.status,
            reason_codes=outcome.reason_codes,
            command_persisted=True,
        )
