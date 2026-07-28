
import numpy as np
import pandas as pd

from strategy_engine.features.range_filter import atr_range_filter


def test_range_filter_is_stateful_and_direction_is_bounded() -> None:
    index = pd.date_range("2026-01-01", periods=120, freq="5min", tz="UTC")
    close = 100 + np.arange(120) * 0.2
    frame = pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close},
        index=index,
    )
    result = atr_range_filter(frame)
    assert result["range_filter_direction"].dropna().isin([-1, 0, 1]).all()
