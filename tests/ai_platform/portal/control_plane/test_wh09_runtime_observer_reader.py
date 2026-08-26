from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_platform.portal.control_plane.wh09_runtime import Wh09RuntimeEvidenceError
from ai_platform.portal.control_plane.wh09_runtime_observer_reader import (
    WH09_MAX_VALIDATED_DECISION_FILES,
    Wh09ObserverRuntimeEvidenceReader,
)
from ai_platform.wickhunter.canonical import canonical_sha256


RUN_ID = "1" * 64
ZERO_AUTHORITY = {
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}


def _decision(index: int) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "wickhunter-production-research-decision-v1",
        "decision_id": f"{index:064x}",
        "run_id": RUN_ID,
        "final_decision": "NO_TRADE",
        "status": "abstained",
        "symbol": "BTCUSDT",
        "calibrated_confidence": "0.55",
        "no_trade_confidence": "0.60",
        "observed_at_ms": 1_800_000_000_000 + index,
        **ZERO_AUTHORITY,
    }
    payload["record_sha256"] = canonical_sha256(payload)
    return payload


def _write_decision(path: Path, index: int) -> None:
    path.write_text(json.dumps(_decision(index), sort_keys=True), encoding="utf-8")


def test_observer_reader_omits_latest_instead_of_failing_above_validation_budget(
    tmp_path: Path,
) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()

    # The production journal can exceed 10k immutable records. Aggregate truth is supplied by
    # self-hashed telemetry, so the observer must not parse unbounded history or guess a latest
    # record from mutable directory metadata.
    for index in range(WH09_MAX_VALIDATED_DECISION_FILES + 1):
        (decisions / f"{index:064x}.json").touch()

    latest = Wh09ObserverRuntimeEvidenceReader(tmp_path)._latest_decision(
        decisions, {"run_id": RUN_ID}
    )

    assert latest is None


def test_observer_reader_still_fully_validates_bounded_history(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    _write_decision(decisions / "1.json", 1)
    _write_decision(decisions / "2.json", 2)

    latest = Wh09ObserverRuntimeEvidenceReader(tmp_path)._latest_decision(
        decisions, {"run_id": RUN_ID}
    )

    assert latest is not None
    assert latest.observed_at_ms == 1_800_000_000_002
    assert latest.record_sha256 == _decision(2)["record_sha256"]


def test_observer_reader_fails_closed_on_tampered_bounded_candidate(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    _write_decision(decisions / "1.json", 1)

    tampered = decisions / "2.json"
    payload = _decision(2)
    payload["execution_enabled"] = True
    tampered.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    with pytest.raises(Wh09RuntimeEvidenceError):
        Wh09ObserverRuntimeEvidenceReader(tmp_path)._latest_decision(decisions, {"run_id": RUN_ID})


def test_observer_reader_rejects_json_symlink(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    target = decisions / "target.txt"
    target.write_text("{}", encoding="utf-8")
    (decisions / "decision.json").symlink_to(target)

    with pytest.raises(Wh09RuntimeEvidenceError, match="regular file"):
        Wh09ObserverRuntimeEvidenceReader(tmp_path)._latest_decision(decisions, {"run_id": RUN_ID})
