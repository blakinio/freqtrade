from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy

from ai_platform.research.tradingview.signals import (
    add_bollinger_mean_reversion_signals,
    add_donchian_signals,
    add_supertrend_signals,
)


class TVDonchianBreakoutStrategy(IStrategy):
    """Research-only Donchian breakout adaptation for futures backtesting."""

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 120
    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return add_donchian_signals(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        liquid = dataframe["volume"] > 0
        dataframe.loc[
            (dataframe["tv_donchian_enter_long"] == 1) & liquid,
            "enter_long",
        ] = 1
        dataframe.loc[
            (dataframe["tv_donchian_enter_short"] == 1) & liquid,
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["tv_donchian_exit_long"] == 1, "exit_long"] = 1
        dataframe.loc[dataframe["tv_donchian_exit_short"] == 1, "exit_short"] = 1
        return dataframe


class TVSupertrendStrategy(IStrategy):
    """Research-only Supertrend reversal adaptation for futures backtesting."""

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 50
    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return add_supertrend_signals(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        liquid = dataframe["volume"] > 0
        dataframe.loc[
            (dataframe["tv_supertrend_enter_long"] == 1) & liquid,
            "enter_long",
        ] = 1
        dataframe.loc[
            (dataframe["tv_supertrend_enter_short"] == 1) & liquid,
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["tv_supertrend_exit_long"] == 1, "exit_long"] = 1
        dataframe.loc[dataframe["tv_supertrend_exit_short"] == 1, "exit_short"] = 1
        return dataframe


class TVBollingerMeanReversionStrategy(IStrategy):
    """Research-only Bollinger mean-reversion adaptation for futures backtesting."""

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 50
    minimal_roi = {"0": 100.0}
    stoploss = -0.08
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return add_bollinger_mean_reversion_signals(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        liquid = dataframe["volume"] > 0
        dataframe.loc[
            (dataframe["tv_bb_enter_long"] == 1) & liquid,
            "enter_long",
        ] = 1
        dataframe.loc[
            (dataframe["tv_bb_enter_short"] == 1) & liquid,
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["tv_bb_exit_long"] == 1, "exit_long"] = 1
        dataframe.loc[dataframe["tv_bb_exit_short"] == 1, "exit_short"] = 1
        return dataframe
