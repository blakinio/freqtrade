
import numpy as np
import pandas as pd

from strategy_engine.features.volume import money_flow_index, volume_ema_oscillator


def test_mfi_is_bounded() -> None:
    index = pd.date_range("2026-01-01", periods=100, freq="5min", tz="UTC")
    close = 100 + np.sin(np.arange(100) / 5)
    frame = pd.DataFrame(
        {"high": close + 1, "low": close - 1, "close": close, "volume": 1000},
        index=index,
    )
    assert money_flow_index(frame).dropna().between(0, 100).all()


def test_volume_oscillator_requires_fast_below_slow() -> None:
    volume = pd.Series(range(100), dtype=float)
    try:
        volume_ema_oscillator(volume, fast=10, slow=5)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
