from datetime import timedelta

import pandas as pd
import pytest

from strategy_engine.features.market_structure import (
    FairValueGapDirection,
    PivotLabel,
    StructureEvent,
    StructureEventType,
    classify_confirmed_pivots,
    confirmed_fair_value_gaps,
    detect_structure_events,
    structure_zones,
)
from strategy_engine.features.pivots import PivotEvent


def pivot(
    kind: str,
    level: float,
    pivot_index: int,
    detected_index: int,
    index: pd.DatetimeIndex,
) -> PivotEvent:
    return PivotEvent(
        kind=kind,
        level=level,
        pivot_index=pivot_index,
        detected_index=detected_index,
        event_time=index[pivot_index],
        detected_at=index[detected_index],
        available_at=index[detected_index],
    )


def test_confirmed_pivots_are_labeled_hh_hl_lh_ll_eqh_eql() -> None:
    index = pd.date_range("2026-01-01", periods=20, freq="5min", tz="UTC")
    labeled = classify_confirmed_pivots(
        [
            pivot("high", 100.0, 1, 3, index),
            pivot("low", 90.0, 2, 4, index),
            pivot("high", 110.0, 5, 7, index),
            pivot("low", 95.0, 6, 8, index),
            pivot("high", 105.0, 9, 11, index),
            pivot("low", 85.0, 10, 12, index),
            pivot("high", 105.05, 13, 15, index),
            pivot("low", 85.04, 14, 16, index),
        ],
        equality_tolerance_bps=10,
    )

    assert [item.label for item in labeled] == [
        None,
        None,
        PivotLabel.HH,
        PivotLabel.HL,
        PivotLabel.LH,
        PivotLabel.LL,
        PivotLabel.EQH,
        PivotLabel.EQL,
    ]


def test_bos_and_choch_use_only_pivots_available_at_break_time() -> None:
    index = pd.date_range("2026-01-01", periods=8, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [95, 95, 95, 95, 95, 95, 85, 105],
            "high": [96, 96, 101, 96, 96, 96, 95, 111],
            "low": [94, 89, 94, 94, 94, 84, 80, 104],
            "close": [95, 95, 95, 95, 95, 85, 85, 110],
        },
        index=index,
    )
    pivots = [
        PivotEvent("high", 100, 2, 4, index[2], index[4], index[4]),
        PivotEvent("low", 90, 1, 3, index[1], index[3], index[3]),
    ]

    events = detect_structure_events(frame, pivots)

    assert [event.event_type for event in events] == [
        StructureEventType.BOS_BEARISH,
        StructureEventType.CHOCH_BULLISH,
    ]
    assert events[0].event_time == index[5]
    assert events[1].event_time == index[7]
    assert all(event.available_at == event.detected_at for event in events)


def test_fvg_waits_for_third_closed_candle_and_replay_is_append_only() -> None:
    index = pd.date_range("2026-01-01", periods=4, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [100, 103, 108, 109],
            "high": [102, 107, 110, 111],
            "low": [99, 102, 105, 108],
            "close": [101, 106, 109, 110],
        },
        index=index,
    )

    assert confirmed_fair_value_gaps(frame.iloc[:2]) == []
    prefix = confirmed_fair_value_gaps(
        frame.iloc[:3],
        processing_latency=timedelta(seconds=1),
    )
    replay = confirmed_fair_value_gaps(
        frame,
        processing_latency=timedelta(seconds=1),
    )

    assert prefix == replay[: len(prefix)]
    assert prefix[0].direction is FairValueGapDirection.BULLISH
    assert prefix[0].lower_bound == 102
    assert prefix[0].upper_bound == 105
    assert prefix[0].detected_at == index[2]
    assert prefix[0].available_at == index[2] + timedelta(seconds=1)


def test_zone_heuristic_uses_only_pre_break_candles() -> None:
    index = pd.date_range("2026-01-01", periods=5, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [100, 99, 98, 105, 200],
            "high": [102, 101, 100, 110, 210],
            "low": [98, 95, 96, 104, 190],
            "close": [99, 98, 99, 109, 205],
        },
        index=index,
    )
    event = StructureEvent(
        event_type=StructureEventType.BOS_BULLISH,
        level=103,
        source_pivot_index=0,
        break_index=3,
        event_time=index[3],
        detected_at=index[3],
        available_at=index[3],
        pivot_version="v1",
        reason_code="CLOSE_ABOVE_CONFIRMED_HIGH",
    )

    zones = structure_zones(frame, [event], lookback_bars=3)

    assert len(zones) == 1
    assert zones[0].anchor_index == 1
    assert zones[0].lower_bound == 95
    assert zones[0].upper_bound == 99
    assert zones[0].available_at == index[3]
    assert zones[0].heuristic_version == "pre-break-extreme-body-v1"


def test_invalid_or_non_point_in_time_inputs_fail_closed() -> None:
    naive = pd.DataFrame(
        {"open": [1], "high": [2], "low": [0], "close": [1]},
        index=pd.date_range("2026-01-01", periods=1),
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        confirmed_fair_value_gaps(naive)

    aware = pd.date_range("2026-01-01", periods=5, freq="5min", tz="UTC")
    invalid = PivotEvent(
        "high",
        2,
        1,
        3,
        aware[1],
        aware[3],
        aware[2],
    )
    with pytest.raises(
        ValueError,
        match="event_time <= detected_at <= available_at",
    ):
        classify_confirmed_pivots([invalid])
