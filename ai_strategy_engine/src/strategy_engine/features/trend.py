from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from strategy_engine.features.common import atr, rma, safe_divide


def vwap_features(
    frame: pd.DataFrame,
    *,
    mode: str = "session",
    rolling_window: int | None = None,
) -> pd.DataFrame:
    if "volume" not in frame:
        raise ValueError("volume column is required")
    typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    pv = typical * frame["volume"]

    if mode == "session":
        if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
            raise ValueError("session VWAP requires a timezone-aware DatetimeIndex")
        session_key = frame.index.floor("D")
        numerator = pv.groupby(session_key).cumsum()
        denominator = frame["volume"].groupby(session_key).cumsum()
    elif mode == "cumulative":
        numerator = pv.cumsum()
        denominator = frame["volume"].cumsum()
    elif mode == "rolling":
        if rolling_window is None or rolling_window < 2:
            raise ValueError("rolling_window must be >= 2 for rolling mode")
        numerator = pv.rolling(rolling_window, min_periods=rolling_window).sum()
        denominator = frame["volume"].rolling(rolling_window, min_periods=rolling_window).sum()
    else:
        raise ValueError("mode must be session, cumulative or rolling")

    vwap = safe_divide(numerator, denominator)
    result = pd.DataFrame(index=frame.index)
    result["vwap"] = vwap
    result["distance_to_vwap"] = frame["close"] - vwap
    result["distance_to_vwap_pct"] = safe_divide(frame["close"] - vwap, vwap)
    return result


def adx_features(frame: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    if period < 2:
        raise ValueError("period must be >= 2")
    up_move = frame["high"].diff()
    down_move = -frame["low"].diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0.0), up_move, 0.0),
        index=frame.index,
        dtype="float64",
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0.0), down_move, 0.0),
        index=frame.index,
        dtype="float64",
    )
    atr_value = atr(frame, period, "rma")
    plus_di = 100.0 * safe_divide(rma(plus_dm, period), atr_value)
    minus_di = 100.0 * safe_divide(rma(minus_dm, period), atr_value)
    dx = 100.0 * safe_divide((plus_di - minus_di).abs(), plus_di + minus_di)
    adx = rma(dx, period)
    result = pd.DataFrame(index=frame.index)
    result["plus_di"] = plus_di
    result["minus_di"] = minus_di
    result["adx"] = adx
    result["di_spread"] = plus_di - minus_di
    result["adx_rising"] = adx > adx.shift(1)
    return result


def psar_features(
    frame: pd.DataFrame,
    *,
    step: float = 0.02,
    max_step: float = 0.2,
) -> pd.DataFrame:
    if step <= 0 or max_step <= 0 or step > max_step:
        raise ValueError("require 0 < step <= max_step")
    if len(frame) == 0:
        return pd.DataFrame(index=frame.index)

    high = frame["high"].to_numpy(dtype=float)
    low = frame["low"].to_numpy(dtype=float)
    close = frame["close"].to_numpy(dtype=float)
    sar = np.full(len(frame), np.nan)
    direction = np.ones(len(frame), dtype=int)
    acceleration = step
    extreme = high[0]
    sar[0] = low[0]

    for i in range(1, len(frame)):
        prior_sar = sar[i - 1]
        if direction[i - 1] == 1:
            candidate = prior_sar + acceleration * (extreme - prior_sar)
            candidate = min(candidate, low[i - 1])
            if i > 1:
                candidate = min(candidate, low[i - 2])
            if low[i] < candidate:
                direction[i] = -1
                sar[i] = extreme
                extreme = low[i]
                acceleration = step
            else:
                direction[i] = 1
                sar[i] = candidate
                if high[i] > extreme:
                    extreme = high[i]
                    acceleration = min(max_step, acceleration + step)
        else:
            candidate = prior_sar + acceleration * (extreme - prior_sar)
            candidate = max(candidate, high[i - 1])
            if i > 1:
                candidate = max(candidate, high[i - 2])
            if high[i] > candidate:
                direction[i] = 1
                sar[i] = extreme
                extreme = high[i]
                acceleration = step
            else:
                direction[i] = -1
                sar[i] = candidate
                if low[i] < extreme:
                    extreme = low[i]
                    acceleration = min(max_step, acceleration + step)

    result = pd.DataFrame(index=frame.index)
    result["psar"] = sar
    result["psar_direction"] = pd.Series(direction, index=frame.index, dtype="Int64")
    result["psar_distance"] = close - sar
    result["psar_flip"] = result["psar_direction"].ne(result["psar_direction"].shift(1))
    return result


def fibonacci_ma_ensemble(
    close: pd.Series,
    *,
    periods: Sequence[int] = (5, 8, 13, 21, 34, 55),
    ma_type: str = "ema",
    aggregation: str = "mean",
) -> pd.DataFrame:
    """Independent Fibonacci-period moving-average ensemble for bounded research."""
    parsed = tuple(int(period) for period in periods)
    if not parsed or min(parsed) < 1 or len(set(parsed)) != len(parsed):
        raise ValueError("periods must be unique positive integers")
    columns: dict[str, pd.Series] = {}
    for period in parsed:
        if ma_type == "ema":
            value = close.ewm(span=period, adjust=False, min_periods=period).mean()
        elif ma_type == "sma":
            value = close.rolling(period, min_periods=period).mean()
        else:
            raise ValueError("ma_type must be ema or sma")
        columns[f"fib_ma_{period}"] = value
    frame = pd.DataFrame(columns, index=close.index)
    if aggregation == "mean":
        aggregate = frame.mean(axis=1, skipna=False)
    elif aggregation == "median":
        aggregate = frame.median(axis=1, skipna=False)
    else:
        raise ValueError("aggregation must be mean or median")
    frame["fib_ma_ensemble"] = aggregate
    frame["fib_ma_distance_pct"] = safe_divide(close - aggregate, aggregate)
    return frame
