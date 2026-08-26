from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ai_platform.portal.control_plane.wh09_runtime import Wh09RuntimeEvidenceError
from ai_platform.portal.control_plane.wh09_runtime_observer_reader import (
    WH09_MAX_LATEST_DECISION_CANDIDATES,
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


def _write_decision(path: Path, index: int, *, mtime_ns: int) -> None:
    path.write_text(json.dumps(_decision(index), sort_keys=True), encoding="utf-8")
    os.utime(path, ns=(mtime_ns, mtime_ns))


def test_observer_reader_handles_more_than_10000_decisions_with_bounded_latest_window(
    tmp_path: Path,
) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    total = 10_020
    selected_start = total - WH09_MAX_LATEST_DECISION_CANDIDATES

    # Historical immutable entries are intentionally not reparsed by the Portal observer.
    # Their aggregate truth is supplied by self-hashed telemetry; only the newest bounded
    # window is needed to materialize latest_decision for the UI.
    for index in range(selected_start):
        path = decisions / f"{index:064x}.json"
        path.touch()
        os.utime(path, ns=(index + 1, index + 1))

    for index in range(selected_start, total):
        _write_decision(
            decisions / f"{index:064x}.json",
            index,
            mtime_ns=10_000_000_000 + index,
        )

    reader = Wh09ObserverRuntimeEvidenceReader(tmp_path)
    latest = reader._latest_decision(decisions, {"run_id": RUN_ID})

    assert latest is not None
    assert latest.observed_at_ms == 1_800_000_000_000 + total - 1
    assert latest.final_decision == "NO_TRADE"
    assert latest.record_sha256 == _decision(total - 1)["record_sha256"]


def test_observer_reader_fails_closed_on_tampered_newest_candidate(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    valid = decisions / "1.json"
    _write_decision(valid, 1, mtime_ns=1)

    tampered = decisions / "2.json"
    payload = _decision(2)
    payload["execution_enabled"] = True
    tampered.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    os.utime(tampered, ns=(2, 2))

    with pytest.raises(Wh09RuntimeEvidenceError):
        Wh09ObserverRuntimeEvidenceReader(tmp_path)._latest_decision(
            decisions, {"run_id": RUN_ID}
        )


def test_observer_reader_rejects_json_symlink(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    target = decisions / "target.txt"
    target.write_text("{}", encoding="utf-8")
    (decisions / "decision.json").symlink_to(target)

    with pytest.raises(Wh09RuntimeEvidenceError, match="regular file"):
        Wh09ObserverRuntimeEvidenceReader(tmp_path)._latest_decision(
            decisions, {"run_id": RUN_ID}
        )
