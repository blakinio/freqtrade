from __future__ import annotations

from pandas import DataFrame, Series

from ai_platform.strategies.AiFrozenCandidateStrategy import AiFrozenCandidateStrategy


def bounded_symmetric_volume_change(volume: Series) -> Series:
    """Return a finite symmetric volume change bounded to [-2, 2]."""
    previous = volume.shift(1)
    denominator = volume.abs() + previous.abs()
    change = 2.0 * (volume - previous) / denominator.where(denominator != 0)
    return change.replace([float("inf"), float("-inf")], 0.0).fillna(0.0)


class AiFrozenCandidateStrategyV2(AiFrozenCandidateStrategy):
    """Versioned M1 remediation with finite volume-change semantics only."""

    def feature_engineering_expand_basic(
        self,
        dataframe: DataFrame,
        metadata: dict,
        **kwargs,
    ) -> DataFrame:
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-volume-change"] = bounded_symmetric_volume_change(dataframe["volume"])
        dataframe["%-high-low-range"] = (
            dataframe["high"] - dataframe["low"]
        ) / dataframe["close"]
        return dataframe
