from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ai_platform.portal.reconciliation.engine import (
    ConflictingReplayError,
    InvalidTransitionError,
    ReconciliationEngine,
)
from ai_platform.portal.reconciliation.models import (
    CommandEnvelope,
    CommandState,
    ObservationEvidence,
    ObservationOutcome,
    TerminalReasonCode,
)
from ai_platform.portal.reconciliation.ports import ConcurrentWriteError
from ai_platform.portal.reconciliation.store import InMemorySnapshotStore


NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def envelope(
    *,
    command_id: str = "command-1",
    tenant_id: str = "tenant-a",
    generation_id: str = "generation-7",
    payload_hash: str = HASH_A,
) -> CommandEnvelope:
    return CommandEnvelope(
        command_id=command_id,
        tenant_id=tenant_id,
        bot_id="bot-1",
        generation_id=generation_id,
        expected_state_version=5,
        execution_safety_epoch=3,
        correlation_id=UUID("10000000-0000-0000-0000-000000000001"),
        causation_id=UUID("20000000-0000-0000-0000-000000000002"),
        canonical_payload_hash=payload_hash,
        received_at=NOW,
    )


def observation(
    *,
    payload_hash: str = HASH_B,
    sequence: int = 10,
    epoch: int = 2,
    succeeded: bool = True,
    tenant_id: str = "tenant-a",
    generation_id: str = "generation-7",
) -> ObservationEvidence:
    return ObservationEvidence(
        command_id="command-1",
        tenant_id=tenant_id,
        bot_id="bot-1",
        generation_id=generation_id,
        source_sequence=sequence,
        source_version=f"source-{sequence}",
        reconciliation_epoch=epoch,
        canonical_payload_hash=payload_hash,
        execution_succeeded=succeeded,
        rejection_reason=None if succeeded else "runtime_rejected",
        observed_at=NOW + timedelta(seconds=sequence),
    )


def advance_to_dispatched(engine: ReconciliationEngine) -> None:
    engine.receive(envelope())
    engine.validate(
        "tenant-a",
        "command-1",
        current_generation_id="generation-7",
        current_state_version=5,
        current_safety_epoch=3,
        recorded_at=NOW + timedelta(seconds=1),
    )
    engine.reserve("tenant-a", "command-1", NOW + timedelta(seconds=2))
    engine.dispatch("tenant-a", "command-1", NOW + timedelta(seconds=3))


def test_exact_replay_is_stable_and_conflicting_replay_fails_closed() -> None:
    store = InMemorySnapshotStore()
    engine = ReconciliationEngine(store)

    first = engine.receive(envelope())
    replay = engine.receive(envelope())

    assert replay == first
    assert len(replay.transitions) == 1
    with pytest.raises(ConflictingReplayError):
        engine.receive(envelope(payload_hash=HASH_C))


@pytest.mark.parametrize(
    ("generation", "state_version", "safety_epoch", "reason"),
    [
        ("generation-old", 5, 3, TerminalReasonCode.STALE_GENERATION),
        ("generation-7", 4, 3, TerminalReasonCode.STALE_STATE_VERSION),
        ("generation-7", 5, 2, TerminalReasonCode.STALE_SAFETY_EPOCH),
    ],
)
def test_stale_identity_version_and_fence_are_terminal(
    generation: str,
    state_version: int,
    safety_epoch: int,
    reason: TerminalReasonCode,
) -> None:
    engine = ReconciliationEngine(InMemorySnapshotStore())
    engine.receive(envelope())

    record = engine.validate(
        "tenant-a",
        "command-1",
        current_generation_id=generation,
        current_state_version=state_version,
        current_safety_epoch=safety_epoch,
        recorded_at=NOW + timedelta(seconds=1),
    )

    assert record.state == CommandState.FAILED_TERMINAL
    assert record.terminal_reason_code == reason


def test_transport_ack_never_becomes_execution_success() -> None:
    engine = ReconciliationEngine(InMemorySnapshotStore())
    advance_to_dispatched(engine)

    record = engine.acknowledge("tenant-a", "command-1", HASH_C, NOW + timedelta(seconds=4))

    assert record.state == CommandState.ACKNOWLEDGED_BUT_UNRECONCILED
    assert not record.is_terminal
    assert record.transport_ack_hash == HASH_C


