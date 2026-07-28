
from __future__ import annotations

import pandas as pd


def no_repeat_signals(raw: pd.Series, cooldown_bars: int = 0) -> pd.Series:
    """Keep transitions into a non-zero direction and enforce an optional cooldown.

    Input values are expected to be -1, 0 or 1. Output has the same domain.
    """
    if cooldown_bars < 0:
        raise ValueError("cooldown_bars must be >= 0")
    if not raw.dropna().isin([-1, 0, 1]).all():
        raise ValueError("raw signals must be in {-1, 0, 1}")
    output = pd.Series(0, index=raw.index, dtype="Int64")
    last_emitted_index = -10**12
    last_direction = 0
    for i, value in enumerate(raw.fillna(0).astype(int)):
        transition = value != 0 and value != last_direction
        cooldown_elapsed = i - last_emitted_index > cooldown_bars
        if transition and cooldown_elapsed:
            output.iloc[i] = value
            last_emitted_index = i
        if value != 0:
            last_direction = value
    return output


def time_window_mask(
    index: pd.DatetimeIndex,
    *,
    start_hour_utc: int,
    end_hour_utc: int,
) -> pd.Series:
    if index.tz is None:
        raise ValueError("index must be timezone-aware")
    if not (0 <= start_hour_utc <= 23 and 0 <= end_hour_utc <= 23):
        raise ValueError("hours must be in 0..23")
    utc = index.tz_convert("UTC")
    if start_hour_utc <= end_hour_utc:
        mask = (utc.hour >= start_hour_utc) & (utc.hour < end_hour_utc)
    else:
        mask = (utc.hour >= start_hour_utc) | (utc.hour < end_hour_utc)
    return pd.Series(mask, index=index)
