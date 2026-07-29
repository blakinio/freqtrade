from __future__ import annotations

import numpy as np
import pandas as pd


def candle_geometry(frame: pd.DataFrame, epsilon: float = 1e-12) -> pd.DataFrame:
    candle_range = frame["high"] - frame["low"]
    denominator = candle_range.clip(lower=epsilon)

    body = (frame["close"] - frame["open"]).abs()
    upper_wick = frame["high"] - frame[["open", "close"]].max(axis=1)
    lower_wick = frame[["open", "close"]].min(axis=1) - frame["low"]

    result = pd.DataFrame(index=frame.index)
    result["range"] = candle_range
    result["body"] = body
    result["upper_wick"] = upper_wick.clip(lower=0.0)
    result["lower_wick"] = lower_wick.clip(lower=0.0)
    result["body_ratio"] = body / denominator
    result["upper_wick_ratio"] = result["upper_wick"] / denominator
    result["lower_wick_ratio"] = result["lower_wick"] / denominator
    result["is_bullish"] = frame["close"] > frame["open"]
    result["is_bearish"] = frame["close"] < frame["open"]
    result.loc[candle_range <= epsilon, ["body_ratio", "upper_wick_ratio", "lower_wick_ratio"]] = (
        np.nan
    )
    return result
