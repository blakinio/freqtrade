from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from ai_platform.portal.control_plane.wh09_runtime import (
    WH09_EXPECTED_BOT_INSTANCE,
    WH09_EXPECTED_MANIFEST_SHA256,
    WH09_EXPECTED_MODEL_ARTIFACT_SHA256,
    WH09_EXPECTED_MODEL_HASH,
    WH09_EXPECTED_PACKAGE_ID,
    WH09_EXPECTED_PARAMETER_HASH,
    Wh09RuntimeEvidenceError,
    Wh09RuntimeEvidenceReader,
)
from ai_platform.wickhunter.canonical import canonical_sha256


NOW = datetime(2026, 8, 10, 7, 0, tzinfo=UTC)
RUN_ID = "1" * 64
DATASET_HASH = "2" * 64
OPERATOR_COMMIT = "3" * 40
ZERO_AUTHORITY_EVIDENCE = {
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}


def _hashed(payload: dict[str, object], field: str) -> dict[str, object]:
    result = dict(payload)
    result[field] = canonical_sha256(result)
    return result


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _evidence_root(root: Path, *, checked_at: datetime = NOW) -> Path:
    identity = _hashed(
        {
            "schema_version": "wickhunter-production-research-runtime-identity-v1",
            "run_id": RUN_ID,
            "bot_instance": WH09_EXPECTED_BOT_INSTANCE,
            "mode": "shadow",
            "package_id": WH09_EXPECTED_PACKAGE_ID,
            "package_manifest_sha256": WH09_EXPECTED_MANIFEST_SHA256,
            "model_artifact_sha256": WH09_EXPECTED_MODEL_ARTIFACT_SHA256,
            "model_version": "wh09-h900-v1",
            "model_hash": WH09_EXPECTED_MODEL_HASH,
            "parameter_version": "wh09-parameters-v1",
            "parameter_hash": WH09_EXPECTED_PARAMETER_HASH,
            "dataset_hash": DATASET_HASH,
            "model_source_commit": OPERATOR_COMMIT,
            "no_trade_confidence": "0.60",
            "outcome_horizon_ms": 900000,
            **ZERO_AUTHORITY_EVIDENCE,
        },
        "identity_sha256",
    )
    telemetry = _hashed(
        {
            "schema_version": "wickhunter-production-research-telemetry-v1",
            "run_id": RUN_ID,
            "mode": "shadow",
            "model_version": "wh09-h900-v1",
            "model_hash": WH09_EXPECTED_MODEL_HASH,
            "model_artifact_sha256": WH09_EXPECTED_MODEL_ARTIFACT_SHA256,
            "parameter_version": "wh09-parameters-v1",
            "parameter_hash": WH09_EXPECTED_PARAMETER_HASH,
            "dataset_hash": DATASET_HASH,
            "no_trade_confidence": "0.60",
            "outcome_horizon_ms": 900000,
            "operator_commit": OPERATOR_COMMIT,
            "runtime_generation": 7,
            "decision_count": 11,
            "no_trade_count": 11,
            **ZERO_AUTHORITY_EVIDENCE,
        },
        "telemetry_sha256",
    )
    health = _hashed(
        {
            "schema_version": "wickhunter-production-research-runtime-health-v1",
            "status": "healthy",
            "checked_at_ms": int(checked_at.timestamp() * 1000),
            "last_success_at_ms": int(checked_at.timestamp() * 1000),
            "operator_commit": OPERATOR_COMMIT,
            "run_id": RUN_ID,
            "mode": "shadow",
            "generation": 7,
            "runtime_health": "healthy",
            "model_drift": "healthy",
            "data_drift": "healthy",
            "circuit_breaker_active": False,
            "circuit_breaker_reasons": [],
            "error_code": None,
            "model_version": "wh09-h900-v1",
            "model_hash": WH09_EXPECTED_MODEL_HASH,
            "model_artifact_sha256": WH09_EXPECTED_MODEL_ARTIFACT_SHA256,
            "parameter_version": "wh09-parameters-v1",
            "parameter_hash": WH09_EXPECTED_PARAMETER_HASH,
            "dataset_hash": DATASET_HASH,
            "no_trade_confidence": "0.60",
            "outcome_horizon_ms": 900000,
            "telemetry_sha256": telemetry["telemetry_sha256"],
            **ZERO_AUTHORITY_EVIDENCE,
        },
        "health_sha256",
    )
    decision_id = "4" * 64
    decision = _hashed(
        {
            "schema_version": "wickhunter-production-research-decision-v1",
            "decision_id": decision_id,
            "run_id": RUN_ID,
            "final_decision": "NO_TRADE",
            "status": "abstained",
            "symbol": "BTCUSDT",
            "calibrated_confidence": "0.55",
            "no_trade_confidence": "0.60",
            "observed_at_ms": int(checked_at.timestamp() * 1000),
            **ZERO_AUTHORITY_EVIDENCE,
        },
        "record_sha256",
    )
    _write(root / "journal" / "identity.json", identity)
    _write(root / "journal" / "telemetry.json", telemetry)
    _write(root / "journal" / "decisions" / f"{decision_id}.json", decision)
    _write(root / "operator" / "health.json", health)
    return root


def test_reader_exposes_truthful_h900_shadow_zero_authority(tmp_path: Path) -> None:
    reader = Wh09RuntimeEvidenceReader(_evidence_root(tmp_path), clock=lambda: NOW)

    evidence = reader.read()

    assert evidence.candidate_identity == "H900"
    assert evidence.mode.value == "shadow"
    assert evidence.health == "HEALTHY"
    assert evidence.no_trade_confidence == Decimal("0.60")
    assert evidence.outcome_horizon_ms == 900000
    assert evidence.decision_count == 11
    assert evidence.no_trade_count == 11
    assert evidence.latest_decision is not None
    assert evidence.latest_decision.final_decision == "NO_TRADE"
    assert evidence.paper_active is False
    assert evidence.paper_activation_authorized is False
    assert evidence.live_status == "BLOCKED"
    assert evidence.trading_credentials_present is False
    assert evidence.order_adapter_present is False
    assert evidence.execution_enabled is False
    assert type(evidence.orders_submitted) is int and evidence.orders_submitted == 0
    assert evidence.live_capital_authorized is False


def test_reader_marks_valid_but_old_health_stale(tmp_path: Path) -> None:
    old = NOW - timedelta(minutes=11)
    reader = Wh09RuntimeEvidenceReader(_evidence_root(tmp_path, checked_at=old), clock=lambda: NOW)

    assert reader.read().health == "STALE"


def test_reader_fails_closed_when_self_hash_or_identity_is_tampered(tmp_path: Path) -> None:
    root = _evidence_root(tmp_path)
    identity_path = root / "journal" / "identity.json"
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    identity["no_trade_confidence"] = "0.61"
    identity_path.write_text(json.dumps(identity), encoding="utf-8")

    with pytest.raises(Wh09RuntimeEvidenceError):
        Wh09RuntimeEvidenceReader(root, clock=lambda: NOW).read()


def test_reader_fails_closed_when_source_generation_disagrees(tmp_path: Path) -> None:
    root = _evidence_root(tmp_path)
    health_path = root / "operator" / "health.json"
    health = json.loads(health_path.read_text(encoding="utf-8"))
    health.pop("health_sha256")
    health["generation"] = 8
    health["health_sha256"] = canonical_sha256(health)
    health_path.write_text(json.dumps(health), encoding="utf-8")

    with pytest.raises(Wh09RuntimeEvidenceError, match="source generation"):
        Wh09RuntimeEvidenceReader(root, clock=lambda: NOW).read()
