from __future__ import annotations

import numpy as np
import pandas as pd

from strategy_engine.features.common import atr, source_series


def atr_range_filter(
    frame: pd.DataFrame,
    *,
    atr_period: int = 14,
    multiplier: float = 2.0,
    source: str = "close",
    atr_type: str = "rma",
) -> pd.DataFrame:
    """Stateful independent ATR range filter for bounded research."""
    if atr_period < 2:
        raise ValueError("atr_period must be >= 2")
    if multiplier <= 0:
        raise ValueError("multiplier must be > 0")
    src = source_series(frame, source)
    threshold = atr(frame, atr_period, atr_type) * multiplier
    filtered = pd.Series(np.nan, index=frame.index, dtype="float64")
    direction = pd.Series(0, index=frame.index, dtype="Int64")

    for i in range(len(frame)):
        value = src.iloc[i]
        width = threshold.iloc[i]
        if np.isnan(value) or np.isnan(width):
            continue
        if i == 0 or np.isnan(filtered.iloc[i - 1]):
            filtered.iloc[i] = value
            continue
        previous = filtered.iloc[i - 1]
        if value > previous + width:
            filtered.iloc[i] = value - width
            direction.iloc[i] = 1
        elif value < previous - width:
            filtered.iloc[i] = value + width
            direction.iloc[i] = -1
        else:
            filtered.iloc[i] = previous
            direction.iloc[i] = direction.iloc[i - 1]

    result = pd.DataFrame(index=frame.index)
    result["range_filter"] = filtered
    result["range_filter_direction"] = direction
    result["range_filter_distance_atr"] = (src - filtered) / threshold.replace(0.0, np.nan)
    result["range_filter_flip"] = direction.ne(direction.shift(1)) & direction.ne(0)
    return result
