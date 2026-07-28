from __future__ import annotations

import numpy as np
import pandas as pd

from .common import atr, source_series


def supertrend_features(
    frame: pd.DataFrame,
    *,
    atr_period: int = 10,
    multiplier: float = 3.0,
    atr_type: str = "rma",
    source: str = "hl2",
) -> pd.DataFrame:
    if atr_period < 2:
        raise ValueError("atr_period must be >= 2")
    if multiplier <= 0:
        raise ValueError("multiplier must be > 0")

    src = source_series(frame, source)
    atr_values = atr(frame, atr_period, atr_type)

    basic_up = src - multiplier * atr_values
    basic_down = src + multiplier * atr_values

    final_up = basic_up.copy()
    final_down = basic_down.copy()
    direction = pd.Series(index=frame.index, dtype="float64")

    for i in range(len(frame)):
        if i == 0 or np.isnan(atr_values.iloc[i]):
            direction.iloc[i] = 1.0 if i == 0 else direction.iloc[i - 1]
            continue

        prev_up = final_up.iloc[i - 1]
        prev_down = final_down.iloc[i - 1]
        prev_close = frame["close"].iloc[i - 1]
        close = frame["close"].iloc[i]

        final_up.iloc[i] = (
            max(basic_up.iloc[i], prev_up) if prev_close > prev_up else basic_up.iloc[i]
        )
        final_down.iloc[i] = (
            min(basic_down.iloc[i], prev_down) if prev_close < prev_down else basic_down.iloc[i]
        )

        prev_direction = direction.iloc[i - 1]
        if prev_direction == -1 and close > prev_down:
            direction.iloc[i] = 1
        elif prev_direction == 1 and close < prev_up:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = prev_direction

    active_band = pd.Series(
        np.where(direction == 1, final_up, final_down),
        index=frame.index,
        dtype="float64",
    )

    result = pd.DataFrame(index=frame.index)
    result["atr"] = atr_values
    result["supertrend_up"] = final_up
    result["supertrend_down"] = final_down
    result["supertrend_direction"] = direction.astype("Int64")
    result["supertrend_band"] = active_band
    result["supertrend_distance_atr"] = (frame["close"] - active_band) / atr_values.replace(
        0.0, np.nan
    )
    result["supertrend_flip"] = direction.ne(direction.shift(1)) & direction.shift(1).notna()
    return result
