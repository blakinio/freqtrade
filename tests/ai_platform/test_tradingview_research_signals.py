from __future__ import annotations

import pytest


pd = pytest.importorskip("pandas")

from ai_platform.research.tradingview.signals import (  # noqa: E402
    add_bollinger_mean_reversion_signals,
    add_donchian_signals,
    add_supertrend_signals,
    add_wickhunter_vwap_gates,
    rolling_vwap,
)


def _frame(close: list[float], *, volume: list[float] | None = None) -> pd.DataFrame:
    close_series = pd.Series(close, dtype=float)
    return pd.DataFrame(
        {
            "open": close_series,
            "high": close_series + 0.5,
            "low": close_series - 0.5,
            "close": close_series,
            "volume": volume if volume is not None else [1.0] * len(close),
        }
    )


def test_rolling_vwap_uses_only_current_and_past_rows() -> None:
    dataframe = pd.DataFrame(
        {
            "open": [1.0, 2.0, 3.0],
            "high": [1.0, 2.0, 3.0],
            "low": [1.0, 2.0, 3.0],
            "close": [1.0, 2.0, 3.0],
            "volume": [1.0, 1.0, 2.0],
        }
    )

    result = rolling_vwap(dataframe, periods=2)

    assert pd.isna(result.iloc[0])
    assert result.iloc[1] == pytest.approx(1.5)
    assert result.iloc[2] == pytest.approx(8.0 / 3.0)


def test_donchian_entry_uses_previous_window_not_current_breakout_candle() -> None:
    dataframe = pd.DataFrame(
        {
            "open": [9.0, 10.0, 49.0],
            "high": [10.0, 11.0, 50.0],
            "low": [8.0, 9.0, 48.0],
            "close": [9.0, 10.0, 49.0],
            "volume": [1.0, 1.0, 1.0],
        }
    )

    result = add_donchian_signals(
        dataframe,
        entry_period=2,
        exit_period=2,
        ema_period=2,
    )

    assert result.loc[2, "tv_donchian_entry_upper"] == pytest.approx(11.0)
    assert result.loc[2, "tv_donchian_enter_long"] == 1


def test_supertrend_adaptation_emits_bearish_and_bullish_reversals() -> None:
    dataframe = _frame([10, 9, 8, 7, 6, 5, 6, 7, 8, 9, 10])

    result = add_supertrend_signals(dataframe, atr_period=3, multiplier=1.0)

    assert result["tv_supertrend_enter_short"].sum() >= 1
    assert result["tv_supertrend_enter_long"].sum() >= 1


def test_bollinger_mean_reversion_flags_large_downside_outlier() -> None:
    dataframe = _frame([10.0] * 19 + [1.0])

    result = add_bollinger_mean_reversion_signals(dataframe, periods=20)

    assert result.loc[19, "tv_bb_enter_long"] == 1
    assert result.loc[19, "tv_bb_enter_short"] == 0


def test_wickhunter_vwap_layer_is_a_gate_not_a_liquidation_trigger() -> None:
    dataframe = pd.DataFrame(
        {
            "open": [100.0, 100.0, 70.0],
            "high": [100.0, 100.0, 70.0],
            "low": [100.0, 100.0, 70.0],
            "close": [100.0, 100.0, 70.0],
            "volume": [1.0, 1.0, 1.0],
        }
    )

    result = add_wickhunter_vwap_gates(dataframe, periods=3, long_distance=0.10)

    assert result.loc[2, "tv_wh_long_gate"] == 1
    assert "liquidation" not in " ".join(result.columns)


def test_missing_ohlcv_columns_fail_explicitly() -> None:
    with pytest.raises(ValueError, match="Missing required OHLCV columns"):
        rolling_vwap(pd.DataFrame({"close": [1.0]}), periods=2)
