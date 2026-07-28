from __future__ import annotations

import numpy as np
import pandas as pd

from strategy_engine.features.common import safe_divide


def money_flow_index(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    if period < 2:
        raise ValueError("period must be >= 2")
    if "volume" not in frame:
        raise ValueError("volume column is required")
    typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    raw_flow = typical * frame["volume"]
    direction = typical.diff()
    positive = raw_flow.where(direction > 0.0, 0.0)
    negative = raw_flow.where(direction < 0.0, 0.0)
    positive_sum = positive.rolling(period, min_periods=period).sum()
    negative_sum = negative.rolling(period, min_periods=period).sum()
    ratio = safe_divide(positive_sum, negative_sum)
    mfi = 100.0 - 100.0 / (1.0 + ratio)
    mfi = mfi.mask((positive_sum == 0.0) & (negative_sum == 0.0), 50.0)
    mfi = mfi.mask((negative_sum == 0.0) & (positive_sum > 0.0), 100.0)
    mfi = mfi.mask((positive_sum == 0.0) & (negative_sum > 0.0), 0.0)
    return mfi


def volume_ema_oscillator(
    volume: pd.Series,
    *,
    fast: int = 5,
    slow: int = 10,
) -> pd.Series:
    if min(fast, slow) < 1 or fast >= slow:
        raise ValueError("require 1 <= fast < slow")
    fast_ema = volume.ewm(span=fast, adjust=False, min_periods=fast).mean()
    slow_ema = volume.ewm(span=slow, adjust=False, min_periods=slow).mean()
    return 100.0 * safe_divide(fast_ema - slow_ema, slow_ema)


def robust_volume_zscore(volume: pd.Series, window: int = 100) -> pd.Series:
    if window < 5:
        raise ValueError("window must be >= 5")
    median = volume.rolling(window, min_periods=window).median()
    absolute_deviation = (volume - median).abs()
    mad = absolute_deviation.rolling(window, min_periods=window).median()
    scale = 1.4826 * mad
    result = safe_divide(volume - median, scale)
    return result.replace([np.inf, -np.inf], np.nan)
