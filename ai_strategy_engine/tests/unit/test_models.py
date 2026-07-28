from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from strategy_engine.domain.models import FeatureRecord


def test_feature_timestamp_order_is_enforced() -> None:
    event = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        FeatureRecord(
            feature_id="x.v1",
            symbol="BTC/USDT",
            timeframe="5m",
            event_time=event,
            detected_at=event - timedelta(seconds=1),
            available_at=event,
            value=1,
            is_confirmed=True,
            source="test",
            code_version="a",
            data_version="b",
        )


def test_timezone_must_be_utc() -> None:
    naive = datetime(2026, 1, 1)
    with pytest.raises(ValidationError):
        FeatureRecord(
            feature_id="x.v1",
            symbol="BTC/USDT",
            timeframe="5m",
            event_time=naive,
            detected_at=naive,
            available_at=naive,
            value=1,
            is_confirmed=True,
            source="test",
            code_version="a",
            data_version="b",
        )
