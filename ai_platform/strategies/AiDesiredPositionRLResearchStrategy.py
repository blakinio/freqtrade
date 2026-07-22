import talib.abstract as ta
from pandas import DataFrame

from ai_platform.scripts.rl_v2_synthetic_reference import DesiredPosition
from freqtrade.strategy import IStrategy


class AiDesiredPositionRLResearchStrategy(IStrategy):
    """Research-only FreqAI strategy exposing RL-v2 desired-position policy outputs."""

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
        dataframe["&-action"] = DesiredPosition.TARGET_FLAT.value
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self.freqai.start(dataframe, metadata, self)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        target_long = (
            (dataframe["do_predict"] == 1)
            & (dataframe["&-action"] == DesiredPosition.TARGET_LONG.value)
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[target_long, ["enter_long", "enter_tag"]] = (
            1,
            "freqai_rl_v2_target_long",
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        target_flat = (dataframe["do_predict"] == 1) & (
            dataframe["&-action"] == DesiredPosition.TARGET_FLAT.value
        )
        dataframe.loc[target_flat, ["exit_long", "exit_tag"]] = (
            1,
            "freqai_rl_v2_target_flat",
        )
        return dataframe
