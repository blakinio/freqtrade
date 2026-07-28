from __future__ import annotations

import pandas as pd

from strategy_engine.policies.signals import no_repeat_signals


def test_no_repeat_keeps_direction_transitions_only() -> None:
    raw = pd.Series([0, 1, 1, 1, -1, -1, 1])
    result = no_repeat_signals(raw)
    assert result.tolist() == [0, 1, 0, 0, -1, 0, 1]


def test_cooldown_blocks_rapid_direction_change_until_expiry() -> None:
    raw = pd.Series([1, 0, -1, 0, 0, -1, 0, 1])
    result = no_repeat_signals(raw, cooldown_bars=3)
    assert result.tolist() == [1, 0, 0, 0, 0, -1, 0, 0]
