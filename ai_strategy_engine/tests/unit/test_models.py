from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from strategy_engine.domain.models import FeatureRecord, Provenance, ShadowDecisionEvidence

HASH_A = hashlib.sha256(b"a").hexdigest()
HASH_B = hashlib.sha256(b"b").hexdigest()
HASH_C = hashlib.sha256(b"c").hexdigest()


def _feature(**overrides: object) -> FeatureRecord:
    event = datetime(2026, 1, 1, tzinfo=timezone.utc)
    values: dict[str, object] = {
        "feature_id": "x.v1",
        "feature_version": "1",
        "symbol": "BTC/USDT",
        "timeframe": "5m",
        "event_time": event,
        "detected_at": event,
        "available_at": event,
        "value": 1,
        "is_confirmed": True,
        "source": "test",
        "idempotency_key": "feature:test",
        "code_version": HASH_A,
        "data_version": HASH_B,
        "configuration_hash": HASH_C,
        "provenance": Provenance(
            producer="test",
            source_event_id="event:test",
            details={"lineage_complete": True, "future_shift": 0},
        ),
    }
    values.update(overrides)
    return FeatureRecord.model_validate(values)


def test_feature_timestamp_order_is_enforced() -> None:
    event = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        _feature(detected_at=event - timedelta(seconds=1))


def test_timezone_must_be_utc() -> None:
    naive = datetime(2026, 1, 1)
    with pytest.raises(ValidationError):
        _feature(event_time=naive, detected_at=naive, available_at=naive)


def test_shadow_evidence_hash_is_self_verifying() -> None:
    decision_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    provenance = Provenance(
        producer="test",
        source_event_id="evidence:test",
        details={"lineage_complete": True, "future_shift": 0},
    )
    evidence = ShadowDecisionEvidence.create(
        evidence_version="1",
        decision_time=decision_time,
        symbol="BTC/USDT",
        timeframe="5m",
        strategy_id="strategy",
        strategy_version="1.0.0",
        feature_records=(_feature(),),
        signal=None,
        risk_outcome="no_signal",
        reason_codes=("NO_SIGNAL",),
        data_hash=HASH_B,
        config_hash=HASH_C,
        code_hash=HASH_A,
        idempotency_key="evidence:test",
        provenance=provenance,
        no_order_submitted=True,
    )
    assert len(evidence.evidence_hash) == 64
    assert ShadowDecisionEvidence.model_validate_json(evidence.canonical_json()) == evidence


def test_shadow_evidence_rejects_modified_hash() -> None:
    decision_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    provenance = Provenance(producer="test", source_event_id="evidence:test")
    with pytest.raises(ValidationError):
        ShadowDecisionEvidence(
            evidence_version="1",
            decision_time=decision_time,
            symbol="BTC/USDT",
            timeframe="5m",
            strategy_id="strategy",
            strategy_version="1.0.0",
            feature_records=(),
            signal=None,
            risk_outcome="rejected",
            reason_codes=("REJECTED",),
            data_hash=HASH_B,
            config_hash=HASH_C,
            code_hash=HASH_A,
            idempotency_key="evidence:test",
            provenance=provenance,
            no_order_submitted=True,
            evidence_hash="0" * 64,
        )
