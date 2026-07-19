from functools import reduce

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import DecimalParameter, IStrategy


class AiBaselineStrategy(IStrategy):
    """Research-only FreqAI baseline.

    This strategy is intentionally simple. It exists to establish a reproducible
    benchmark for the AI-platform validation pipeline. It must not be treated as
    production-ready merely because a backtest is profitable.
    """

    timeframe = "15m"
    can_short = False
    process_only_new_candles = True
    startup_candle_count: int = 200

    minimal_roi = {
        "0": 0.03,
        "240": 0.015,
        "720": 0.0,
    }

    stoploss = -0.05
    use_exit_signal = True

    # Phase 5.1 exposes only the entry signal threshold. The default preserves
    # the pre-optimization baseline behavior outside Hyperopt.
    entry_prediction_threshold = DecimalParameter(
        0.001,
        0.02,
        decimals=3,
        default=0.005,
        space="buy",
    )
    exit_prediction_threshold = 0.0

    def feature_engineering_expand_all(
        self,
        dataframe: DataFrame,
        period: int,
        metadata: dict,
        **kwargs,
    ) -> DataFrame:
        """Features expanded by FreqAI across configured periods/timeframes/pairs."""

        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)
        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)
        dataframe["%-ema-period"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["%-relative-volume-period"] = (
            dataframe["volume"] / dataframe["volume"].rolling(period).mean()
        )

        atr = ta.ATR(dataframe, timeperiod=period)
        dataframe["%-atr-normalized-period"] = atr / dataframe["close"]

        return dataframe

    def feature_engineering_expand_basic(
        self,
        dataframe: DataFrame,
        metadata: dict,
        **kwargs,
    ) -> DataFrame:
        """Features expanded across configured timeframes/shifted candles/pairs."""

        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-volume-change"] = dataframe["volume"].pct_change()
        dataframe["%-high-low-range"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]

        return dataframe

    def feature_engineering_standard(
        self,
        dataframe: DataFrame,
        metadata: dict,
        **kwargs,
    ) -> DataFrame:
        """Base-timeframe contextual features that should not be auto-expanded."""

        dataframe["%-day-of-week"] = dataframe["date"].dt.dayofweek / 6.0
        dataframe["%-hour-of-day"] = dataframe["date"].dt.hour / 23.0
        return dataframe

    def set_freqai_targets(
        self,
        dataframe: DataFrame,
        metadata: dict,
        **kwargs,
    ) -> DataFrame:
        """Predict the average forward return over the configured label horizon."""

        horizon = self.freqai_info["feature_parameters"]["label_period_candles"]
        future_average_close = dataframe["close"].shift(-horizon).rolling(horizon).mean()
        dataframe["&-future_return"] = future_average_close / dataframe["close"] - 1
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self.freqai.start(dataframe, metadata, self)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-future_return"] > self.entry_prediction_threshold.value,
            dataframe["volume"] > 0,
        ]

        dataframe.loc[
            reduce(lambda left, right: left & right, conditions),
            ["enter_long", "enter_tag"],
        ] = (1, "freqai_baseline_long")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-future_return"] < self.exit_prediction_threshold,
        ]

        dataframe.loc[
            reduce(lambda left, right: left & right, conditions),
            ["exit_long", "exit_tag"],
        ] = (1, "freqai_baseline_exit")

        return dataframe
