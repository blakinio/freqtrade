from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import PositiveInt, model_validator

from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
)
from ai_platform.portal.contracts.bot_management.commands import (
    CommandOutcome,
    OrderAction,
    OrderCommand,
    PositionAction,
    PositionCommand,
)
from ai_platform.portal.contracts.bot_management.exchange_connections import CredentialReference
from ai_platform.portal.contracts.bot_management.policies import PositiveDecimal
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex, UtcDateTime
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.execution_submission.schema import PrivateDryRunSubmission


class CommandActivationState(StrEnum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    RESERVED = "RESERVED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    AMBIGUOUS = "AMBIGUOUS"
    REJECTED = "REJECTED"
    REPLAY_PENDING = "REPLAY_PENDING"


class PolicyEntrySource(StrEnum):
    DCA = "DCA"
    GRID = "GRID"


class RuntimePositionEvidence(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    runtime_id: NonEmptyStr
    position_id: NonEmptyStr
    position_revision: PositiveInt
    source_trade_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: PositiveDecimal
    observed_at: UtcDateTime


class RuntimeOrderEvidence(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    runtime_id: NonEmptyStr
    order_id: NonEmptyStr
    order_revision: PositiveInt
    source_trade_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    stake_amount: PositiveDecimal
    observed_at: UtcDateTime


class RuntimeCommandAcknowledgement(ContractModel):
    runtime_request_ref: NonEmptyStr
    response_digest: Sha256Hex
    acknowledged_at: UtcDateTime
    execution_proven: bool = False

    @model_validator(mode="after")
    def reject_execution_claim(self) -> Self:
        if self.execution_proven:
            raise ValueError("runtime command acknowledgement cannot prove execution")
        return self


class PositionCommandActivationRequest(ContractModel):
    context: BotCommandContext
    command: PositionCommand
    runtime: AuthoritativeBotRuntimeState
    runtime_health: RuntimeHealthState
    connection_id: NonEmptyStr
    credential_ref: CredentialReference
    exchange_id: NonEmptyStr
    positions: tuple[RuntimePositionEvidence, ...] = ()

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        _validate_common(self.context, self.command.tenant_id, self.runtime)
        if self.command.action == PositionAction.CLOSE_ALL:
            if self.positions:
                _validate_position_scope(self.runtime, self.positions)
            return self
        matches = [
            item
            for item in self.positions
            if item.position_id == self.command.position_id
            and item.position_revision == self.command.position_revision
        ]
        if len(matches) != 1:
            raise ValueError("position command requires one exact runtime position evidence record")
        _validate_position_scope(self.runtime, tuple(matches))
        if self.command.action == PositionAction.PARTIAL_CLOSE:
            quantity = self.command.close_quantity
            if quantity is not None and quantity >= matches[0].amount:
                raise ValueError("partial close quantity must be below current position amount")
        return self


class OrderCommandActivationRequest(ContractModel):
    context: BotCommandContext
    command: OrderCommand
    runtime: AuthoritativeBotRuntimeState
    runtime_health: RuntimeHealthState
    connection_id: NonEmptyStr
    credential_ref: CredentialReference
    exchange_id: NonEmptyStr
    orders: tuple[RuntimeOrderEvidence, ...] = ()
    replacement_submission: PrivateDryRunSubmission | None = None

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        _validate_common(self.context, self.command.tenant_id, self.runtime)
        _validate_order_scope(self.runtime, self.orders)
        if self.command.action == OrderAction.CANCEL_ALL_ORDERS:
            if self.replacement_submission is not None:
                raise ValueError("cancel-all must not declare replacement submission")
            return self
        matches = [
            item
            for item in self.orders
            if item.order_id == self.command.order_id
            and item.order_revision == self.command.order_revision
        ]
        if len(matches) != 1:
            raise ValueError("order command requires one exact runtime order evidence record")
        if self.command.action == OrderAction.REPLACE_ORDER:
            if self.replacement_submission is None:
                raise ValueError("replace-order requires risk-approved PI-08 replacement submission")
            _validate_replacement(self, matches[0])
        elif self.replacement_submission is not None:
            raise ValueError("cancel-order must not declare replacement submission")
        return self


class PolicyEntryActivationRequest(ContractModel):
    source: PolicyEntrySource
    policy_ref: NonEmptyStr
    evidence_ref: NonEmptyStr
    submission: PrivateDryRunSubmission


class CommandActivationResult(ContractModel):
    outcome: CommandOutcome
    activation_state: CommandActivationState
    execution_attempt_ref: NonEmptyStr | None = None
    acknowledgement: RuntimeCommandAcknowledgement | None = None
    reason_code: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.activation_state == CommandActivationState.NOT_SUBMITTED:
            if self.execution_attempt_ref is not None or self.acknowledgement is not None:
                raise ValueError("not-submitted result cannot have execution evidence")
        else:
            if self.execution_attempt_ref is None:
                raise ValueError("activated result requires execution attempt reference")
        if self.activation_state == CommandActivationState.ACKNOWLEDGED:
            if self.acknowledgement is None:
                raise ValueError("acknowledged result requires acknowledgement evidence")
        return self


def _validate_common(
    context: BotCommandContext,
    tenant_id: str,
    runtime: AuthoritativeBotRuntimeState,
) -> None:
    if tenant_id != context.tenant_id or runtime.tenant_id != context.tenant_id:
        raise ValueError("command activation tenant mismatch")


def _validate_position_scope(
    runtime: AuthoritativeBotRuntimeState,
    positions: tuple[RuntimePositionEvidence, ...],
) -> None:
    identities = set()
    for position in positions:
        if (
            position.tenant_id != runtime.tenant_id
            or position.bot_id != runtime.bot_id
            or position.runtime_id != runtime.runtime_id
        ):
            raise ValueError("position evidence scope mismatch")
        identity = (position.position_id, position.position_revision)
        if identity in identities:
            raise ValueError("duplicate position evidence")
        identities.add(identity)


def _validate_order_scope(
    runtime: AuthoritativeBotRuntimeState,
    orders: tuple[RuntimeOrderEvidence, ...],
) -> None:
    identities = set()
    for order in orders:
        if (
            order.tenant_id != runtime.tenant_id
            or order.bot_id != runtime.bot_id
            or order.runtime_id != runtime.runtime_id
        ):
            raise ValueError("order evidence scope mismatch")
        identity = (order.order_id, order.order_revision)
        if identity in identities:
            raise ValueError("duplicate order evidence")
        identities.add(identity)


def _validate_replacement(
    request: OrderCommandActivationRequest,
    current: RuntimeOrderEvidence,
) -> None:
    replacement = request.replacement_submission
    if replacement is None:
        raise ValueError("replacement submission is missing")
    binding = replacement.binding
    command = request.command
    if (
        binding.tenant_id != command.tenant_id
        or binding.bot_id != command.target.bot_id
        or binding.config_revision != command.target.config_revision
        or binding.runtime_id != command.target.runtime_id
        or binding.runtime_revision != command.target.runtime_revision
    ):
        raise ValueError("replacement PI-08 submission binding mismatch")
    intent = replacement.intent.trade_intent
    if intent.pair != current.pair or intent.side != current.side:
        raise ValueError("replacement PI-08 intent market identity mismatch")
    if command.replacement_quantity is not None:
        if intent.amount != command.replacement_quantity:
            raise ValueError("replacement intent amount must match replacement quantity")
    if command.replacement_price is not None:
        raise ValueError("price-changing replace is unsupported without native runtime replace")
