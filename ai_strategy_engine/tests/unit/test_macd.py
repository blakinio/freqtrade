import numpy as np
import pandas as pd

from strategy_engine.features.macd import macd_features


def test_sma_and_ema_signal_are_distinct() -> None:
    idx = pd.date_range("2026-01-01", periods=200, freq="5min", tz="UTC")
    close = pd.Series(np.sin(np.arange(200) / 5) + np.arange(200) / 100, index=idx)
    ema = macd_features(close, signal_ma_type="ema")
    sma = macd_features(close, signal_ma_type="sma")
    assert not ema["macd_signal"].equals(sma["macd_signal"])
