from __future__ import annotations

from enum import StrEnum
from typing import Self, TypeAlias
from uuid import UUID

from pydantic import model_validator

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    CommandOutcome,
    CommandOutcomeStatus,
    CommandReasonCode,
    OrderCommand,
    PositionCommand,
)
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor
from ai_platform.portal.execution.private_read import RuntimeReadFreshness


BotOperationCommand: TypeAlias = BotLifecycleCommand | PositionCommand | OrderCommand


class BotOperationCommandKind(StrEnum):
    LIFECYCLE = "lifecycle"
    POSITION = "position"
    ORDER = "order"


class BotCommandEventType(StrEnum):
    ACCEPTED = "bot_command.accepted"
    REJECTED = "bot_command.rejected"
    BLOCKED = "bot_command.blocked"
    PENDING_RECONCILIATION = "bot_command.pending_reconciliation"


class BotCommandContext(ContractModel):
    """Trusted application context resolved before the feature service is called."""

    tenant_id: NonEmptyStr
    actor: Actor
    environment: Environment
    capabilities: tuple[BotManagementCapability, ...]

    @model_validator(mode="after")
    def validate_context(self) -> Self:
        if self.actor.tenant_id != self.tenant_id:
            raise ValueError("command context actor must belong to the context tenant")
        capability_values = [capability.value for capability in self.capabilities]
        if len(capability_values) != len(set(capability_values)):
            raise ValueError("command context capabilities must be unique")
        if capability_values != sorted(capability_values):
            raise ValueError("command context capabilities must use deterministic sorted order")
        return self


class AuthoritativeBotRuntimeState(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    config_revision: int
    runtime_generation_id: NonEmptyStr
    runtime_id: NonEmptyStr
    runtime_revision: int
    environment: Environment
    freshness: RuntimeReadFreshness
    kill_switch_active: bool
    observed_at: UtcDateTime

    @model_validator(mode="after")
    def validate_revisions(self) -> Self:
        if self.config_revision < 1 or self.runtime_revision < 1:
            raise ValueError("runtime bindings require positive revisions")
        return self


class PreparedCommandAudit(ContractModel):
    audit_id: UUID
    scope_tenant_id: NonEmptyStr
    attempted_tenant_id: NonEmptyStr
    actor: Actor
    command_id: NonEmptyStr
    command_kind: BotOperationCommandKind
    action: NonEmptyStr
    status: CommandOutcomeStatus
    reason_codes: tuple[CommandReasonCode, ...]
    occurred_at: UtcDateTime

    @model_validator(mode="after")
    def validate_reason_codes(self) -> Self:
        values = [reason.value for reason in self.reason_codes]
        if len(values) != len(set(values)) or values != sorted(values):
            raise ValueError("prepared audit reason codes must be unique and sorted")
        if self.actor.tenant_id != self.scope_tenant_id:
            raise ValueError("prepared audit actor must belong to the scope tenant")
        return self


class PreparedCommandEvent(ContractModel):
    event_id: UUID
    event_type: BotCommandEventType
    scope_tenant_id: NonEmptyStr
    attempted_tenant_id: NonEmptyStr
    actor_id: NonEmptyStr
    bot_id: NonEmptyStr
    command_id: NonEmptyStr
    command_kind: BotOperationCommandKind
    action: NonEmptyStr
    status: CommandOutcomeStatus
    reason_codes: tuple[CommandReasonCode, ...]
    occurred_at: UtcDateTime

    @model_validator(mode="after")
    def validate_reason_codes(self) -> Self:
        values = [reason.value for reason in self.reason_codes]
        if len(values) != len(set(values)) or values != sorted(values):
            raise ValueError("prepared event reason codes must be unique and sorted")
        expected = {
            CommandOutcomeStatus.ACCEPTED: BotCommandEventType.ACCEPTED,
            CommandOutcomeStatus.REJECTED: BotCommandEventType.REJECTED,
            CommandOutcomeStatus.BLOCKED: BotCommandEventType.BLOCKED,
            CommandOutcomeStatus.PENDING_RECONCILIATION: BotCommandEventType.PENDING_RECONCILIATION,
        }[self.status]
        if self.event_type != expected:
            raise ValueError("prepared event type must match the command outcome status")
        return self


class CommandHistoryEntry(ContractModel):
    history_id: UUID
    sequence: int
    command: BotOperationCommand
    outcome: CommandOutcome
    audit: PreparedCommandAudit
    event: PreparedCommandEvent
    recorded_at: UtcDateTime

    @model_validator(mode="after")
    def validate_binding(self) -> Self:
        if self.sequence < 1:
            raise ValueError("command history sequence must be positive")
        if self.command.command_id != self.outcome.command_id:
            raise ValueError("command history outcome must reference the command")
        if self.command.target != self.outcome.target:
            raise ValueError("command history outcome must preserve the exact target")
        if self.audit.command_id != self.command.command_id:
            raise ValueError("command history audit must reference the command")
        if self.event.command_id != self.command.command_id:
            raise ValueError("command history event must reference the command")
        if self.audit.status != self.outcome.status or self.event.status != self.outcome.status:
            raise ValueError("command history evidence must match the outcome status")
        if self.audit.reason_codes != self.outcome.reason_codes:
            raise ValueError("command history audit reasons must match the outcome")
        if self.event.reason_codes != self.outcome.reason_codes:
            raise ValueError("command history event reasons must match the outcome")
        return self


class IdempotencyConflictRecord(ContractModel):
    conflict_id: UUID
    scope_tenant_id: NonEmptyStr
    idempotency_key: NonEmptyStr
    existing_command_id: NonEmptyStr
    attempted_command: BotOperationCommand
    outcome: CommandOutcome
    audit: PreparedCommandAudit
    event: PreparedCommandEvent
    recorded_at: UtcDateTime

    @model_validator(mode="after")
    def validate_conflict(self) -> Self:
        if self.outcome.status != CommandOutcomeStatus.REJECTED:
            raise ValueError("idempotency conflict must be rejected")
        if self.outcome.reason_codes != (CommandReasonCode.DUPLICATE_IDEMPOTENCY_KEY,):
            raise ValueError("idempotency conflict must use the duplicate reason code")
        if self.attempted_command.idempotency_key != self.idempotency_key:
            raise ValueError("idempotency conflict key must match the attempted command")
        return self


def command_kind(command: BotOperationCommand) -> BotOperationCommandKind:
    if isinstance(command, BotLifecycleCommand):
        return BotOperationCommandKind.LIFECYCLE
    if isinstance(command, PositionCommand):
        return BotOperationCommandKind.POSITION
    return BotOperationCommandKind.ORDER
