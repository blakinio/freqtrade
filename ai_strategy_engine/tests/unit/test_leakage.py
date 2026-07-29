from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest

from strategy_engine.domain.models import FeatureRecord, Provenance
from strategy_engine.validation.leakage import (
    LeakageContext,
    LeakageError,
    LeakageReason,
    assert_features_available,
    assert_replay_stable,
)

NOW = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
HASH_A = hashlib.sha256(b"a").hexdigest()
HASH_B = hashlib.sha256(b"b").hexdigest()
HASH_C = hashlib.sha256(b"c").hexdigest()


def _record(
    feature_id: str = "squeeze_ratio.v1",
    *,
    available_at: datetime = NOW,
    is_confirmed: bool = True,
    data_version: str = HASH_B,
    code_version: str = HASH_A,
    configuration_hash: str = HASH_C,
    details: dict[str, object] | None = None,
) -> FeatureRecord:
    provenance_details: dict[str, object] = {
        "lineage_complete": True,
        "future_shift": 0,
    }
    provenance_details.update(details or {})
    return FeatureRecord.model_validate(
        {
            "feature_id": feature_id,
            "feature_version": "1",
            "symbol": "BTC/USDT",
            "timeframe": "5m",
            "event_time": NOW - timedelta(minutes=5),
            "detected_at": NOW - timedelta(seconds=1),
            "available_at": available_at,
            "value": 1,
            "source": "test",
            "is_confirmed": is_confirmed,
            "idempotency_key": f"feature:{feature_id}:{available_at.isoformat()}",
            "code_version": code_version,
            "data_version": data_version,
            "configuration_hash": configuration_hash,
            "provenance": {
                "producer": "test",
                "source_event_id": "event:test",
                "details": provenance_details,
            },
        }
    )


def _assert_reason(
    expected: LeakageReason,
    records: tuple[FeatureRecord, ...],
    *,
    context: LeakageContext | None = None,
) -> None:
    with pytest.raises(LeakageError) as captured:
        assert_features_available(records, NOW, context=context)
    assert captured.value.reason_code is expected


def test_available_at_must_not_follow_decision_time() -> None:
    _assert_reason(
        LeakageReason.FEATURE_AFTER_DECISION,
        (_record(available_at=NOW + timedelta(microseconds=1)),),
    )


def test_unconfirmed_feature_is_rejected() -> None:
    _assert_reason(LeakageReason.UNCONFIRMED_FEATURE, (_record(is_confirmed=False),))


def test_pivot_before_confirmation_is_rejected() -> None:
    _assert_reason(
        LeakageReason.PIVOT_BEFORE_CONFIRMATION,
        (_record("confirmed_pivot.v1", details={"pivot_confirmed": False}),),
    )


def test_unclosed_htf_bar_is_rejected() -> None:
    _assert_reason(
        LeakageReason.HTF_BAR_NOT_CLOSED,
        (
            _record(
                details={
                    "is_htf": True,
                    "bar_closed": False,
                    "htf_close_time": (NOW + timedelta(hours=1)).isoformat(),
                }
            ),
        ),
    )


def test_future_shift_is_rejected() -> None:
    _assert_reason(LeakageReason.FUTURE_SHIFT, (_record(details={"future_shift": 1}),))


def test_target_leakage_is_rejected() -> None:
    _assert_reason(LeakageReason.TARGET_LEAKAGE, (_record(details={"is_target": True}),))


def test_unavailable_revision_is_rejected() -> None:
    _assert_reason(
        LeakageReason.REVISED_DATA_NOT_POINT_IN_TIME,
        (
            _record(
                details={
                    "is_revised": True,
                    "revision_available_at": (NOW + timedelta(minutes=1)).isoformat(),
                }
            ),
        ),
    )


def test_final_holdout_reuse_is_rejected() -> None:
    _assert_reason(
        LeakageReason.FINAL_HOLDOUT_REUSED,
        (_record(),),
        context=LeakageContext(decision_time=NOW, final_holdout_reused=True),
    )


def test_inconsistent_data_versions_are_rejected() -> None:
    _assert_reason(
        LeakageReason.DATA_VERSION_MISMATCH,
        (_record(), _record("supertrend_direction.v1", data_version=HASH_A)),
    )


def test_inconsistent_code_versions_are_rejected() -> None:
    _assert_reason(
        LeakageReason.CODE_VERSION_MISMATCH,
        (_record(), _record("supertrend_direction.v1", code_version=HASH_B)),
    )


def test_inconsistent_configuration_hashes_are_rejected() -> None:
    _assert_reason(
        LeakageReason.CONFIGURATION_HASH_MISMATCH,
        (_record(), _record("supertrend_direction.v1", configuration_hash=HASH_A)),
    )


def test_missing_provenance_is_rejected() -> None:
    record = _record()
    invalid_provenance = Provenance.model_construct(
        producer="",
        source_event_id="",
        lineage=(),
        details={"lineage_complete": True, "future_shift": 0},
    )
    invalid = record.model_copy(update={"provenance": invalid_provenance})
    _assert_reason(LeakageReason.MISSING_PROVENANCE, (invalid,))


def test_valid_point_in_time_records_are_returned() -> None:
    pivot = _record("confirmed_pivot.v1", details={"pivot_confirmed": True})
    assert assert_features_available((_record(), pivot), NOW) == (_record(), pivot)


def test_replay_must_not_change_historical_output() -> None:
    with pytest.raises(LeakageError) as captured:
        assert_replay_stable([("a", "1", 1)], [("a", "1", 2)])
    assert captured.value.reason_code is LeakageReason.REPLAY_CHANGED_HISTORY
