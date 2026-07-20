from __future__ import annotations

import numpy as np
from pandas import DataFrame, Series

_REQUIRED_OHLCV = {"open", "high", "low", "close", "volume"}


def _validate_ohlcv(dataframe: DataFrame) -> None:
    missing = sorted(_REQUIRED_OHLCV.difference(dataframe.columns))
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {', '.join(missing)}")


def rolling_vwap(dataframe: DataFrame, periods: int) -> Series:
    """Return a rolling typical-price VWAP without future data."""
    _validate_ohlcv(dataframe)
    if periods < 1:
        raise ValueError("periods must be >= 1")

    typical_price = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
    weighted_price = typical_price * dataframe["volume"]
    weighted_sum = weighted_price.rolling(periods, min_periods=periods).sum()
    volume_sum = dataframe["volume"].rolling(periods, min_periods=periods).sum()
    return weighted_sum / volume_sum.replace(0, np.nan)


def add_wickhunter_vwap_gates(
    dataframe: DataFrame,
    *,
    periods: int = 10,
    long_distance: float = 0.01,
    short_distance: float = 0.01,
) -> DataFrame:
    """Add Wick-Hunter-style VWAP distance gates.

    These are gates only. A liquidation event is still required before a trade
    can be considered. ``long_distance`` and ``short_distance`` are ratios, so
    ``0.01`` means one percent.
    """
    if long_distance < 0 or short_distance < 0:
        raise ValueError("VWAP distances must be non-negative")

    result = dataframe.copy()
    result["tv_wh_vwap"] = rolling_vwap(result, periods)
    result["tv_wh_long_gate"] = (
        result["close"] <= result["tv_wh_vwap"] * (1.0 - long_distance)
    ).astype(int)
    result["tv_wh_short_gate"] = (
        result["close"] >= result["tv_wh_vwap"] * (1.0 + short_distance)
    ).astype(int)
    return result


def add_donchian_signals(
    dataframe: DataFrame,
    *,
    entry_period: int = 20,
    exit_period: int = 10,
    ema_period: int = 100,
) -> DataFrame:
    """Add a no-lookahead Donchian breakout adaptation with an EMA filter."""
    _validate_ohlcv(dataframe)
    if min(entry_period, exit_period, ema_period) < 1:
        raise ValueError("Donchian and EMA periods must be >= 1")

    result = dataframe.copy()
    result["tv_donchian_entry_upper"] = (
        result["high"].rolling(entry_period, min_periods=entry_period).max().shift(1)
    )
    result["tv_donchian_entry_lower"] = (
        result["low"].rolling(entry_period, min_periods=entry_period).min().shift(1)
    )
    result["tv_donchian_exit_upper"] = (
        result["high"].rolling(exit_period, min_periods=exit_period).max().shift(1)
    )
    result["tv_donchian_exit_lower"] = (
        result["low"].rolling(exit_period, min_periods=exit_period).min().shift(1)
    )
    result["tv_donchian_ema"] = result["close"].ewm(
        span=ema_period,
        adjust=False,
        min_periods=ema_period,
    ).mean()

    result["tv_donchian_enter_long"] = (
        (result["close"] > result["tv_donchian_entry_upper"])
        & (result["close"] > result["tv_donchian_ema"])
    ).astype(int)
    result["tv_donchian_enter_short"] = (
        (result["close"] < result["tv_donchian_entry_lower"])
        & (result["close"] < result["tv_donchian_ema"])
    ).astype(int)
    result["tv_donchian_exit_long"] = (
        result["close"] < result["tv_donchian_exit_lower"]
    ).astype(int)
    result["tv_donchian_exit_short"] = (
        result["close"] > result["tv_donchian_exit_upper"]
    ).astype(int)
    return result


def _true_range(dataframe: DataFrame) -> Series:
    previous_close = dataframe["close"].shift(1)
    ranges = DataFrame(
        {
            "high_low": dataframe["high"] - dataframe["low"],
            "high_previous_close": (dataframe["high"] - previous_close).abs(),
            "low_previous_close": (dataframe["low"] - previous_close).abs(),
        },
        index=dataframe.index,
    )
    return ranges.max(axis=1)


