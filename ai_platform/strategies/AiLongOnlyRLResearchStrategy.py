import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy


class AiLongOnlyRLResearchStrategy(IStrategy):
    """Research-only long-only FreqAI RL strategy for integration and OOS feasibility work."""

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

    def feature_engineering_expand_all(
        self,
        dataframe: DataFrame,
        period: int,
        metadata: dict,
        **kwargs,
    ) -> DataFrame:
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
        dataframe["%-raw_close"] = dataframe["close"]
        dataframe["%-raw_open"] = dataframe["open"]
        dataframe["%-raw_high"] = dataframe["high"]
        dataframe["%-raw_low"] = dataframe["low"]
        dataframe["%-day-of-week"] = dataframe["date"].dt.dayofweek / 6.0
        dataframe["%-hour-of-day"] = dataframe["date"].dt.hour / 23.0
        return dataframe

    def set_freqai_targets(
        self,
        dataframe: DataFrame,
        metadata: dict,
        **kwargs,
    ) -> DataFrame:
        dataframe["&-action"] = 0
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self.freqai.start(dataframe, metadata, self)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = (
            (dataframe["do_predict"] == 1)
            & (dataframe["&-action"] == 1)
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (1, "freqai_rl_long")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = (dataframe["do_predict"] == 1) & (dataframe["&-action"] == 2)
        dataframe.loc[condition, ["exit_long", "exit_tag"]] = (1, "freqai_rl_exit")
        return dataframe
