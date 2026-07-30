from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from strategy_engine.timing.closed_bar_scheduler import (
    ClosedBarError,
    ClosedBarErrorCode,
    ClosedBarObservation,
    ClosedBarScheduler,
)

OPEN = datetime(2026, 7, 30, 10, 0, tzinfo=UTC)
DURATIONS = {"5m": timedelta(minutes=5), "1h": timedelta(hours=1)}
DELAYS = {"1h": timedelta(seconds=30)}


def _observation(
    *,
    source_event_id: str = "bar:btc:5m:1000",
    timeframe: str = "5m",
    event_time: datetime = OPEN,
    detected_at: datetime | None = None,
    decision_time: datetime | None = None,
    is_closed: bool = True,
) -> ClosedBarObservation:
    duration = DURATIONS.get(timeframe, timedelta(minutes=5))
    close_time = event_time + duration
    return ClosedBarObservation(
        source_event_id=source_event_id,
        symbol="BTC/USDT",
        timeframe=timeframe,
        event_time=event_time,
        detected_at=detected_at or close_time,
        decision_time=decision_time or close_time,
        is_closed=is_closed,
    )


def _scheduler() -> ClosedBarScheduler:
    return ClosedBarScheduler(
        timeframe_durations=DURATIONS,
        confirmation_delays=DELAYS,
    )


def _assert_error(code: ClosedBarErrorCode, observation: ClosedBarObservation) -> None:
    with pytest.raises(ClosedBarError) as captured:
        _scheduler().ingest(observation)
    assert captured.value.code is code


def test_base_bar_is_available_at_exact_close_boundary() -> None:
    scheduled = _scheduler().ingest(_observation())
    assert scheduled.close_time == OPEN + timedelta(minutes=5)
    assert scheduled.confirmation_time == scheduled.close_time
    assert scheduled.available_at == scheduled.close_time


def test_higher_timeframe_waits_for_confirmation_boundary() -> None:
    close_time = OPEN + timedelta(hours=1)
    before_confirmation = _observation(
        source_event_id="bar:btc:1h:1000",
        timeframe="1h",
        detected_at=close_time,
        decision_time=close_time + timedelta(seconds=29),
    )
    _assert_error(ClosedBarErrorCode.AVAILABLE_AFTER_DECISION, before_confirmation)

    at_confirmation = _observation(
        source_event_id="bar:btc:1h:1000",
        timeframe="1h",
        detected_at=close_time,
        decision_time=close_time + timedelta(seconds=30),
    )
    scheduled = _scheduler().ingest(at_confirmation)
    assert scheduled.available_at == close_time + timedelta(seconds=30)


def test_explicitly_unconfirmed_bar_fails_closed() -> None:
    _assert_error(ClosedBarErrorCode.UNCONFIRMED_BAR, _observation(is_closed=False))


def test_bar_cannot_claim_closed_before_close_time() -> None:
    _assert_error(
        ClosedBarErrorCode.UNCONFIRMED_BAR,
        _observation(
            detected_at=OPEN + timedelta(minutes=4, seconds=59),
            decision_time=OPEN + timedelta(minutes=5),
        ),
    )


def test_naive_and_non_utc_timestamps_fail_closed() -> None:
    _assert_error(
        ClosedBarErrorCode.NAIVE_TIMESTAMP,
        _observation(event_time=OPEN.replace(tzinfo=None)),
    )
    plus_two = timezone(timedelta(hours=2))
    non_utc = OPEN.astimezone(plus_two)
    _assert_error(
        ClosedBarErrorCode.NON_UTC_TIMESTAMP,
        _observation(event_time=non_utc),
    )


def test_late_bar_uses_actual_detection_as_availability() -> None:
    detected_at = OPEN + timedelta(minutes=7)
    scheduled = _scheduler().ingest(
        _observation(detected_at=detected_at, decision_time=detected_at)
    )
    assert scheduled.close_time == OPEN + timedelta(minutes=5)
    assert scheduled.available_at == detected_at


def test_duplicate_is_idempotent_and_conflicting_duplicate_is_rejected() -> None:
    scheduler = _scheduler()
    first = scheduler.ingest(_observation())
    duplicate = scheduler.ingest(
        _observation(
            detected_at=OPEN + timedelta(minutes=6),
            decision_time=OPEN + timedelta(minutes=6),
        )
    )
    assert duplicate is first
    assert scheduler.records == (first,)

    with pytest.raises(ClosedBarError) as captured:
        scheduler.ingest(_observation(source_event_id="bar:conflict"))
    assert captured.value.code is ClosedBarErrorCode.CONFLICTING_DUPLICATE
    assert scheduler.records == (first,)


def test_out_of_order_bar_cannot_rewrite_emitted_history() -> None:
    scheduler = _scheduler()
    later_open = OPEN + timedelta(minutes=5)
    first = scheduler.ingest(
        _observation(
            source_event_id="bar:btc:5m:1005",
            event_time=later_open,
        )
    )
    with pytest.raises(ClosedBarError) as captured:
        scheduler.ingest(_observation())
    assert captured.value.code is ClosedBarErrorCode.OUT_OF_ORDER_BAR
    assert scheduler.records == (first,)


def test_unknown_timeframe_and_invalid_configuration_fail_closed() -> None:
    _assert_error(
        ClosedBarErrorCode.UNKNOWN_TIMEFRAME,
        _observation(timeframe="15m"),
    )
    with pytest.raises(ClosedBarError) as captured:
        ClosedBarScheduler(timeframe_durations={})
    assert captured.value.code is ClosedBarErrorCode.INVALID_CONFIGURATION
