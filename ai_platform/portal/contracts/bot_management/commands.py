from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import PositiveInt, model_validator

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.policies import FractionDecimal, PositiveDecimal
from ai_platform.portal.contracts.common import (
    ContractModel,
    CorrelationContext,
    NonEmptyStr,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor


class LifecycleAction(StrEnum):
    START = "START"
    PAUSE_NEW_ENTRIES = "PAUSE_NEW_ENTRIES"
    RESUME = "RESUME"
    STOP_KEEP_POSITIONS = "STOP_KEEP_POSITIONS"
    STOP_AFTER_EXIT = "STOP_AFTER_EXIT"
    RESTART_RUNTIME = "RESTART_RUNTIME"
    RETIRE = "RETIRE"


class PositionAction(StrEnum):
    CLOSE_POSITION = "CLOSE_POSITION"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    CLOSE_ALL = "CLOSE_ALL"
    FORCE_TAKE_PROFIT = "FORCE_TAKE_PROFIT"


class OrderAction(StrEnum):
    CANCEL_ORDER = "CANCEL_ORDER"
    CANCEL_ALL_ORDERS = "CANCEL_ALL_ORDERS"
    REPLACE_ORDER = "REPLACE_ORDER"


class ConfirmationMethod(StrEnum):
    USER_CONFIRMATION = "user_confirmation"
    STEP_UP_MFA = "step_up_mfa"
    DUAL_CONTROL = "dual_control"


class CommandOutcomeStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    PENDING_RECONCILIATION = "PENDING_RECONCILIATION"


class CommandReasonCode(StrEnum):
    CAPABILITY_MISSING = "CAPABILITY_MISSING"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    DUPLICATE_IDEMPOTENCY_KEY = "DUPLICATE_IDEMPOTENCY_KEY"
    ENVIRONMENT_MISMATCH = "ENVIRONMENT_MISMATCH"
    INVALID_COMMAND = "INVALID_COMMAND"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    RISK_REJECTED = "RISK_REJECTED"
    RUNTIME_UNAVAILABLE = "RUNTIME_UNAVAILABLE"
    RUNTIME_RESPONSE_AMBIGUOUS = "RUNTIME_RESPONSE_AMBIGUOUS"
    STALE_GENERATION = "STALE_GENERATION"
    STALE_REVISION = "STALE_REVISION"
    TENANT_MISMATCH = "TENANT_MISMATCH"


class CommandTarget(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    config_revision: PositiveInt
    runtime_generation_id: NonEmptyStr
    runtime_id: NonEmptyStr
    runtime_revision: PositiveInt


class CommandConfirmationRequirement(ContractModel):
    required: bool
    step_up_required: bool = False
    method: ConfirmationMethod | None = None
    confirmation_reference: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_confirmation(self) -> Self:
        if not self.required:
            if (
                self.step_up_required
                or self.method is not None
                or self.confirmation_reference is not None
            ):
                raise ValueError("optional confirmation must not contain confirmation metadata")
        else:
            if self.method is None:
                raise ValueError("required confirmation must declare a method")
            if self.step_up_required and self.method != ConfirmationMethod.STEP_UP_MFA:
                raise ValueError("step-up confirmation must use the step-up MFA method")
        return self


class CommandEnvelope(ContractModel):
    command_id: NonEmptyStr
    tenant_id: NonEmptyStr
    actor: Actor
    environment: Environment
    correlation: CorrelationContext
    idempotency_key: NonEmptyStr
    target: CommandTarget
    capability: BotManagementCapability
    confirmation: CommandConfirmationRequirement
    submitted_at: UtcDateTime

    @model_validator(mode="after")
    def validate_context(self) -> Self:
        if self.actor.tenant_id != self.tenant_id:
            raise ValueError("command actor must belong to the command tenant")
        if self.target.tenant_id != self.tenant_id:
            raise ValueError("command target must belong to the command tenant")
        return self


class BotLifecycleCommand(CommandEnvelope):
    action: LifecycleAction

    @model_validator(mode="after")
    def validate_capability(self) -> Self:
        expected = {
            LifecycleAction.START: BotManagementCapability.BOT_START,
            LifecycleAction.PAUSE_NEW_ENTRIES: BotManagementCapability.BOT_PAUSE,
            LifecycleAction.RESUME: BotManagementCapability.BOT_START,
            LifecycleAction.STOP_KEEP_POSITIONS: BotManagementCapability.BOT_STOP,
            LifecycleAction.STOP_AFTER_EXIT: BotManagementCapability.BOT_STOP,
            LifecycleAction.RESTART_RUNTIME: BotManagementCapability.BOT_START,
            LifecycleAction.RETIRE: BotManagementCapability.BOT_RETIRE,
        }[self.action]
        if self.capability != expected:
            raise ValueError("lifecycle action capability does not match the action")
        return self


class PositionCommand(CommandEnvelope):
    action: PositionAction
    position_id: NonEmptyStr | None = None
    position_revision: PositiveInt | None = None
    close_fraction: FractionDecimal | None = None
    close_quantity: PositiveDecimal | None = None

    @model_validator(mode="after")
    def validate_position_command(self) -> Self:
        expected = {
            PositionAction.CLOSE_POSITION: BotManagementCapability.POSITION_CLOSE,
            PositionAction.PARTIAL_CLOSE: BotManagementCapability.POSITION_PARTIAL_CLOSE,
            PositionAction.CLOSE_ALL: BotManagementCapability.POSITION_CLOSE_ALL,
            PositionAction.FORCE_TAKE_PROFIT: BotManagementCapability.POSITION_CLOSE,
        }[self.action]
        if self.capability != expected:
            raise ValueError("position action capability does not match the action")
        if self.action == PositionAction.CLOSE_ALL:
            if any(
                value is not None
                for value in (
                    self.position_id,
                    self.position_revision,
                    self.close_fraction,
                    self.close_quantity,
                )
            ):
                raise ValueError("close-all command must not target one position")
            return self
        if self.position_id is None or self.position_revision is None:
            raise ValueError("position command requires exact position identity and revision")
        if self.action == PositionAction.PARTIAL_CLOSE:
            supplied = sum(
                value is not None for value in (self.close_fraction, self.close_quantity)
            )
            if supplied != 1:
                raise ValueError("partial close requires exactly one quantity or fraction")
        elif self.close_fraction is not None or self.close_quantity is not None:
            raise ValueError("non-partial position command must not declare partial size")
        return self


class OrderCommand(CommandEnvelope):
    action: OrderAction
    order_id: NonEmptyStr | None = None
    order_revision: PositiveInt | None = None
    replacement_price: PositiveDecimal | None = None
    replacement_quantity: PositiveDecimal | None = None

    @model_validator(mode="after")
    def validate_order_command(self) -> Self:
        expected = {
            OrderAction.CANCEL_ORDER: BotManagementCapability.ORDER_CANCEL,
            OrderAction.CANCEL_ALL_ORDERS: BotManagementCapability.ORDER_CANCEL_ALL,
            OrderAction.REPLACE_ORDER: BotManagementCapability.ORDER_REPLACE,
        }[self.action]
        if self.capability != expected:
            raise ValueError("order action capability does not match the action")
        if self.action == OrderAction.CANCEL_ALL_ORDERS:
            if any(
                value is not None
                for value in (
                    self.order_id,
                    self.order_revision,
                    self.replacement_price,
                    self.replacement_quantity,
                )
            ):
                raise ValueError("cancel-all command must not target one order")
            return self
        if self.order_id is None or self.order_revision is None:
            raise ValueError("order command requires exact order identity and revision")
        if self.action == OrderAction.REPLACE_ORDER:
            if self.replacement_price is None and self.replacement_quantity is None:
                raise ValueError("replace-order requires a replacement price or quantity")
        elif self.replacement_price is not None or self.replacement_quantity is not None:
            raise ValueError("cancel-order must not contain replacement values")
        return self


def _validate_outcome_reason_codes(outcome: CommandOutcome) -> None:
    reasons = [reason.value for reason in outcome.reason_codes]
    if len(reasons) != len(set(reasons)):
        raise ValueError("command outcome reason codes must be unique")
    if reasons != sorted(reasons):
        raise ValueError("command outcome reason codes must use sorted order")


def _validate_outcome_status(outcome: CommandOutcome) -> None:
    if outcome.status == CommandOutcomeStatus.ACCEPTED:
        if outcome.reason_codes or outcome.reconciliation_ref is not None:
            raise ValueError("ACCEPTED is not execution success or reconciliation")
    if outcome.status in {CommandOutcomeStatus.REJECTED, CommandOutcomeStatus.BLOCKED}:
        if not outcome.reason_codes:
            raise ValueError("rejected or blocked outcome requires a reason code")
        if outcome.execution_attempt_ref is not None or outcome.reconciliation_ref is not None:
            raise ValueError("rejected or blocked command must not have execution evidence")
    if (
        outcome.status == CommandOutcomeStatus.PENDING_RECONCILIATION
        and outcome.execution_attempt_ref is None
    ):
        raise ValueError("pending reconciliation requires an execution attempt reference")


def _validate_outcome_revision(outcome: CommandOutcome) -> None:
    stale = CommandReasonCode.STALE_REVISION in outcome.reason_codes
    if stale:
        if outcome.observed_config_revision is None:
            raise ValueError("stale revision outcome requires observed revision")
        if outcome.observed_config_revision == outcome.target.config_revision:
            raise ValueError("stale revision outcome must show a different revision")
        return
    if (
        outcome.observed_config_revision is not None
        and outcome.observed_config_revision != outcome.target.config_revision
    ):
        raise ValueError("revision mismatch must use STALE_REVISION reason code")


def _validate_outcome_generation(outcome: CommandOutcome) -> None:
    stale = CommandReasonCode.STALE_GENERATION in outcome.reason_codes
    if stale:
        if outcome.observed_runtime_generation_id is None:
            raise ValueError("stale generation outcome requires observed generation")
        if outcome.observed_runtime_generation_id == outcome.target.runtime_generation_id:
            raise ValueError("stale generation outcome must show a different generation")
        return
    if (
        outcome.observed_runtime_generation_id is not None
        and outcome.observed_runtime_generation_id != outcome.target.runtime_generation_id
    ):
        raise ValueError("generation mismatch must use STALE_GENERATION reason code")


class CommandOutcome(ContractModel):
    command_id: NonEmptyStr
    tenant_id: NonEmptyStr
    target: CommandTarget
    status: CommandOutcomeStatus
    reason_codes: tuple[CommandReasonCode, ...] = ()
    observed_config_revision: PositiveInt | None = None
    observed_runtime_generation_id: NonEmptyStr | None = None
    execution_attempt_ref: NonEmptyStr | None = None
    reconciliation_ref: NonEmptyStr | None = None
    decided_at: UtcDateTime

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        if self.target.tenant_id != self.tenant_id:
            raise ValueError("command outcome target must belong to the outcome tenant")
        _validate_outcome_reason_codes(self)
        _validate_outcome_status(self)
        _validate_outcome_revision(self)
        _validate_outcome_generation(self)
        return self
