from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pandas import DataFrame

from ai_platform.scripts.rl_v2_action_observability import (
    RLV2ActionObservabilityError,
    RLV2ActionObservabilityRecorder,
)
from ai_platform.strategies.AiDesiredPositionRLLifecycleAlignedResearchStrategy import (
    AiDesiredPositionRLLifecycleAlignedResearchStrategy,
)


_ENABLED_ENV = "RL_V2_ACTION_OBSERVABILITY_ENABLED"
_OUTPUT_DIR_ENV = "RL_V2_ACTION_OBSERVABILITY_OUTPUT_DIR"
_METADATA_ENV = {
    "git_commit": "RL_V2_ACTION_OBSERVABILITY_GIT_COMMIT",
    "strategy_sha256": "RL_V2_ACTION_OBSERVABILITY_STRATEGY_SHA256",
    "freqai_model": "RL_V2_ACTION_OBSERVABILITY_MODEL_NAME",
    "freqai_model_sha256": "RL_V2_ACTION_OBSERVABILITY_MODEL_SHA256",
    "config_sha256": "RL_V2_ACTION_OBSERVABILITY_CONFIG_SHA256",
    "freqai_identifier": "RL_V2_ACTION_OBSERVABILITY_IDENTIFIER",
    "seed": "RL_V2_ACTION_OBSERVABILITY_SEED",
    "timerange": "RL_V2_ACTION_OBSERVABILITY_TIMERANGE",
    "timeframe": "RL_V2_ACTION_OBSERVABILITY_TIMEFRAME",
}


class AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy(
    AiDesiredPositionRLLifecycleAlignedResearchStrategy,
):
    """Research-only lifecycle strategy with request-gated action telemetry."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        enabled = os.environ.get(_ENABLED_ENV) == "1"
        self._action_observability_recorder = RLV2ActionObservabilityRecorder(enabled=enabled)
        self._action_observability_pairs: set[str] = set()

    @property
    def action_observability_enabled(self) -> bool:
        """Expose the request-gated recorder state for focused validation."""
        return self._action_observability_recorder.enabled

    def _action_observability_metadata(self) -> dict[str, Any]:
        values: dict[str, str] = {}
        for field, environment_name in _METADATA_ENV.items():
            value = os.environ.get(environment_name)
            if value is None or not value.strip():
                raise RLV2ActionObservabilityError(
                    f"Missing action-observability runtime metadata: {environment_name}"
                )
            values[field] = value.strip()
        try:
            seed = int(values["seed"])
        except ValueError as exc:
            raise RLV2ActionObservabilityError(
                "RL_V2_ACTION_OBSERVABILITY_SEED must be an integer"
            ) from exc
        pairs = sorted({str(row["pair"]) for row in self._action_observability_recorder.rows})
        return {
            "schema_version": 1,
            "git_commit": values["git_commit"],
            "strategy_name": self.__class__.__name__,
            "strategy_sha256": values["strategy_sha256"],
            "freqai_model": values["freqai_model"],
            "freqai_model_sha256": values["freqai_model_sha256"],
            "config_sha256": values["config_sha256"],
            "freqai_identifier": values["freqai_identifier"],
            "seed": seed,
            "timerange": values["timerange"],
            "timeframe": values["timeframe"],
            "pairs": pairs,
        }

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Evaluate inherited signals, then capture their immutable inference inputs."""
        result = super().populate_exit_trend(dataframe, metadata)
        if not self.action_observability_enabled:
            return result

        pair = metadata.get("pair")
        if not isinstance(pair, str) or not pair.strip() or pair != pair.strip():
            raise RLV2ActionObservabilityError(
                "Enabled action observability requires metadata['pair']"
            )
        if pair in self._action_observability_pairs:
            raise RLV2ActionObservabilityError(
                f"Action observability captured pair more than once: {pair}"
            )

        self._action_observability_recorder.capture_pair_dataframe(pair, result)
        self._action_observability_pairs.add(pair)

        output_dir = os.environ.get(_OUTPUT_DIR_ENV)
        if output_dir is None or not output_dir.strip():
            raise RLV2ActionObservabilityError(
                f"Missing action-observability destination: {_OUTPUT_DIR_ENV}"
            )
        self._action_observability_recorder.write_artifacts(
            Path(output_dir.strip()),
            self._action_observability_metadata(),
        )
        return result
