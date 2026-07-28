import numpy as np
import pandas as pd

from strategy_engine.features.squeeze import squeeze_features


def _frame() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=200, freq="5min", tz="UTC")
    base = np.linspace(100, 120, len(idx)) + np.sin(np.arange(len(idx)) / 4)
    return pd.DataFrame(
        {
            "open": base,
            "high": base + 1,
            "low": base - 1,
            "close": base + np.sin(np.arange(len(idx)) / 7),
            "volume": 1000,
        },
        index=idx,
    )


def test_bb_mult_changes_corrected_output() -> None:
    frame = _frame()
    a = squeeze_features(frame, bb_mult=1.5, compatibility_mode="corrected")
    b = squeeze_features(frame, bb_mult=2.5, compatibility_mode="corrected")
    assert not a["bb_upper"].equals(b["bb_upper"])


def test_bb_mult_is_ignored_only_in_legacy_compatibility_mode() -> None:
    frame = _frame()
    a = squeeze_features(frame, bb_mult=1.5, compatibility_mode="legacy_bug_compatible")
    b = squeeze_features(frame, bb_mult=2.5, compatibility_mode="legacy_bug_compatible")
    pd.testing.assert_series_equal(a["bb_upper"], b["bb_upper"])
