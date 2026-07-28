from datetime import datetime, timezone

from strategy_engine.domain.models import FeatureRecord
from strategy_engine.validation.leakage import assert_features_available


def test_feature_can_be_used_only_after_available_at() -> None:
    t = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    feature = FeatureRecord(
        feature_id="supertrend_direction.v1",
        symbol="BTC/USDT:USDT",
        timeframe="5m",
        event_time=t,
        detected_at=t,
        available_at=t,
        value=1,
        is_confirmed=True,
        source="feature-engine",
        code_version="sha",
        data_version="data-sha",
    )
    assert_features_available([feature], t)
