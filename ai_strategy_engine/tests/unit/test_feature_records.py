from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest

from strategy_engine.features.records import make_confirmed_htf_record
from strategy_engine.validation.leakage import (
    LeakageError,
    LeakageReason,
    assert_features_available,
)

CODE = hashlib.sha256(b"code").hexdigest()
DATA = hashlib.sha256(b"data").hexdigest()
CONFIG = hashlib.sha256(b"config").hexdigest()
OPEN = datetime(2026, 7, 28, 10, 0, tzinfo=UTC)


def _htf(decision_time: datetime):
    return make_confirmed_htf_record(
        feature_id="supertrend_direction.v1",
        symbol="BTC/USDT",
        timeframe="1h",
        bar_open_time=OPEN,
        bar_duration=timedelta(hours=1),
        processing_latency=timedelta(seconds=1),
        decision_time=decision_time,
        value={"value": 1, "direction": 1},
        source="test-htf",
        idempotency_key="htf:test",
        code_version=CODE,
        data_version=DATA,
        configuration_hash=CONFIG,
        producer="test",
        source_event_id="bar:test",
    )


def test_htf_is_unconfirmed_before_bar_close() -> None:
    record = _htf(OPEN + timedelta(minutes=59, seconds=59))
    assert not record.is_confirmed
    with pytest.raises(LeakageError) as captured:
        assert_features_available((record,), OPEN + timedelta(minutes=59, seconds=59))
    assert captured.value.reason_code is LeakageReason.FEATURE_AFTER_DECISION


def test_htf_is_not_available_during_processing_latency() -> None:
    record = _htf(OPEN + timedelta(hours=1))
    assert record.is_confirmed
    with pytest.raises(LeakageError) as captured:
        assert_features_available((record,), OPEN + timedelta(hours=1))
    assert captured.value.reason_code is LeakageReason.FEATURE_AFTER_DECISION


def test_htf_is_usable_only_after_close_and_latency() -> None:
    decision_time = OPEN + timedelta(hours=1, seconds=1)
    record = _htf(decision_time)
    assert record.is_confirmed
    assert assert_features_available((record,), decision_time) == (record,)
