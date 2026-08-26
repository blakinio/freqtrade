from __future__ import annotations

from decimal import Decimal, InvalidOperation
from heapq import heappush, heapreplace
from pathlib import Path
from typing import Any

from ai_platform.portal.control_plane.wh09_runtime import (
    WH09_DECISION_SCHEMA,
    WH09_FROZEN_NO_TRADE_CONFIDENCE,
    Wh09LatestDecision,
    Wh09RuntimeEvidenceError,
    Wh09RuntimeEvidenceReader,
    _load_object,
    _require_zero_authority,
    _verify_hash,
)


WH09_MAX_LATEST_DECISION_CANDIDATES = 256


class Wh09ObserverRuntimeEvidenceReader(Wh09RuntimeEvidenceReader):
    """Read WH09 Portal evidence without rescanning the complete immutable decision journal.

    Aggregate decision truth remains bound to the self-hashed telemetry document.  The observer
    only needs a latest-decision sample for the UI, so it selects a bounded set of the newest
    immutable decision files by filesystem mtime and then applies the complete schema, authority,
    run-identity and self-hash validation to every selected candidate.
    """

    def _latest_decision(
        self,
        decisions_root: Path,
        identity: dict[str, Any],
    ) -> Wh09LatestDecision | None:
        if decisions_root.is_symlink() or not decisions_root.is_dir():
            return None

        candidates: list[tuple[int, str, Path]] = []
        try:
            for path in decisions_root.iterdir():
                if path.suffix != ".json":
                    continue
                if path.is_symlink() or not path.is_file():
                    raise Wh09RuntimeEvidenceError(
                        "WH09 decision evidence entry is not a regular file"
                    )
                mtime_ns = path.stat().st_mtime_ns
                candidate = (mtime_ns, path.name, path)
                if len(candidates) < WH09_MAX_LATEST_DECISION_CANDIDATES:
                    heappush(candidates, candidate)
                elif candidate[:2] > candidates[0][:2]:
                    heapreplace(candidates, candidate)
        except OSError as exc:
            raise Wh09RuntimeEvidenceError("WH09 decision evidence inventory is unreadable") from exc

        latest: tuple[int, dict[str, Any]] | None = None
        for _, _, path in candidates:
            payload = _load_object(path, label="WH09 decision")
            if payload.get("schema_version") != WH09_DECISION_SCHEMA:
                raise Wh09RuntimeEvidenceError("WH09 decision schema mismatch")
            _require_zero_authority(payload, label="WH09 decision")
            record_hash = _verify_hash(payload, hash_field="record_sha256", label="WH09 decision")
            if payload.get("run_id") != identity.get("run_id"):
                raise Wh09RuntimeEvidenceError("WH09 decision run identity mismatch")
            observed_at_ms = payload.get("observed_at_ms")
            if type(observed_at_ms) is not int or observed_at_ms <= 0:
                raise Wh09RuntimeEvidenceError("WH09 decision timestamp is invalid")
            if latest is None or observed_at_ms > latest[0]:
                latest = (observed_at_ms, {**payload, "record_sha256": record_hash})

        if latest is None:
            return None
        payload = latest[1]
        try:
            threshold = Decimal(str(payload.get("no_trade_confidence")))
        except (InvalidOperation, ValueError) as exc:
            raise Wh09RuntimeEvidenceError("WH09 latest decision threshold is invalid") from exc
        if threshold != WH09_FROZEN_NO_TRADE_CONFIDENCE:
            raise Wh09RuntimeEvidenceError("WH09 latest decision changed no-trade threshold")
        try:
            return Wh09LatestDecision(
                final_decision=str(payload["final_decision"]),
                status=str(payload["status"]),
                symbol=str(payload["symbol"]),
                calibrated_confidence=(
                    None
                    if payload.get("calibrated_confidence") is None
                    else Decimal(str(payload["calibrated_confidence"]))
                ),
                no_trade_confidence=threshold,
                observed_at_ms=int(payload["observed_at_ms"]),
                record_sha256=str(payload["record_sha256"]),
            )
        except (InvalidOperation, KeyError, ValueError) as exc:
            raise Wh09RuntimeEvidenceError("WH09 latest decision payload is invalid") from exc
