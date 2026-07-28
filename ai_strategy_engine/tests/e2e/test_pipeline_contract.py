from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from strategy_engine.domain.models import FeatureRecord, Provenance
from strategy_engine.validation.leakage import assert_features_available


def test_feature_can_be_used_only_after_available_at() -> None:
    decision_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    feature = FeatureRecord(
        feature_id="supertrend_direction.v1",
        feature_version="1",
        symbol="BTC/USDT:USDT",
        timeframe="5m",
        event_time=decision_time,
        detected_at=decision_time,
        available_at=decision_time,
        value=1,
        is_confirmed=True,
        source="feature-engine",
        idempotency_key="feature:supertrend:2026-01-01T12:00:00Z",
        code_version=hashlib.sha256(b"code").hexdigest(),
        data_version=hashlib.sha256(b"data").hexdigest(),
        configuration_hash=hashlib.sha256(b"configuration").hexdigest(),
        provenance=Provenance(
            producer="feature-engine",
            source_event_id="market-bar:1",
            details={"lineage_complete": True, "future_shift": 0},
        ),
    )

    assert assert_features_available([feature], decision_time) == (feature,)
