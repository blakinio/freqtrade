from __future__ import annotations

from datetime import datetime, timedelta

from ai_platform.portal.reconciliation.models import (
    CommandEnvelope,
    CommandState,
    ObservationEvidence,
    ObservationOutcome,
    ReconciliationRecord,
    RetryState,
    TerminalReasonCode,
    TransitionEvidence,
)
from ai_platform.portal.reconciliation.ports import (
    ReconciliationStore,
    RecordAlreadyExistsError,
)


class ReconciliationError(RuntimeError):
    pass


class ConflictingReplayError(ReconciliationError):
    pass


class InvalidTransitionError(ReconciliationError):
    pass


class ReconciliationEngine:
    def __init__(self, store: ReconciliationStore) -> None:
        self._store = store

    def receive(self, envelope: CommandEnvelope, *, max_attempts: int = 3) -> ReconciliationRecord:
        loaded = self._store.load(envelope.tenant_id, envelope.command_id)
        if loaded is not None:
            existing, _ = loaded
            if existing.envelope == envelope:
                return existing
            raise ConflictingReplayError(
                "command identity was replayed with different canonical data"
            )
        transition = TransitionEvidence(
            sequence=1,
            state=CommandState.RECEIVED,
            recorded_at=envelope.received_at,
        )
        record = ReconciliationRecord(
            envelope=envelope,
            state=CommandState.RECEIVED,
            retry=RetryState(max_attempts=max_attempts),
            transitions=(transition,),
        )
        try:
            self._store.create(record)
            return record
        except RecordAlreadyExistsError:
            raced, _ = self._required(envelope.tenant_id, envelope.command_id)
            if raced.envelope == envelope:
                return raced
            raise ConflictingReplayError(
                "command identity was concurrently reserved with different canonical data"
            ) from None

    def validate(
        self,
        tenant_id: str,
        command_id: str,
        *,
        current_generation_id: str,
        current_state_version: int,
        current_safety_epoch: int,
        recorded_at: datetime,
    ) -> ReconciliationRecord:
        record, version = self._required(tenant_id, command_id)
        if record.state == CommandState.VALIDATED or record.is_terminal:
            return record
        self._require_state(record, CommandState.RECEIVED)
        reason = self._fence_reason(
            record,
            current_generation_id=current_generation_id,
            current_state_version=current_state_version,
            current_safety_epoch=current_safety_epoch,
        )
        state = CommandState.FAILED_TERMINAL if reason is not None else CommandState.VALIDATED
        return self._persist(self._transition(record, state, recorded_at, reason=reason), version)

    def reserve(
        self, tenant_id: str, command_id: str, recorded_at: datetime
    ) -> ReconciliationRecord:
        return self._simple_transition(
            tenant_id,
            command_id,
            CommandState.VALIDATED,
            CommandState.RESERVED,
            recorded_at,
        )

    def dispatch(
        self,
        tenant_id: str,
        command_id: str,
        recorded_at: datetime,
        *,
        current_generation_id: str,
        current_state_version: int,
        current_safety_epoch: int,
    ) -> ReconciliationRecord:
        """Final authority boundary: revalidate the current execution fence before dispatch."""

        record, version = self._required(tenant_id, command_id)
        if record.state == CommandState.DISPATCHED_PENDING_EXTERNAL:
            return record
        self._require_state(record, CommandState.RESERVED)
        reason = self._fence_reason(
            record,
            current_generation_id=current_generation_id,
            current_state_version=current_state_version,
            current_safety_epoch=current_safety_epoch,
        )
        if reason is not None:
            return self._persist(
                self._transition(record, CommandState.FAILED_TERMINAL, recorded_at, reason=reason),
                version,
            )
        return self._persist(
            self._transition(record, CommandState.DISPATCHED_PENDING_EXTERNAL, recorded_at),
            version,
        )

    def acknowledge(
        self,
        tenant_id: str,
        command_id: str,
        acknowledgement_hash: str,
        recorded_at: datetime,
    ) -> ReconciliationRecord:
        record, version = self._required(tenant_id, command_id)
        if record.state == CommandState.ACKNOWLEDGED_BUT_UNRECONCILED:
            if record.transport_ack_hash == acknowledgement_hash:
                return record
            raise ConflictingReplayError("transport acknowledgement hash changed")
        if record.state in {
            CommandState.RECONCILED_SUCCESS,
            CommandState.RECONCILED_REJECTED,
        }:
            if record.transport_ack_hash not in (None, acknowledgement_hash):
                raise ConflictingReplayError("transport acknowledgement hash changed")
            return record
        self._require_state(record, CommandState.DISPATCHED_PENDING_EXTERNAL)
        updated = self._transition(record, CommandState.ACKNOWLEDGED_BUT_UNRECONCILED, recorded_at)
        updated = updated.model_copy(update={"transport_ack_hash": acknowledgement_hash})
        return self._persist(updated, version)

    def observe(
        self, evidence: ObservationEvidence
    ) -> tuple[ReconciliationRecord, ObservationOutcome]:
        record, version = self._required(evidence.tenant_id, evidence.command_id)
        if evidence.canonical_payload_hash in record.observed_hashes:
            return record, ObservationOutcome.EXACT_DUPLICATE
        if record.is_terminal:
            raise InvalidTransitionError(
                "new observed evidence cannot alter terminal command state"
            )
        if (
            evidence.bot_id != record.envelope.bot_id
            or evidence.generation_id != record.envelope.generation_id
        ):
            poisoned = self._transition(
                record,
                CommandState.POISONED,
                evidence.observed_at,
                reason=TerminalReasonCode.CONFLICTING_OBSERVED_EVIDENCE,
                evidence_hash=evidence.canonical_payload_hash,
            )
            return self._persist(poisoned, version), ObservationOutcome.APPLIED
        order = self._observation_order(evidence)
        current_order = self._record_observation_order(record)
        if order < current_order:
            return record, ObservationOutcome.OUT_OF_ORDER_IGNORED
        if order == current_order and record.last_observation_hash is not None:
            poisoned = self._transition(
                record,
                CommandState.POISONED,
                evidence.observed_at,
                reason=TerminalReasonCode.CONFLICTING_OBSERVED_EVIDENCE,
                evidence_hash=evidence.canonical_payload_hash,
            )
            return self._persist(poisoned, version), ObservationOutcome.APPLIED
        state = (
            CommandState.RECONCILED_SUCCESS
            if evidence.execution_succeeded
            else CommandState.RECONCILED_REJECTED
        )
        reason = None if evidence.execution_succeeded else TerminalReasonCode.EXTERNAL_REJECTED
        updated = self._transition(
            record,
            state,
            evidence.observed_at,
            reason=reason,
            detail=evidence.rejection_reason,
            evidence_hash=evidence.canonical_payload_hash,
        ).model_copy(
            update={
                "reconciliation_epoch": evidence.reconciliation_epoch,
                "last_source_sequence": evidence.source_sequence,
                "last_source_version": evidence.source_version,
                "last_observation_hash": evidence.canonical_payload_hash,
                "observed_hashes": (*record.observed_hashes, evidence.canonical_payload_hash),
            }
        )
        return self._persist(updated, version), ObservationOutcome.APPLIED

    def record_retry(
        self,
        tenant_id: str,
        command_id: str,
        *,
        attempt_id: str,
        error_code: str,
        recorded_at: datetime,
        base_delay: timedelta,
    ) -> ReconciliationRecord:
        record, version = self._required(tenant_id, command_id)
        if record.is_terminal:
            raise InvalidTransitionError("terminal commands cannot be retried")
        if attempt_id in record.retry.attempted_ids:
            return record
        attempted_ids = (*record.retry.attempted_ids, attempt_id)
        attempt = len(attempted_ids)
        if attempt >= record.retry.max_attempts:
            updated = self._transition(
                record,
                CommandState.DEAD_LETTER,
                recorded_at,
                reason=TerminalReasonCode.RETRIES_EXHAUSTED,
                detail=error_code,
            ).model_copy(
                update={
                    "retry": RetryState(
                        attempt=attempt,
                        max_attempts=record.retry.max_attempts,
                        last_attempt_id=attempt_id,
                        attempted_ids=attempted_ids,
                        last_error_code=error_code,
                    )
                }
            )
        else:
            delay = base_delay * (2 ** (attempt - 1))
            updated = record.model_copy(
                update={
                    "retry": RetryState(
                        attempt=attempt,
                        max_attempts=record.retry.max_attempts,
                        last_attempt_id=attempt_id,
                        attempted_ids=attempted_ids,
                        next_attempt_at=recorded_at + delay,
                        last_error_code=error_code,
                    )
                }
            )
        return self._persist(updated, version)

    def recoverable(self) -> tuple[ReconciliationRecord, ...]:
        return self._store.list_nonterminal()

    def _simple_transition(
        self,
        tenant_id: str,
        command_id: str,
        expected: CommandState,
        target: CommandState,
        recorded_at: datetime,
    ) -> ReconciliationRecord:
        record, version = self._required(tenant_id, command_id)
        if record.state == target:
            return record
        self._require_state(record, expected)
        return self._persist(self._transition(record, target, recorded_at), version)

    def _required(self, tenant_id: str, command_id: str) -> tuple[ReconciliationRecord, int]:
        loaded = self._store.load(tenant_id, command_id)
        if loaded is None:
            raise KeyError((tenant_id, command_id))
        return loaded

    def _persist(self, record: ReconciliationRecord, version: int) -> ReconciliationRecord:
        self._store.compare_and_swap(record, version)
        return record

    @staticmethod
    def _require_state(record: ReconciliationRecord, expected: CommandState) -> None:
        if record.state != expected:
            raise InvalidTransitionError(f"expected {expected.value}, found {record.state.value}")

    @staticmethod
    def _fence_reason(
        record: ReconciliationRecord,
        *,
        current_generation_id: str,
        current_state_version: int,
        current_safety_epoch: int,
    ) -> TerminalReasonCode | None:
        if record.envelope.generation_id != current_generation_id:
            return TerminalReasonCode.STALE_GENERATION
        if record.envelope.expected_state_version != current_state_version:
            return TerminalReasonCode.STALE_STATE_VERSION
        if record.envelope.execution_safety_epoch != current_safety_epoch:
            return TerminalReasonCode.STALE_SAFETY_EPOCH
        return None

    @staticmethod
    def _observation_order(evidence: ObservationEvidence) -> tuple[int, str, int]:
        return (
            evidence.source_sequence if evidence.source_sequence is not None else -1,
            evidence.source_version or "",
            evidence.reconciliation_epoch,
        )

    @staticmethod
    def _record_observation_order(record: ReconciliationRecord) -> tuple[int, str, int]:
        return (
            record.last_source_sequence if record.last_source_sequence is not None else -1,
            record.last_source_version or "",
            record.reconciliation_epoch,
        )

    @staticmethod
    def _transition(
        record: ReconciliationRecord,
        state: CommandState,
        recorded_at: datetime,
        *,
        reason: TerminalReasonCode | None = None,
        detail: str | None = None,
        evidence_hash: str | None = None,
    ) -> ReconciliationRecord:
        transition = TransitionEvidence(
            sequence=len(record.transitions) + 1,
            state=state,
            recorded_at=recorded_at,
            reason_code=reason,
            evidence_hash=evidence_hash,
        )
        return record.model_copy(
            update={
                "state": state,
                "terminal_reason_code": reason,
                "terminal_detail": detail,
                "transitions": (*record.transitions, transition),
            }
        )
