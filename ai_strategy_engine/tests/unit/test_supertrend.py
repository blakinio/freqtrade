from __future__ import annotations

import pandas as pd

from strategy_engine.features.supertrend import supertrend_features


def _frame(closes: list[float]) -> pd.DataFrame:
    index = pd.date_range("2026-07-28T00:00:00Z", periods=len(closes), freq="5min")
    return pd.DataFrame(
        {
            "open": closes,
            "high": [value + 1.0 for value in closes],
            "low": [value - 1.0 for value in closes],
            "close": closes,
            "volume": [100.0] * len(closes),
        },
        index=index,
    )


def test_supertrend_flip_occurs_only_after_gap_bar_is_in_closed_input() -> None:
    closed_before_gap = _frame([100, 99, 98, 97, 96, 95, 94, 93, 92, 91])
    before = supertrend_features(
        closed_before_gap,
        atr_period=3,
        multiplier=1.5,
        atr_type="rma",
        source="hl2",
    )
    after = supertrend_features(
        _frame([100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 105]),
        atr_period=3,
        multiplier=1.5,
        atr_type="rma",
        source="hl2",
    )
    assert int(before["supertrend_direction"].iloc[-1]) == -1
    assert int(after["supertrend_direction"].iloc[-1]) == 1
    assert bool(after["supertrend_flip"].iloc[-1])
    pd.testing.assert_series_equal(
        before["supertrend_direction"],
        after["supertrend_direction"].iloc[:-1],
    )


def test_supertrend_gap_uses_gap_aware_true_range() -> None:
    result = supertrend_features(
        _frame([100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 105]),
        atr_period=3,
        multiplier=1.5,
    )
    final_high_low_range = 2.0
    assert float(result["atr"].iloc[-1]) > final_high_low_range
    assert result["supertrend_band"].iloc[-1] == result["supertrend_up"].iloc[-1]
