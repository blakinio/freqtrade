
import numpy as np
import pandas as pd
import pytest

from strategy_engine.features.momentum import rate_of_change, rsi, stochastic_rsi


def test_rsi_is_bounded() -> None:
    index = pd.date_range("2026-01-01", periods=100, freq="5min", tz="UTC")
    close = pd.Series(100 + np.sin(np.arange(100) / 4), index=index)
    values = rsi(close, 14).dropna()
    assert values.between(0, 100).all()


def test_stochastic_rsi_is_bounded() -> None:
    index = pd.date_range("2026-01-01", periods=150, freq="5min", tz="UTC")
    close = pd.Series(100 + np.sin(np.arange(150) / 5), index=index)
    values = stochastic_rsi(close)["stoch_rsi"].dropna()
    assert values.between(0, 100).all()


def test_roc_matches_simple_change() -> None:
    close = pd.Series([100.0, 110.0, 121.0])
    assert rate_of_change(close, 1).iloc[-1] == pytest.approx(10.0)