def test_authoritative_observation_completes_and_exact_duplicate_is_noop() -> None:
    engine = ReconciliationEngine(InMemorySnapshotStore())
    advance_to_dispatched(engine)
    engine.acknowledge("tenant-a", "command-1", HASH_C, NOW + timedelta(seconds=4))

    completed, outcome = engine.observe(observation())
    duplicate, duplicate_outcome = engine.observe(observation())

    assert outcome == ObservationOutcome.APPLIED
    assert completed.state == CommandState.RECONCILED_SUCCESS
    assert duplicate_outcome == ObservationOutcome.EXACT_DUPLICATE
    assert duplicate == completed


def test_out_of_order_evidence_is_ignored_before_newer_terminal_evidence() -> None:
    engine = ReconciliationEngine(InMemorySnapshotStore())
    advance_to_dispatched(engine)
    current, _ = engine._required("tenant-a", "command-1")
    seeded = current.model_copy(
        update={
            "reconciliation_epoch": 3,
            "last_source_sequence": 20,
            "last_observation_hash": HASH_C,
            "observed_hashes": (HASH_C,),
        }
    )
    _, version = engine._required("tenant-a", "command-1")
    engine._store.compare_and_swap(seeded, version)

    unchanged, outcome = engine.observe(observation(sequence=19, epoch=3))

    assert outcome == ObservationOutcome.OUT_OF_ORDER_IGNORED
    assert unchanged.state == CommandState.DISPATCHED_PENDING_EXTERNAL
    assert unchanged.observed_hashes == (HASH_C,)


def test_same_order_conflict_is_poisoned_without_blocking_other_tenant() -> None:
    store = InMemorySnapshotStore()
    engine = ReconciliationEngine(store)
    advance_to_dispatched(engine)
    current, version = engine._required("tenant-a", "command-1")
    seeded = current.model_copy(
        update={
            "reconciliation_epoch": 2,
            "last_source_sequence": 10,
            "last_observation_hash": HASH_C,
            "observed_hashes": (HASH_C,),
        }
    )
    store.compare_and_swap(seeded, version)
    engine.receive(envelope(command_id="command-2", tenant_id="tenant-b"))

    poisoned, _ = engine.observe(observation(payload_hash=HASH_B))

    assert poisoned.state == CommandState.POISONED
    assert poisoned.terminal_reason_code == TerminalReasonCode.CONFLICTING_OBSERVED_EVIDENCE
    assert [item.envelope.tenant_id for item in engine.recoverable()] == ["tenant-b"]


def test_rejected_observation_is_terminal_but_not_success() -> None:
    engine = ReconciliationEngine(InMemorySnapshotStore())
    advance_to_dispatched(engine)

    record, _ = engine.observe(observation(succeeded=False))

    assert record.state == CommandState.RECONCILED_REJECTED
    assert record.terminal_reason_code == TerminalReasonCode.EXTERNAL_REJECTED
    assert record.terminal_detail == "runtime_rejected"


def test_retry_backoff_is_deterministic_and_exhaustion_dead_letters() -> None:
    engine = ReconciliationEngine(InMemorySnapshotStore())
    engine.receive(envelope(), max_attempts=3)

    first = engine.record_retry(
        "tenant-a",
        "command-1",
        attempt_id="attempt-1",
        error_code="gateway_unavailable",
        recorded_at=NOW,
        base_delay=timedelta(seconds=5),
    )
    second = engine.record_retry(
        "tenant-a",
        "command-1",
        attempt_id="attempt-2",
        error_code="gateway_unavailable",
        recorded_at=NOW,
        base_delay=timedelta(seconds=5),
    )
    terminal = engine.record_retry(
        "tenant-a",
        "command-1",
        attempt_id="attempt-3",
        error_code="gateway_unavailable",
        recorded_at=NOW,
        base_delay=timedelta(seconds=5),
    )

    assert first.retry.next_attempt_at == NOW + timedelta(seconds=5)
    assert second.retry.next_attempt_at == NOW + timedelta(seconds=10)
    assert terminal.state == CommandState.DEAD_LETTER
    assert terminal.retry.attempt == 3
    assert terminal.terminal_reason_code == TerminalReasonCode.RETRIES_EXHAUSTED


