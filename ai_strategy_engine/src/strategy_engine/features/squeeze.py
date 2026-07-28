from __future__ import annotations

import numpy as np
import pandas as pd

from .common import true_range


def _rolling_linreg_last(series: pd.Series, period: int) -> pd.Series:
    x = np.arange(period, dtype=float)

    def fit_last(values: np.ndarray) -> float:
        if np.isnan(values).any():
            return np.nan
        slope, intercept = np.polyfit(x, values, 1)
        return float(intercept + slope * x[-1])

    return series.rolling(period, min_periods=period).apply(fit_last, raw=True)


def squeeze_features(
    frame: pd.DataFrame,
    *,
    bb_length: int = 20,
    bb_mult: float = 2.0,
    kc_length: int = 20,
    kc_mult: float = 1.5,
    use_true_range: bool = True,
    compatibility_mode: str = "corrected",
) -> pd.DataFrame:
    if min(bb_length, kc_length) < 2:
        raise ValueError("Lengths must be >= 2")
    if compatibility_mode not in {"corrected", "legacy_bug_compatible"}:
        raise ValueError("Invalid compatibility_mode")

    close = frame["close"]
    basis = close.rolling(bb_length, min_periods=bb_length).mean()
    std = close.rolling(bb_length, min_periods=bb_length).std(ddof=0)

    effective_bb_mult = kc_mult if compatibility_mode == "legacy_bug_compatible" else bb_mult
    dev = effective_bb_mult * std
    upper_bb = basis + dev
    lower_bb = basis - dev

    ma = close.rolling(kc_length, min_periods=kc_length).mean()
    raw_range = true_range(frame) if use_true_range else frame["high"] - frame["low"]
    range_ma = raw_range.rolling(kc_length, min_periods=kc_length).mean()
    upper_kc = ma + range_ma * kc_mult
    lower_kc = ma - range_ma * kc_mult

    squeeze_on = (lower_bb > lower_kc) & (upper_bb < upper_kc)
    squeeze_off = (lower_bb < lower_kc) & (upper_bb > upper_kc)
    no_squeeze = ~(squeeze_on | squeeze_off)

    highest = frame["high"].rolling(kc_length, min_periods=kc_length).max()
    lowest = frame["low"].rolling(kc_length, min_periods=kc_length).min()
    close_sma = close.rolling(kc_length, min_periods=kc_length).mean()
    baseline = ((highest + lowest) / 2.0 + close_sma) / 2.0
    momentum_input = close - baseline
    momentum = _rolling_linreg_last(momentum_input, kc_length)

    bb_width = upper_bb - lower_bb
    kc_width = upper_kc - lower_kc
    squeeze_ratio = bb_width / kc_width.replace(0.0, np.nan)

    result = pd.DataFrame(index=frame.index)
    result["bb_upper"] = upper_bb
    result["bb_lower"] = lower_bb
    result["kc_upper"] = upper_kc
    result["kc_lower"] = lower_kc
    result["squeeze_on"] = squeeze_on
    result["squeeze_off"] = squeeze_off
    result["no_squeeze"] = no_squeeze
    result["squeeze_ratio"] = squeeze_ratio
    result["linreg_momentum"] = momentum
    result["momentum_slope"] = momentum.diff()
    result["momentum_acceleration"] = result["momentum_slope"].diff()
    result["squeeze_release"] = squeeze_on.shift(1, fill_value=False) & ~squeeze_on
    return result
