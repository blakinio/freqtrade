import pandas as pd

from strategy_engine.features.pivots import confirmed_pivots


def test_pivot_available_only_after_right_bars() -> None:
    idx = pd.date_range("2026-01-01", periods=7, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [1, 2, 3, 2, 1, 2, 3],
            "high": [1, 2, 5, 2, 1, 2, 3],
            "low": [0, 1, 2, 1, 0, 1, 2],
            "close": [1, 2, 3, 2, 1, 2, 3],
        },
        index=idx,
    )
    events = confirmed_pivots(frame, left_bars=2, right_bars=2)
    high_event = next(event for event in events if event.kind == "high")
    assert high_event.event_time == idx[2]
    assert high_event.detected_at == idx[4]
    assert high_event.available_at == idx[4]
