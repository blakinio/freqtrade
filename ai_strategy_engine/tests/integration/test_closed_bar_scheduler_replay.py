from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from strategy_engine.timing.closed_bar_scheduler import (
    ClosedBarError,
    ClosedBarErrorCode,
    ClosedBarObservation,
    ClosedBarScheduler,
    canonical_schedule_sha256,
    replay_closed_bars,
)

START = datetime(2026, 7, 30, 8, 0, tzinfo=UTC)
DURATIONS = {"5m": timedelta(minutes=5), "1h": timedelta(hours=1)}
DELAYS = {"1h": timedelta(seconds=30)}


def _bar(
    source_event_id: str,
    timeframe: str,
    event_time: datetime,
    *,
    detected_at: datetime,
    decision_time: datetime,
) -> ClosedBarObservation:
    return ClosedBarObservation(
        source_event_id=source_event_id,
        symbol="BTC/USDT",
        timeframe=timeframe,
        event_time=event_time,
        detected_at=detected_at,
        decision_time=decision_time,
        is_closed=True,
    )


def _manifest() -> tuple[ClosedBarObservation, ...]:
    return (
        _bar(
            "bar:btc:5m:0800",
            "5m",
            START,
            detected_at=START + timedelta(minutes=5),
            decision_time=START + timedelta(minutes=5),
        ),
        _bar(
            "bar:btc:5m:0805",
            "5m",
            START + timedelta(minutes=5),
            detected_at=START + timedelta(minutes=12),
            decision_time=START + timedelta(minutes=12),
        ),
        _bar(
            "bar:btc:1h:0800",
            "1h",
            START,
            detected_at=START + timedelta(hours=1),
            decision_time=START + timedelta(hours=1, seconds=30),
        ),
    )


def test_identical_manifests_produce_identical_schedule_and_hash() -> None:
    first = replay_closed_bars(
        _manifest(),
        timeframe_durations=DURATIONS,
        confirmation_delays=DELAYS,
    )
    second = replay_closed_bars(
        _manifest(),
        timeframe_durations=DURATIONS,
        confirmation_delays=DELAYS,
    )
    assert second == first
    assert canonical_schedule_sha256(second) == canonical_schedule_sha256(first)


def test_future_append_preserves_the_historical_prefix() -> None:
    scheduler = ClosedBarScheduler(
        timeframe_durations=DURATIONS,
        confirmation_delays=DELAYS,
    )
    first_two = _manifest()[:2]
    for observation in first_two:
        scheduler.ingest(observation)
    historical = scheduler.records
    historical_hash = scheduler.canonical_sha256

    future_open = START + timedelta(minutes=10)
    scheduler.ingest(
        _bar(
            "bar:btc:5m:0810",
            "5m",
            future_open,
            detected_at=future_open + timedelta(minutes=5),
            decision_time=future_open + timedelta(minutes=5),
        )
    )

    assert scheduler.records[: len(historical)] == historical
    assert canonical_schedule_sha256(scheduler.records[: len(historical)]) == historical_hash


def test_duplicate_replay_does_not_change_history_or_hash() -> None:
    scheduler = ClosedBarScheduler(timeframe_durations=DURATIONS)
    observation = _manifest()[0]
    scheduler.ingest(observation)
    history = scheduler.records
    history_hash = scheduler.canonical_sha256

    scheduler.ingest(
        ClosedBarObservation(
            source_event_id=observation.source_event_id,
            symbol=observation.symbol,
            timeframe=observation.timeframe,
            event_time=observation.event_time,
            detected_at=observation.detected_at + timedelta(minutes=1),
            decision_time=observation.decision_time + timedelta(minutes=1),
            is_closed=True,
        )
    )
    assert scheduler.records == history
    assert scheduler.canonical_sha256 == history_hash


def test_late_out_of_order_replay_fails_without_mutating_history() -> None:
    scheduler = ClosedBarScheduler(timeframe_durations=DURATIONS)
    later = _manifest()[1]
    scheduler.ingest(later)
    history = scheduler.records
    history_hash = scheduler.canonical_sha256

    with pytest.raises(ClosedBarError) as captured:
        scheduler.ingest(_manifest()[0])
    assert captured.value.code is ClosedBarErrorCode.OUT_OF_ORDER_BAR
    assert scheduler.records == history
    assert scheduler.canonical_sha256 == history_hash
