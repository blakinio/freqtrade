from __future__ import annotations

import pandas as pd
import pytest

from ai_platform.strategies.TradingViewResearchStrategies import (
    TVBollingerMeanReversionStrategy,
    TVDonchianBreakoutStrategy,
    TVSupertrendStrategy,
)


def _sample_frame(rows: int = 160) -> pd.DataFrame:
    close = pd.Series([100.0 + ((index % 20) - 10) * 0.5 for index in range(rows)])
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": [1000.0] * rows,
        }
    )


@pytest.mark.parametrize(
    "strategy_class",
    [
        TVDonchianBreakoutStrategy,
        TVSupertrendStrategy,
        TVBollingerMeanReversionStrategy,
    ],
)
def test_research_strategy_signal_pipeline(strategy_class: type) -> None:
    strategy = object.__new__(strategy_class)
    dataframe = strategy.populate_indicators(_sample_frame(), {})
    dataframe = strategy.populate_entry_trend(dataframe, {})
    dataframe = strategy.populate_exit_trend(dataframe, {})

    assert strategy.INTERFACE_VERSION == 3
    assert strategy.can_short is True
    assert strategy.timeframe == "15m"
    assert {"enter_long", "enter_short", "exit_long", "exit_short"}.issubset(dataframe.columns)