def add_supertrend_signals(
    dataframe: DataFrame,
    *,
    atr_period: int = 10,
    multiplier: float = 3.0,
) -> DataFrame:
    """Add a deterministic Supertrend adaptation and reversal signals."""
    _validate_ohlcv(dataframe)
    if atr_period < 1:
        raise ValueError("atr_period must be >= 1")
    if multiplier <= 0:
        raise ValueError("multiplier must be > 0")

    result = dataframe.copy()
    atr = _true_range(result).rolling(atr_period, min_periods=atr_period).mean()
    midpoint = (result["high"] + result["low"]) / 2.0
    basic_upper = midpoint + multiplier * atr
    basic_lower = midpoint - multiplier * atr

    final_upper = np.full(len(result), np.nan, dtype=float)
    final_lower = np.full(len(result), np.nan, dtype=float)
    trend = np.full(len(result), np.nan, dtype=float)
    supertrend = np.full(len(result), np.nan, dtype=float)

    valid_positions = np.flatnonzero(atr.notna().to_numpy())
    if valid_positions.size:
        start = int(valid_positions[0])
        close = result["close"].to_numpy(dtype=float)
        basic_upper_values = basic_upper.to_numpy(dtype=float)
        basic_lower_values = basic_lower.to_numpy(dtype=float)

        final_upper[start] = basic_upper_values[start]
        final_lower[start] = basic_lower_values[start]
        trend[start] = 1.0
        supertrend[start] = final_lower[start]

        for position in range(start + 1, len(result)):
            previous = position - 1
            upper = basic_upper_values[position]
            lower = basic_lower_values[position]

            final_upper[position] = (
                upper
                if upper < final_upper[previous] or close[previous] > final_upper[previous]
                else final_upper[previous]
            )
            final_lower[position] = (
                lower
                if lower > final_lower[previous] or close[previous] < final_lower[previous]
                else final_lower[previous]
            )

            if trend[previous] < 0 and close[position] > final_upper[position]:
                trend[position] = 1.0
            elif trend[previous] > 0 and close[position] < final_lower[position]:
                trend[position] = -1.0
            else:
                trend[position] = trend[previous]

            supertrend[position] = (
                final_lower[position] if trend[position] > 0 else final_upper[position]
            )

    result["tv_supertrend_atr"] = atr
    result["tv_supertrend"] = supertrend
    result["tv_supertrend_direction"] = trend
    previous_trend = result["tv_supertrend_direction"].shift(1)
    result["tv_supertrend_enter_long"] = (
        (result["tv_supertrend_direction"] > 0) & (previous_trend < 0)
    ).astype(int)
    result["tv_supertrend_enter_short"] = (
        (result["tv_supertrend_direction"] < 0) & (previous_trend > 0)
    ).astype(int)
    result["tv_supertrend_exit_long"] = result["tv_supertrend_enter_short"]
    result["tv_supertrend_exit_short"] = result["tv_supertrend_enter_long"]
    return result


def add_bollinger_mean_reversion_signals(
    dataframe: DataFrame,
    *,
    periods: int = 20,
    standard_deviations: float = 2.0,
) -> DataFrame:
    """Add a simple Bollinger mean-reversion adaptation."""
    _validate_ohlcv(dataframe)
    if periods < 2:
        raise ValueError("periods must be >= 2")
    if standard_deviations <= 0:
        raise ValueError("standard_deviations must be > 0")

    result = dataframe.copy()
    basis = result["close"].rolling(periods, min_periods=periods).mean()
    deviation = result["close"].rolling(periods, min_periods=periods).std(ddof=0)
    result["tv_bb_basis"] = basis
    result["tv_bb_upper"] = basis + standard_deviations * deviation
    result["tv_bb_lower"] = basis - standard_deviations * deviation
    result["tv_bb_enter_long"] = (result["close"] < result["tv_bb_lower"]).astype(int)
    result["tv_bb_enter_short"] = (result["close"] > result["tv_bb_upper"]).astype(int)
    result["tv_bb_exit_long"] = (result["close"] >= result["tv_bb_basis"]).astype(int)
    result["tv_bb_exit_short"] = (result["close"] <= result["tv_bb_basis"]).astype(int)
    return result
