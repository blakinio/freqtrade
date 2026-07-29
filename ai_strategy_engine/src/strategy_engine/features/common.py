from __future__ import annotations

import numpy as np
import pandas as pd


def true_range(frame: pd.DataFrame) -> pd.Series:
    prev_close = frame["close"].shift(1)
    components = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - prev_close).abs(),
            (frame["low"] - prev_close).abs(),
        ],
        axis=1,
    )
    return components.max(axis=1)


def rma(series: pd.Series, period: int) -> pd.Series:
    if period < 1:
        raise ValueError("period must be >= 1")
    return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int, ma_type: str = "rma") -> pd.Series:
    tr = true_range(frame)
    if ma_type == "rma":
        return rma(tr, period)
    if ma_type == "sma":
        return tr.rolling(period, min_periods=period).mean()
    raise ValueError(f"Unsupported ma_type: {ma_type}")


def source_series(frame: pd.DataFrame, source: str) -> pd.Series:
    if source == "close":
        return frame["close"]
    if source == "hl2":
        return (frame["high"] + frame["low"]) / 2.0
    if source == "ohlc4":
        return (frame["open"] + frame["high"] + frame["low"] + frame["close"]) / 4.0
    raise ValueError(f"Unsupported source: {source}")


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0.0, np.nan)
    return numerator / denominator
