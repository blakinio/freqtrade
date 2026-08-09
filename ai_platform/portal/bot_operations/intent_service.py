from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol, Self
from uuid import UUID, uuid4

from pydantic import PositiveInt, model_validator

from ai_platform.portal.bot_operations.command_store import BotCommandStore
from ai_platform.portal.bot_operations.lifecycle import lifecycle_command_policy
from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
    BotOperationCommand,
)
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    CommandConfirmationRequirement,
    CommandOutcome,
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
from ai_platform.portal.control_plane.database import SessionFactory


Clock = Callable[[], datetime]
IdFactory = Callable[[], UUID]
IdempotentCommand = tuple[BotOperationCommand, CommandOutcome]


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


class IdempotentCommandLookup(Protocol):
    def find(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
    ) -> IdempotentCommand | None: ...


class UnavailableIdempotentCommandLookup:
    def find(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
    ) -> IdempotentCommand | None:
        del tenant_id, idempotency_key
        return None


class SqlAlchemyIdempotentCommandLookup:
    """Read existing append-only BM-03 evidence without changing command semantics."""

    def __init__(
        self,
        session_factory: SessionFactory,
        store: BotCommandStore | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._store = store or BotCommandStore()

    def find(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
    ) -> IdempotentCommand | None:
        with self._session_factory() as session:
            stored = self._store.get_by_idempotency_key(
                session,
                tenant_id,
                idempotency_key,
            )
            if stored is None:
                return None
            history = self._store.list_history(
                session,
                tenant_id,
                stored.command.command_id,
            )
            if not history:
                raise RuntimeError("idempotent command history is missing")
            return stored.command, history[-1].outcome


class LifecycleIntentContext(ContractModel):
    tenant_id: NonEmptyStr
    actor: Actor
    capabilities: tuple[BotManagementCapability, ...]
    correlation: CorrelationContext

    @model_validator(mode="after")
    def validate_context(self) -> Self:
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
    expected_runtime_generation_id: NonEmptyStr
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
    def validate_result(self) -> Self:
        if self.command_persisted != (self.command_id is not None):
            raise ValueError("persisted lifecycle intent must expose exactly one command id")
        if self.execution_submission_performed:
            raise ValueError("BMW-02 must not perform execution submission")
        return self


class LifecycleCommandIntentService:
    """Prepare and persist a BM-03 lifecycle command intent without executing it."""

    def __init__(
        self,
        commands: BotCommandService,
        runtime_states: AuthoritativeBotRuntimeStateProvider,
        *,
        idempotency_lookup: IdempotentCommandLookup | None = None,
        clock: Clock | None = None,
        id_factory: IdFactory = uuid4,
    ) -> None:
        self._commands = commands
        self._runtime_states = runtime_states
        self._idempotency_lookup = idempotency_lookup or UnavailableIdempotentCommandLookup()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    def submit(
        self,
        context: LifecycleIntentContext,
        request: LifecycleIntentRequest,
    ) -> LifecycleIntentResult:
        policy = lifecycle_command_policy(request.action)
        existing = self._idempotency_lookup.find(
            tenant_id=context.tenant_id,
            idempotency_key=request.idempotency_key,
        )
        if existing is not None:
            existing_command, existing_outcome = existing
            if self._is_transport_replay(context, request, policy.capability, existing_command):
                return LifecycleIntentResult(
                    command_id=existing_outcome.command_id,
                    bot_id=request.bot_id,
                    action=request.action,
                    status=existing_outcome.status,
                    reason_codes=existing_outcome.reason_codes,
                    command_persisted=True,
                )

        runtime = self._runtime_states.resolve(
            tenant_id=context.tenant_id,
            bot_id=request.bot_id,
        )
        if runtime is None:
            if existing is not None:
                return LifecycleIntentResult(
                    bot_id=request.bot_id,
                    action=request.action,
                    status=CommandOutcomeStatus.REJECTED,
                    reason_codes=(CommandReasonCode.DUPLICATE_IDEMPOTENCY_KEY,),
                    command_persisted=False,
                )
            return LifecycleIntentResult(
                bot_id=request.bot_id,
                action=request.action,
                status=CommandOutcomeStatus.BLOCKED,
                reason_codes=(CommandReasonCode.RUNTIME_UNAVAILABLE,),
                command_persisted=False,
            )

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
                runtime_generation_id=request.expected_runtime_generation_id,
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
        outcome = self._commands.submit_lifecycle(
            BotCommandContext(
                tenant_id=context.tenant_id,
                actor=context.actor,
                environment=runtime.environment,
                capabilities=context.capabilities,
            ),
            command,
            runtime,
        )
        conflict = CommandReasonCode.DUPLICATE_IDEMPOTENCY_KEY in outcome.reason_codes
        return LifecycleIntentResult(
            command_id=None if conflict else outcome.command_id,
            bot_id=request.bot_id,
            action=request.action,
            status=outcome.status,
            reason_codes=outcome.reason_codes,
            command_persisted=not conflict,
        )

    @staticmethod
    def _is_transport_replay(
        context: LifecycleIntentContext,
        request: LifecycleIntentRequest,
        required_capability: BotManagementCapability,
        existing_command: object,
    ) -> bool:
        return (
            isinstance(existing_command, BotLifecycleCommand)
            and existing_command.actor == context.actor
            and required_capability in context.capabilities
            and existing_command.capability == required_capability
            and existing_command.target.tenant_id == context.tenant_id
            and existing_command.target.bot_id == request.bot_id
            and existing_command.target.config_revision == request.expected_config_revision
            and existing_command.target.runtime_generation_id
            == request.expected_runtime_generation_id
            and existing_command.action == request.action
        )
