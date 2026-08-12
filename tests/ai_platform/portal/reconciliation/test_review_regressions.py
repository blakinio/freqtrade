from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ai_platform.portal.reconciliation.engine import InvalidTransitionError, ReconciliationEngine
from ai_platform.portal.reconciliation.models import (
    CommandEnvelope,
    CommandState,
    ObservationEvidence,
    ObservationOutcome,
    TerminalReasonCode,
)
from ai_platform.portal.reconciliation.store import InMemorySnapshotStore


NOW = datetime(2026, 8, 12, 12, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def envelope() -> CommandEnvelope:
    return CommandEnvelope(
        command_id="command-1",
        tenant_id="tenant-a",
        bot_id="bot-1",
        generation_id="generation-7",
        expected_state_version=5,
        execution_safety_epoch=3,
        correlation_id=UUID("10000000-0000-0000-0000-000000000001"),
        canonical_payload_hash=HASH_A,
        received_at=NOW,
    )


def observation(
    *,
    payload_hash: str = HASH_B,
    sequence: int = 10,
    version: str | None = None,
    epoch: int = 2,
    generation_id: str = "generation-7",
) -> ObservationEvidence:
    return ObservationEvidence(
        command_id="command-1",
        tenant_id="tenant-a",
        bot_id="bot-1",
        generation_id=generation_id,
        source_sequence=sequence,
        source_version=version or f"source-{sequence}",
        reconciliation_epoch=epoch,
        canonical_payload_hash=payload_hash,
        execution_succeeded=True,
        observed_at=NOW + timedelta(seconds=sequence),
    )


def reserved() -> ReconciliationEngine:
    engine = ReconciliationEngine(InMemorySnapshotStore())
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
    return engine


def dispatched() -> ReconciliationEngine:
    engine = reserved()
    engine.dispatch(
        "tenant-a",
        "command-1",
        NOW + timedelta(seconds=3),
        current_generation_id="generation-7",
        current_state_version=5,
        current_safety_epoch=3,
    )
    return engine


@pytest.mark.parametrize(
    ("generation", "state_version", "safety_epoch", "reason"),
    [
        ("generation-8", 5, 3, TerminalReasonCode.STALE_GENERATION),
        ("generation-7", 6, 3, TerminalReasonCode.STALE_STATE_VERSION),
        ("generation-7", 5, 4, TerminalReasonCode.STALE_SAFETY_EPOCH),
    ],
)
def test_dispatch_revalidates_current_fence_atomically(
    generation: str,
    state_version: int,
    safety_epoch: int,
    reason: TerminalReasonCode,
) -> None:
    engine = reserved()
    result = engine.dispatch(
        "tenant-a",
        "command-1",
        NOW + timedelta(seconds=3),
        current_generation_id=generation,
        current_state_version=state_version,
        current_safety_epoch=safety_epoch,
    )
    assert result.state == CommandState.FAILED_TERMINAL
    assert result.terminal_reason_code == reason


def test_terminal_success_cannot_be_replaced_by_misrouted_poison_evidence() -> None:
    engine = dispatched()
    terminal, _ = engine.observe(observation())
    assert terminal.state == CommandState.RECONCILED_SUCCESS

    with pytest.raises(InvalidTransitionError):
        engine.observe(
            observation(
                payload_hash=HASH_C,
                sequence=11,
                generation_id="generation-other",
            )
        )
    persisted, _ = engine._required("tenant-a", "command-1")
    assert persisted.state == CommandState.RECONCILED_SUCCESS


def test_source_sequence_precedes_local_reconciliation_epoch() -> None:
    engine = dispatched()
    record, version = engine._required("tenant-a", "command-1")
    seeded = record.model_copy(
        update={
            "last_source_sequence": 20,
            "last_source_version": "source-20",
            "reconciliation_epoch": 1,
            "last_observation_hash": HASH_C,
            "observed_hashes": (HASH_C,),
        }
    )
    engine._store.compare_and_swap(seeded, version)

    unchanged, outcome = engine.observe(
        observation(payload_hash=HASH_B, sequence=19, epoch=999)
    )
    assert outcome is ObservationOutcome.OUT_OF_ORDER_IGNORED
    assert unchanged.state == CommandState.DISPATCHED_PENDING_EXTERNAL


def test_retry_identity_history_survives_nonconsecutive_replay_and_restart() -> None:
    store = InMemorySnapshotStore()
    engine = ReconciliationEngine(store)
    engine.receive(envelope(), max_attempts=4)
    engine.record_retry(
        "tenant-a",
        "command-1",
        attempt_id="attempt-1",
        error_code="timeout",
        recorded_at=NOW,
        base_delay=timedelta(seconds=1),
    )
    second = engine.record_retry(
        "tenant-a",
        "command-1",
        attempt_id="attempt-2",
        error_code="timeout",
        recorded_at=NOW + timedelta(seconds=1),
        base_delay=timedelta(seconds=1),
    )
    restarted = ReconciliationEngine(InMemorySnapshotStore.from_json(store.export_json()))
    replay = restarted.record_retry(
        "tenant-a",
        "command-1",
        attempt_id="attempt-1",
        error_code="timeout",
        recorded_at=NOW + timedelta(minutes=1),
        base_delay=timedelta(seconds=1),
    )
    assert replay.retry.attempt == 2
    assert replay.retry.attempted_ids == second.retry.attempted_ids


def test_late_transport_ack_after_authoritative_success_is_noop() -> None:
    engine = dispatched()
    terminal, _ = engine.observe(observation())
    late = engine.acknowledge(
        "tenant-a",
        "command-1",
        HASH_C,
        NOW + timedelta(seconds=30),
    )
    assert late == terminal
    assert late.state == CommandState.RECONCILED_SUCCESS
