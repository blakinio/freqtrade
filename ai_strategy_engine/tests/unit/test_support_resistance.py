from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pytest

from strategy_engine.features.pivots import PivotEvent, confirmed_pivots
from strategy_engine.features.support_resistance import (
    distance_bps,
    support_resistance_events,
)


def _pivot(
    kind: str,
    level: float,
    pivot_index: int,
    detected_index: int,
    *,
    start: str = "2026-01-01T00:00:00Z",
    latency_seconds: int = 1,
) -> PivotEvent:
    index = pd.date_range(start, periods=20, freq="5min", tz="UTC")
    return PivotEvent(
        kind=kind,
        level=level,
        pivot_index=pivot_index,
        detected_index=detected_index,
        event_time=index[pivot_index],
        detected_at=index[detected_index],
        available_at=index[detected_index] + timedelta(seconds=latency_seconds),
    )


def test_level_is_emitted_only_after_confirmed_touches_are_available() -> None:
    events = support_resistance_events(
        [
            _pivot("low", 100.0, 2, 4),
            _pivot("low", 100.4, 6, 8),
            _pivot("high", 110.0, 3, 5),
            _pivot("high", 109.7, 7, 9),
        ],
        min_confirmations=2,
        tolerance_bps=50.0,
    )

    support = next(event for event in events if event.kind == "support")
    resistance = next(event for event in events if event.kind == "resistance")

    assert support.level == pytest.approx(100.2, abs=1e-12)
    assert support.confirmations == 2
    assert support.source_pivot_indices == (2, 6)
    assert support.event_time == pd.Timestamp("2026-01-01T00:30:00Z")
    assert support.detected_at == pd.Timestamp("2026-01-01T00:40:00Z")
    assert support.available_at == pd.Timestamp("2026-01-01T00:40:01Z")

    assert resistance.level == pytest.approx(109.85, abs=1e-12)
    assert resistance.source_pivot_indices == (3, 7)
    assert resistance.available_at == pd.Timestamp("2026-01-01T00:45:01Z")


def test_append_only_replay_does_not_repaint_an_emitted_level() -> None:
    prefix = [
        _pivot("low", 100.0, 2, 4),
        _pivot("low", 100.4, 6, 8),
    ]
    later = [
        _pivot("low", 100.2, 10, 12),
        _pivot("low", 95.0, 13, 15),
    ]

    first = support_resistance_events(prefix, min_confirmations=2, tolerance_bps=50.0)
    replay = support_resistance_events(prefix + later, min_confirmations=2, tolerance_bps=50.0)

    assert first == replay


def test_unconfirmed_future_pivot_is_not_visible_before_available_at() -> None:
    index = pd.date_range("2026-01-01", periods=7, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [4, 3, 2, 3, 4, 3, 2],
            "high": [5, 4, 3, 4, 5, 4, 3],
            "low": [3, 2, 0, 2, 3, 2, 1],
            "close": [4, 3, 2, 3, 4, 3, 2],
        },
        index=index,
    )

    prefix_pivots = confirmed_pivots(frame.iloc[:4], left_bars=2, right_bars=2)
    full_pivots = confirmed_pivots(frame.iloc[:5], left_bars=2, right_bars=2)

    assert support_resistance_events(prefix_pivots, min_confirmations=1) == []
    events = support_resistance_events(full_pivots, min_confirmations=1)
    support = next(event for event in events if event.kind == "support")
    assert support.event_time == index[2]
    assert support.detected_at == index[4]
    assert support.available_at == index[4]


def test_nearest_anchor_selection_is_deterministic_for_unsorted_input() -> None:
    pivots = [
        _pivot("low", 101.0, 6, 8),
        _pivot("low", 100.0, 2, 4),
        _pivot("low", 100.45, 10, 12),
    ]

    events = support_resistance_events(pivots, min_confirmations=2, tolerance_bps=60.0)

    assert len(events) == 1
    assert events[0].source_pivot_indices == (2, 10)
    assert events[0].level == pytest.approx(100.225, abs=1e-12)


def test_invalid_parameters_and_source_timing_fail_closed() -> None:
    with pytest.raises(ValueError, match="min_confirmations"):
        support_resistance_events([], min_confirmations=0)
    with pytest.raises(ValueError, match="tolerance_bps"):
        support_resistance_events([], tolerance_bps=float("nan"))

    invalid = _pivot("low", 100.0, 2, 4)
    invalid = PivotEvent(
        kind=invalid.kind,
        level=invalid.level,
        pivot_index=invalid.pivot_index,
        detected_index=invalid.detected_index,
        event_time=invalid.event_time,
        detected_at=invalid.detected_at,
        available_at=invalid.detected_at - timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="event_time <= detected_at <= available_at"):
        support_resistance_events([invalid])


def test_distance_bps_is_symmetric_and_scale_safe() -> None:
    assert distance_bps(100.0, 100.5) == pytest.approx(distance_bps(100.5, 100.0))
    assert distance_bps(0.0, 0.0) == 0.0
