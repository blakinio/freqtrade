from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from ai_platform.portal.bot_operations.command_store import BotCommandStore
from ai_platform.portal.bot_operations.lifecycle import lifecycle_command_policy
from ai_platform.portal.bot_operations.order_commands import order_command_policy
from ai_platform.portal.bot_operations.position_commands import position_command_policy
from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
    BotCommandEventType,
    BotOperationCommand,
    BotOperationCommandKind,
    CommandHistoryEntry,
    IdempotencyConflictRecord,
    PreparedCommandAudit,
    PreparedCommandEvent,
    command_kind,
)
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    CommandOutcome,
    CommandOutcomeStatus,
    CommandReasonCode,
    OrderCommand,
    PositionCommand,
)
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.execution.private_read import RuntimeReadFreshness


class BotCommandNotFoundError(LookupError):
    pass


class BotCommandIdentityConflictError(RuntimeError):
    pass


class BotCommandTransitionError(RuntimeError):
    pass


class BotCommandReadDeniedError(PermissionError):
    pass


class _CommandPolicy(Protocol):
    capability: BotManagementCapability
    blocked_by_kill_switch: bool


Clock = Callable[[], datetime]
IdFactory = Callable[[], UUID]


class BotCommandService:
    """Persist command intent and evidence without invoking a runtime adapter."""

    def __init__(
        self,
        session_factory: SessionFactory,
        store: BotCommandStore | None = None,
        clock: Clock | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._store = store or BotCommandStore()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or uuid4

    def submit_lifecycle(
        self,
        context: BotCommandContext,
        command: BotLifecycleCommand,
        runtime: AuthoritativeBotRuntimeState,
    ) -> CommandOutcome:
        policy = lifecycle_command_policy(command.action)
        return self._submit(context, command, runtime, policy)

    def submit_position(
        self,
        context: BotCommandContext,
        command: PositionCommand,
        runtime: AuthoritativeBotRuntimeState,
    ) -> CommandOutcome:
        policy = position_command_policy(command.action)
        return self._submit(context, command, runtime, policy)

    def submit_order(
        self,
        context: BotCommandContext,
        command: OrderCommand,
        runtime: AuthoritativeBotRuntimeState,
    ) -> CommandOutcome:
        policy = order_command_policy(command.action)
        return self._submit(context, command, runtime, policy)

    def mark_pending_reconciliation(
        self,
        context: BotCommandContext,
        command_id: str,
        execution_attempt_ref: str,
    ) -> CommandOutcome:
        """Append an external attempt reference without claiming execution success."""

        occurred_at = self._clock()
        with self._session_factory() as session, session.begin():
            stored = self._store.get_command(session, context.tenant_id, command_id)
            if stored is None:
                raise BotCommandNotFoundError("bot command not found")
            if (
                stored.command.actor != context.actor
                or stored.command.environment != context.environment
                or stored.command.capability not in context.capabilities
            ):
                raise BotCommandTransitionError(
                    "pending reconciliation context must preserve command authorization"
                )
            history = self._store.list_history(
                session,
                context.tenant_id,
                command_id,
            )
            if not history:
                raise BotCommandTransitionError("bot command history is missing")
            latest = history[-1].outcome
            if latest.status == CommandOutcomeStatus.PENDING_RECONCILIATION:
                if latest.execution_attempt_ref == execution_attempt_ref:
                    return latest
                raise BotCommandTransitionError(
                    "pending reconciliation is already bound to another execution attempt"
                )
            if latest.status != CommandOutcomeStatus.ACCEPTED:
                raise BotCommandTransitionError(
                    "only an accepted command may become pending reconciliation"
                )
            outcome = CommandOutcome(
                command_id=stored.command.command_id,
                tenant_id=stored.command.tenant_id,
                target=stored.command.target,
                status=CommandOutcomeStatus.PENDING_RECONCILIATION,
                execution_attempt_ref=execution_attempt_ref,
                decided_at=occurred_at,
            )
            entry = self._history_entry(
                context,
                stored.kind,
                stored.command,
                outcome,
                sequence=history[-1].sequence + 1,
                occurred_at=occurred_at,
            )
            self._store.append_history(session, context.tenant_id, entry)
        return outcome

    def list_history(
        self,
        context: BotCommandContext,
        command_id: str,
    ) -> tuple[CommandHistoryEntry, ...]:
        self._require_command_read(context)
        with self._session_factory() as session:
            stored = self._store.get_command(
                session,
                context.tenant_id,
                command_id,
            )
            if stored is None:
                raise BotCommandNotFoundError("bot command not found")
            return self._store.list_history(
                session,
                context.tenant_id,
                command_id,
            )

    def list_idempotency_conflicts(
        self,
        context: BotCommandContext,
        idempotency_key: str | None = None,
    ) -> tuple[IdempotencyConflictRecord, ...]:
        self._require_command_read(context)
        with self._session_factory() as session:
            return self._store.list_idempotency_conflicts(
                session,
                context.tenant_id,
                idempotency_key,
            )

    def _submit(
        self,
        context: BotCommandContext,
        command: BotOperationCommand,
        runtime: AuthoritativeBotRuntimeState,
        policy: _CommandPolicy,
    ) -> CommandOutcome:
        kind = command_kind(command)
        command_json = command.canonical_json()
        digest = hashlib.sha256(command_json.encode()).hexdigest()
        occurred_at = self._clock()

        try:
            with self._session_factory() as session, session.begin():
                existing = self._store.get_by_idempotency_key(
                    session,
                    context.tenant_id,
                    command.idempotency_key,
                )
                if existing is not None:
                    history = self._store.list_history(
                        session,
                        context.tenant_id,
                        existing.command.command_id,
                    )
                    if existing.command_digest == digest:
                        if not history:
                            raise BotCommandTransitionError("idempotent command history is missing")
                        return history[-1].outcome
                    outcome = self._outcome(
                        command,
                        CommandOutcomeStatus.REJECTED,
                        (CommandReasonCode.DUPLICATE_IDEMPOTENCY_KEY,),
                        occurred_at,
                    )
                    audit, event = self._prepared_evidence(
                        context,
                        kind,
                        command,
                        outcome,
                        occurred_at,
                    )
                    conflict = IdempotencyConflictRecord(
                        conflict_id=self._id_factory(),
                        scope_tenant_id=context.tenant_id,
                        idempotency_key=command.idempotency_key,
                        existing_command_id=existing.command.command_id,
                        attempted_command=command,
                        outcome=outcome,
                        audit=audit,
                        event=event,
                        recorded_at=occurred_at,
                    )
                    self._store.add_idempotency_conflict(session, conflict)
                    return outcome

                stored_by_id = self._store.get_command(
                    session,
                    context.tenant_id,
                    command.command_id,
                )
                if stored_by_id is not None:
                    raise BotCommandIdentityConflictError("bot command identity already exists")

                status, reasons, observed_revision, observed_generation = self._decide(
                    context,
                    command,
                    runtime,
                    policy,
                )
                outcome = self._outcome(
                    command,
                    status,
                    reasons,
                    occurred_at,
                    observed_config_revision=observed_revision,
                    observed_runtime_generation_id=observed_generation,
                )
                entry = self._history_entry(
                    context,
                    kind,
                    command,
                    outcome,
                    sequence=1,
                    occurred_at=occurred_at,
                )
                self._store.add_command(
                    session,
                    context.tenant_id,
                    kind,
                    command,
                    digest,
                    entry,
                )
        except IntegrityError as exc:
            raise BotCommandIdentityConflictError("bot command persistence conflict") from exc
        return outcome

    @staticmethod
    def _decide(
        context: BotCommandContext,
        command: BotOperationCommand,
        runtime: AuthoritativeBotRuntimeState,
        policy: _CommandPolicy,
    ) -> tuple[
        CommandOutcomeStatus,
        tuple[CommandReasonCode, ...],
        int | None,
        str | None,
    ]:
        if command.tenant_id != context.tenant_id or runtime.tenant_id != context.tenant_id:
            return (
                CommandOutcomeStatus.REJECTED,
                (CommandReasonCode.TENANT_MISMATCH,),
                None,
                None,
            )
        if command.actor != context.actor:
            return (
                CommandOutcomeStatus.REJECTED,
                (CommandReasonCode.INVALID_COMMAND,),
                None,
                None,
            )
        if command.environment != context.environment or runtime.environment != context.environment:
            return (
                CommandOutcomeStatus.REJECTED,
                (CommandReasonCode.ENVIRONMENT_MISMATCH,),
                None,
                None,
            )
        if policy.capability not in context.capabilities or command.capability != policy.capability:
            return (
                CommandOutcomeStatus.REJECTED,
                (CommandReasonCode.CAPABILITY_MISSING,),
                None,
                None,
            )
        if runtime.bot_id != command.target.bot_id:
            return (
                CommandOutcomeStatus.REJECTED,
                (CommandReasonCode.INVALID_COMMAND,),
                None,
                None,
            )
        if runtime.config_revision != command.target.config_revision:
            return (
                CommandOutcomeStatus.REJECTED,
                (CommandReasonCode.STALE_REVISION,),
                runtime.config_revision,
                None,
            )
        if runtime.runtime_generation_id != command.target.runtime_generation_id:
            return (
                CommandOutcomeStatus.REJECTED,
                (CommandReasonCode.STALE_GENERATION,),
                None,
                runtime.runtime_generation_id,
            )
        if (
            runtime.runtime_id != command.target.runtime_id
            or runtime.runtime_revision != command.target.runtime_revision
        ):
            return (
                CommandOutcomeStatus.BLOCKED,
                (CommandReasonCode.RUNTIME_UNAVAILABLE,),
                None,
                None,
            )
        if runtime.freshness != RuntimeReadFreshness.CURRENT:
            return (
                CommandOutcomeStatus.BLOCKED,
                (CommandReasonCode.RUNTIME_UNAVAILABLE,),
                None,
                None,
            )
        if runtime.kill_switch_active and policy.blocked_by_kill_switch:
            return (
                CommandOutcomeStatus.BLOCKED,
                (CommandReasonCode.KILL_SWITCH_ACTIVE,),
                None,
                None,
            )
        return CommandOutcomeStatus.ACCEPTED, (), None, None

    @staticmethod
    def _outcome(
        command: BotOperationCommand,
        status: CommandOutcomeStatus,
        reasons: tuple[CommandReasonCode, ...],
        occurred_at: datetime,
        observed_config_revision: int | None = None,
        observed_runtime_generation_id: str | None = None,
    ) -> CommandOutcome:
        return CommandOutcome(
            command_id=command.command_id,
            tenant_id=command.tenant_id,
            target=command.target,
            status=status,
            reason_codes=tuple(sorted(reasons, key=lambda reason: reason.value)),
            observed_config_revision=observed_config_revision,
            observed_runtime_generation_id=observed_runtime_generation_id,
            decided_at=occurred_at,
        )

    def _history_entry(
        self,
        context: BotCommandContext,
        kind: BotOperationCommandKind,
        command: BotOperationCommand,
        outcome: CommandOutcome,
        *,
        sequence: int,
        occurred_at: datetime,
    ) -> CommandHistoryEntry:
        audit, event = self._prepared_evidence(
            context,
            kind,
            command,
            outcome,
            occurred_at,
        )
        return CommandHistoryEntry(
            history_id=self._id_factory(),
            sequence=sequence,
            command=command,
            outcome=outcome,
            audit=audit,
            event=event,
            recorded_at=occurred_at,
        )

    def _prepared_evidence(
        self,
        context: BotCommandContext,
        kind: BotOperationCommandKind,
        command: BotOperationCommand,
        outcome: CommandOutcome,
        occurred_at: datetime,
    ) -> tuple[PreparedCommandAudit, PreparedCommandEvent]:
        action = command.action.value
        audit = PreparedCommandAudit(
            audit_id=self._id_factory(),
            scope_tenant_id=context.tenant_id,
            attempted_tenant_id=command.tenant_id,
            actor=context.actor,
            command_id=command.command_id,
            command_kind=kind,
            action=action,
            status=outcome.status,
            reason_codes=outcome.reason_codes,
            occurred_at=occurred_at,
        )
        event_type = {
            CommandOutcomeStatus.ACCEPTED: BotCommandEventType.ACCEPTED,
            CommandOutcomeStatus.REJECTED: BotCommandEventType.REJECTED,
            CommandOutcomeStatus.BLOCKED: BotCommandEventType.BLOCKED,
            CommandOutcomeStatus.PENDING_RECONCILIATION: (
                BotCommandEventType.PENDING_RECONCILIATION
            ),
        }[outcome.status]
        event = PreparedCommandEvent(
            event_id=self._id_factory(),
            event_type=event_type,
            scope_tenant_id=context.tenant_id,
            attempted_tenant_id=command.tenant_id,
            actor_id=context.actor.actor_id,
            bot_id=command.target.bot_id,
            command_id=command.command_id,
            command_kind=kind,
            action=action,
            status=outcome.status,
            reason_codes=outcome.reason_codes,
            occurred_at=occurred_at,
        )
        return audit, event

    @staticmethod
    def _require_command_read(context: BotCommandContext) -> None:
        if BotManagementCapability.COMMAND_READ not in context.capabilities:
            raise BotCommandReadDeniedError("bot command read capability is required")
