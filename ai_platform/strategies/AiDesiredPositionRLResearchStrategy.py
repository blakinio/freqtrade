from __future__ import annotations

from collections.abc import Iterable

from pandas import DataFrame

from ai_platform.scripts.rl_v2_synthetic_reference import (
    DesiredPosition,
    RLV2ObservabilityAccumulator,
    RLV2SyntheticReferenceError,
)
from ai_platform.strategies.AiLongOnlyRLResearchStrategy import AiLongOnlyRLResearchStrategy


class AiDesiredPositionRLResearchStrategy(AiLongOnlyRLResearchStrategy):
    """Research-only RL-v2 strategy using position-independent desired-position actions."""

    @staticmethod
    def new_observability_accumulator(pairs: Iterable[str]) -> RLV2ObservabilityAccumulator:
        """Create the canonical zero-preserving RL-v2 observability accumulator."""
        return RLV2ObservabilityAccumulator(pairs)

    @staticmethod
    def record_prediction_observability(
        accumulator: RLV2ObservabilityAccumulator,
        pair: str,
        dataframe: DataFrame,
    ) -> None:
        """Bind prediction rows to canonical action, gating, and pre-trade signal counters."""
        required_columns = {"&-action", "do_predict"}
        missing = required_columns.difference(dataframe.columns)
        if missing:
            missing_columns = ", ".join(sorted(missing))
            raise RLV2SyntheticReferenceError(
                f"Missing RL-v2 observability columns: {missing_columns}",
            )

        for action_value, do_predict_value in dataframe[["&-action", "do_predict"]].itertuples(
            index=False,
            name=None,
        ):
            try:
                action = int(action_value)
            except (TypeError, ValueError, OverflowError) as exc:
                raise RLV2SyntheticReferenceError(
                    f"Unsupported desired-position action value: {action_value}",
                ) from exc

            accumulator.record_action(pair, action)
            accepted = do_predict_value == 1
            accumulator.record_do_predict(pair, accepted=accepted)
            if accepted:
                accumulator.record_pre_trade_signal(
                    pair,
                    enter_long=action == DesiredPosition.TARGET_LONG.value,
                    exit_long=action == DesiredPosition.TARGET_FLAT.value,
                )

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = (
            (dataframe["do_predict"] == 1)
            & (dataframe["&-action"] == DesiredPosition.TARGET_LONG.value)
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (
            1,
            "freqai_rl_v2_target_long",
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = (dataframe["do_predict"] == 1) & (
            dataframe["&-action"] == DesiredPosition.TARGET_FLAT.value
        )
        dataframe.loc[condition, ["exit_long", "exit_tag"]] = (
            1,
            "freqai_rl_v2_target_flat",
        )
        return dataframe
