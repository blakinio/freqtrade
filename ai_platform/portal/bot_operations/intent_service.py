from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import PositiveInt, model_validator

from ai_platform.portal.bot_operations.lifecycle import lifecycle_command_policy
from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
)
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    CommandConfirmationRequirement,
    CommandOutcomeStatus,
    CommandReasonCode,
    CommandTarget,
    ConfirmationMethod,
    LifecycleAction,
)
from ai_platform.portal.contracts.common import (
    ContractModel,
    CorrelationContext,
    NonEmptyStr,
)
from ai_platform.portal.contracts.identity import Actor


Clock = Callable[[], datetime]
IdFactory = Callable[[], UUID]


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


class LifecycleIntentContext(ContractModel):
    tenant_id: NonEmptyStr
    actor: Actor
    capabilities: tuple[BotManagementCapability, ...]
    correlation: CorrelationContext

    @model_validator(mode="after")
    def validate_context(self) -> LifecycleIntentContext:
        if self.actor.tenant_id != self.tenant_id:
            raise ValueError("lifecycle intent actor must belong to the tenant")
        values = [capability.value for capability in self.capabilities]
        if len(values) != len(set(values)) or values != sorted(values):
            raise ValueError("lifecycle intent capabilities must be unique and sorted")
        return self


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

    @model_validator(mode="after")
    def validate_result(self) -> LifecycleIntentResult:
        if self.command_persisted != (self.command_id is not None):
            raise ValueError("persisted lifecycle intent must expose exactly one command id")
        if self.execution_submission_performed:
            raise ValueError("BMW-02 must not perform execution submission")
        return self


class LifecycleCommandIntentService:
    """Prepare and persist BM-03 lifecycle intent without executing it."""

    def __init__(
        self,
        commands: BotCommandService,
        runtime_states: AuthoritativeBotRuntimeStateProvider,
        *,
        clock: Clock | None = None,
        id_factory: IdFactory = uuid4,
    ) -> None:
        self._commands = commands
        self._runtime_states = runtime_states
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    def submit(
        self,
        context: LifecycleIntentContext,
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
        command = BotLifecycleCommand(
            command_id=str(self._id_factory()),
            tenant_id=context.tenant_id,
            actor=context.actor,
            environment=runtime.environment,
            correlation=context.correlation,
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
                confirmation_reference=f"portal-request:{context.correlation.request_id}",
            ),
            submitted_at=self._clock(),
            action=request.action,
        )
        command_context = BotCommandContext(
            tenant_id=context.tenant_id,
            actor=context.actor,
            environment=runtime.environment,
            capabilities=context.capabilities,
        )
        outcome = self._commands.submit_lifecycle(command_context, command, runtime)
        command_persisted = CommandReasonCode.DUPLICATE_IDEMPOTENCY_KEY not in outcome.reason_codes
        return LifecycleIntentResult(
            command_id=outcome.command_id if command_persisted else None,
            bot_id=request.bot_id,
            action=request.action,
            status=outcome.status,
            reason_codes=outcome.reason_codes,
            command_persisted=command_persisted,
        )
