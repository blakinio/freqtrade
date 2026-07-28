
from __future__ import annotations

import numpy as np
import pandas as pd

from strategy_engine.features.common import rma, safe_divide, source_series


def rsi(close: pd.Series, period: int = 14, ma_type: str = "rma") -> pd.Series:
    if period < 2:
        raise ValueError("period must be >= 2")
    delta = close.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    if ma_type == "rma":
        average_gain = rma(gains, period)
        average_loss = rma(losses, period)
    elif ma_type == "sma":
        average_gain = gains.rolling(period, min_periods=period).mean()
        average_loss = losses.rolling(period, min_periods=period).mean()
    else:
        raise ValueError("ma_type must be 'rma' or 'sma'")

    rs = safe_divide(average_gain, average_loss)
    result = 100.0 - 100.0 / (1.0 + rs)
    result = result.mask((average_gain == 0.0) & (average_loss == 0.0), 50.0)
    result = result.mask((average_loss == 0.0) & (average_gain > 0.0), 100.0)
    result = result.mask((average_gain == 0.0) & (average_loss > 0.0), 0.0)
    return result


def stochastic_rsi(
    close: pd.Series,
    *,
    rsi_period: int = 14,
    stochastic_period: int = 14,
    k_smoothing: int = 3,
    d_smoothing: int = 3,
    rsi_ma_type: str = "rma",
) -> pd.DataFrame:
    if min(rsi_period, stochastic_period, k_smoothing, d_smoothing) < 1:
        raise ValueError("all periods must be >= 1")
    rsi_value = rsi(close, rsi_period, rsi_ma_type)
    rolling_low = rsi_value.rolling(stochastic_period, min_periods=stochastic_period).min()
    rolling_high = rsi_value.rolling(stochastic_period, min_periods=stochastic_period).max()
    raw = 100.0 * safe_divide(rsi_value - rolling_low, rolling_high - rolling_low)
    k = raw.rolling(k_smoothing, min_periods=k_smoothing).mean()
    d = k.rolling(d_smoothing, min_periods=d_smoothing).mean()
    return pd.DataFrame({"rsi": rsi_value, "stoch_rsi": raw, "stoch_rsi_k": k, "stoch_rsi_d": d})


def rate_of_change(close: pd.Series, period: int = 12) -> pd.Series:
    if period < 1:
        raise ValueError("period must be >= 1")
    return 100.0 * (safe_divide(close, close.shift(period)) - 1.0)


def wavetrend_features(
    frame: pd.DataFrame,
    *,
    channel_length: int = 10,
    average_length: int = 21,
    signal_length: int = 4,
    source: str = "hl2",
    constant: float = 0.015,
) -> pd.DataFrame:
    """Independent WaveTrend-style oscillator for research.

    This is a generic public-formula implementation, not a parity claim for Miyagi.
    """
    if min(channel_length, average_length, signal_length) < 1:
        raise ValueError("periods must be >= 1")
    if constant <= 0:
        raise ValueError("constant must be > 0")
    src = source_series(frame, source)
    esa = src.ewm(span=channel_length, adjust=False, min_periods=channel_length).mean()
    deviation = (src - esa).abs().ewm(
        span=channel_length, adjust=False, min_periods=channel_length
    ).mean()
    channel_index = safe_divide(src - esa, constant * deviation)
    wt1 = channel_index.ewm(span=average_length, adjust=False, min_periods=average_length).mean()
    wt2 = wt1.rolling(signal_length, min_periods=signal_length).mean()
    result = pd.DataFrame(index=frame.index)
    result["wavetrend"] = wt1
    result["wavetrend_signal"] = wt2
    result["wavetrend_delta"] = wt1 - wt2
    result["wavetrend_cross_up"] = (wt1 > wt2) & (wt1.shift(1) <= wt2.shift(1))
    result["wavetrend_cross_down"] = (wt1 < wt2) & (wt1.shift(1) >= wt2.shift(1))
    return result
