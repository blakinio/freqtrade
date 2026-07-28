
import numpy as np
import pandas as pd

from strategy_engine.features.trend import adx_features, fibonacci_ma_ensemble, vwap_features


def _frame() -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=200, freq="5min", tz="UTC")
    close = 100 + np.arange(200) * 0.1 + np.sin(np.arange(200) / 4)
    return pd.DataFrame(
        {
            "open": close - 0.1,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000 + np.arange(200),
        },
        index=index,
    )


def test_session_vwap_is_finite_after_first_positive_volume_bar() -> None:
    result = vwap_features(_frame(), mode="session")
    assert result["vwap"].notna().all()


def test_adx_is_bounded_when_defined() -> None:
    values = adx_features(_frame())["adx"].dropna()
    assert values.between(0, 100).all()


def test_fibonacci_ensemble_has_declared_period_columns() -> None:
    result = fibonacci_ma_ensemble(_frame()["close"], periods=(5, 8, 13))
    assert {"fib_ma_5", "fib_ma_8", "fib_ma_13", "fib_ma_ensemble"} <= set(result)
