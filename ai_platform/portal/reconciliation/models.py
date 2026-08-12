from __future__ import annotations

from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import NonNegativeInt, PositiveInt, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex, UtcDateTime


class CommandState(StrEnum):
    RECEIVED = "received"
    VALIDATED = "validated"
    RESERVED = "reserved"
    DISPATCHED_PENDING_EXTERNAL = "dispatched_pending_external"
    ACKNOWLEDGED_BUT_UNRECONCILED = "acknowledged_but_unreconciled"
    RECONCILED_SUCCESS = "reconciled_success"
    RECONCILED_REJECTED = "reconciled_rejected"
    FAILED_TERMINAL = "failed_terminal"
    DEAD_LETTER = "dead_letter"
    POISONED = "poisoned"


TERMINAL_STATES = frozenset(
    {
        CommandState.RECONCILED_SUCCESS,
        CommandState.RECONCILED_REJECTED,
        CommandState.FAILED_TERMINAL,
        CommandState.DEAD_LETTER,
        CommandState.POISONED,
    }
)


class TerminalReasonCode(StrEnum):
    CONFLICTING_REPLAY = "conflicting_replay"
    STALE_GENERATION = "stale_generation"
    STALE_STATE_VERSION = "stale_state_version"
    STALE_SAFETY_EPOCH = "stale_safety_epoch"
    EXTERNAL_REJECTED = "external_rejected"
    RETRIES_EXHAUSTED = "retries_exhausted"
    CONFLICTING_OBSERVED_EVIDENCE = "conflicting_observed_evidence"
    INVALID_TRANSITION = "invalid_transition"


class ObservationOutcome(StrEnum):
    APPLIED = "applied"
    EXACT_DUPLICATE = "exact_duplicate"
    OUT_OF_ORDER_IGNORED = "out_of_order_ignored"


class CommandEnvelope(ContractModel):
    command_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    generation_id: NonEmptyStr
    expected_state_version: NonNegativeInt
    execution_safety_epoch: NonNegativeInt
    correlation_id: UUID
    causation_id: UUID | None = None
    canonical_payload_hash: Sha256Hex
    received_at: UtcDateTime


class RetryState(ContractModel):
    attempt: NonNegativeInt = 0
    max_attempts: PositiveInt = 3
    last_attempt_id: NonEmptyStr | None = None
    next_attempt_at: UtcDateTime | None = None
    last_error_code: NonEmptyStr | None = None


class TransitionEvidence(ContractModel):
    sequence: PositiveInt
    state: CommandState
    recorded_at: UtcDateTime
    reason_code: TerminalReasonCode | None = None
    evidence_hash: Sha256Hex | None = None


class ObservationEvidence(ContractModel):
    command_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    generation_id: NonEmptyStr
    source_sequence: NonNegativeInt | None = None
    source_version: NonEmptyStr | None = None
    reconciliation_epoch: NonNegativeInt
    canonical_payload_hash: Sha256Hex
    execution_succeeded: bool
    rejection_reason: NonEmptyStr | None = None
    observed_at: UtcDateTime

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.execution_succeeded and self.rejection_reason is not None:
            raise ValueError("successful evidence cannot include a rejection reason")
        if not self.execution_succeeded and self.rejection_reason is None:
            raise ValueError("rejected evidence requires a rejection reason")
        return self


class ReconciliationRecord(ContractModel):
    envelope: CommandEnvelope
    state: CommandState
    reconciliation_epoch: NonNegativeInt = 0
    last_source_sequence: NonNegativeInt | None = None
    last_source_version: NonEmptyStr | None = None
    last_observation_hash: Sha256Hex | None = None
    observed_hashes: tuple[Sha256Hex, ...] = ()
    retry: RetryState = RetryState()
    terminal_reason_code: TerminalReasonCode | None = None
    terminal_detail: NonEmptyStr | None = None
    transport_ack_hash: Sha256Hex | None = None
    transitions: tuple[TransitionEvidence, ...]

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if not self.transitions:
            raise ValueError("reconciliation record requires transition evidence")
        if self.transitions[-1].state != self.state:
            raise ValueError("last transition must match record state")
        sequences = [item.sequence for item in self.transitions]
        if sequences != list(range(1, len(sequences) + 1)):
            raise ValueError("transition sequences must be contiguous")
        if len(self.observed_hashes) != len(set(self.observed_hashes)):
            raise ValueError("observed evidence hashes must be unique")
        if (
            self.state in TERMINAL_STATES
            and self.state != CommandState.RECONCILED_SUCCESS
            and self.terminal_reason_code is None
        ):
            raise ValueError("non-success terminal states require a reason code")
        if self.state == CommandState.RECONCILED_SUCCESS and self.terminal_reason_code is not None:
            raise ValueError("reconciled success cannot have a terminal reason")
        return self

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES
