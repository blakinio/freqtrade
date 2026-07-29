from __future__ import annotations

import pandas as pd


def macd_features(
    close: pd.Series,
    *,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    signal_ma_type: str = "ema",
) -> pd.DataFrame:
    if fast >= slow:
        raise ValueError("fast must be smaller than slow")
    if min(fast, slow, signal) < 1:
        raise ValueError("Periods must be >= 1")

    fast_ma = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
    slow_ma = close.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd = fast_ma - slow_ma

    if signal_ma_type == "ema":
        signal_line = macd.ewm(span=signal, adjust=False, min_periods=signal).mean()
    elif signal_ma_type == "sma":
        signal_line = macd.rolling(signal, min_periods=signal).mean()
    else:
        raise ValueError("signal_ma_type must be 'ema' or 'sma'")

    hist = macd - signal_line

    result = pd.DataFrame(index=close.index)
    result["macd"] = macd
    result["macd_signal"] = signal_line
    result["macd_hist"] = hist
    result["macd_hist_slope"] = hist.diff()
    result["macd_hist_acceleration"] = hist.diff().diff()
    result["macd_zero_regime"] = (macd >= 0).astype("Int64")
    result["macd_cross_up"] = (macd > signal_line) & (macd.shift(1) <= signal_line.shift(1))
    result["macd_cross_down"] = (macd < signal_line) & (macd.shift(1) >= signal_line.shift(1))
    return result