def test_restart_snapshot_is_canonical_and_recovers_nonterminal_work() -> None:
    store = InMemorySnapshotStore()
    engine = ReconciliationEngine(store)
    advance_to_dispatched(engine)
    serialized = store.export_json()

    restarted_store = InMemorySnapshotStore.from_json(serialized)
    restarted = ReconciliationEngine(restarted_store)

    assert restarted_store.export_json() == serialized
    assert [item.envelope.command_id for item in restarted.recoverable()] == ["command-1"]
    record = restarted.acknowledge(
        "tenant-a", "command-1", HASH_C, NOW + timedelta(seconds=4)
    )
    assert record.state == CommandState.ACKNOWLEDGED_BUT_UNRECONCILED


def test_replayed_transition_and_retry_attempt_are_idempotent_after_restart() -> None:
    store = InMemorySnapshotStore()
    engine = ReconciliationEngine(store)
    engine.receive(envelope())
    engine.validate(
        "tenant-a",
        "command-1",
        current_generation_id="generation-7",
        current_state_version=5,
        current_safety_epoch=3,
        recorded_at=NOW + timedelta(seconds=1),
    )
    first_reservation = engine.reserve("tenant-a", "command-1", NOW + timedelta(seconds=2))
    replayed_reservation = engine.reserve(
        "tenant-a", "command-1", NOW + timedelta(seconds=20)
    )
    first_retry = engine.record_retry(
        "tenant-a",
        "command-1",
        attempt_id="retry-attempt-1",
        error_code="dispatch_timeout",
        recorded_at=NOW,
        base_delay=timedelta(seconds=5),
    )
    replayed_retry = engine.record_retry(
        "tenant-a",
        "command-1",
        attempt_id="retry-attempt-1",
        error_code="dispatch_timeout",
        recorded_at=NOW + timedelta(minutes=1),
        base_delay=timedelta(seconds=5),
    )

    assert replayed_reservation == first_reservation
    assert replayed_retry == first_retry
    assert replayed_retry.retry.attempt == 1


def test_compare_and_swap_rejects_concurrent_stale_writer() -> None:
    store = InMemorySnapshotStore()
    engine = ReconciliationEngine(store)
    engine.receive(envelope())
    record, version = store.load("tenant-a", "command-1") or pytest.fail("missing record")
    engine.validate(
        "tenant-a",
        "command-1",
        current_generation_id="generation-7",
        current_state_version=5,
        current_safety_epoch=3,
        recorded_at=NOW + timedelta(seconds=1),
    )

    with pytest.raises(ConcurrentWriteError):
        store.compare_and_swap(record, version)


def test_concurrent_exact_receive_converges_to_existing_record() -> None:
    class RacingStore(InMemorySnapshotStore):
        def __init__(self) -> None:
            super().__init__()
            self.inject_race = True

        def create(self, record):  # type: ignore[no-untyped-def]
            if self.inject_race:
                self.inject_race = False
                super().create(record)
            super().create(record)

    engine = ReconciliationEngine(RacingStore())

    record = engine.receive(envelope())

    assert record.envelope == envelope()
    assert len(record.transitions) == 1


def test_terminal_state_rejects_retry_and_late_novel_evidence() -> None:
    engine = ReconciliationEngine(InMemorySnapshotStore())
    advance_to_dispatched(engine)
    engine.observe(observation())

    with pytest.raises(InvalidTransitionError):
        engine.record_retry(
            "tenant-a",
            "command-1",
            attempt_id="late-attempt",
            error_code="late",
            recorded_at=NOW,
            base_delay=timedelta(seconds=1),
        )
    with pytest.raises(InvalidTransitionError):
        engine.observe(observation(payload_hash=HASH_C, sequence=11))
