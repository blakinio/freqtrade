from __future__ import annotations

from datetime import datetime
from typing import Iterable

from strategy_engine.domain.models import FeatureRecord


class LeakageError(ValueError):
    pass


def assert_features_available(
    features: Iterable[FeatureRecord],
    decision_time: datetime,
) -> None:
    for feature in features:
        if feature.available_at > decision_time:
            raise LeakageError(
                f"{feature.feature_id} available at {feature.available_at.isoformat()} "
                f"after decision_time {decision_time.isoformat()}"
            )
        if not feature.is_confirmed:
            raise LeakageError(f"{feature.feature_id} is not confirmed")


def assert_replay_stable(
    before: list[tuple[str, str, object]],
    after: list[tuple[str, str, object]],
) -> None:
    if before != after[: len(before)]:
        raise LeakageError("Historical feature output changed after appending future data")
