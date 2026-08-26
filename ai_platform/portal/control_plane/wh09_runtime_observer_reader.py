from __future__ import annotations

from decimal import Decimal, InvalidOperation
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


WH09_MAX_VALIDATED_DECISION_FILES = 10_000


class Wh09ObserverRuntimeEvidenceReader(Wh09RuntimeEvidenceReader):
    """Read WH09 Portal evidence without making an unbounded content scan.

    Aggregate decision truth remains bound to the self-hashed telemetry document.  For journals
    within the bounded validation budget, every immutable decision record is fully validated and
    the latest record is exposed.  Once the journal exceeds that budget, the observer deliberately
    omits ``latest_decision`` instead of guessing from mutable filesystem ordering; aggregate counts
    and all frozen/zero-authority invariants remain available from canonical telemetry.
    """

    def _latest_decision(
        self,
        decisions_root: Path,
        identity: dict[str, Any],
    ) -> Wh09LatestDecision | None:
        if decisions_root.is_symlink() or not decisions_root.is_dir():
            return None

        paths: list[Path] = []
        overflow = False
        try:
            for path in decisions_root.iterdir():
                if path.suffix != ".json":
                    continue
                if path.is_symlink() or not path.is_file():
                    raise Wh09RuntimeEvidenceError(
                        "WH09 decision evidence entry is not a regular file"
                    )
                if len(paths) < WH09_MAX_VALIDATED_DECISION_FILES:
                    paths.append(path)
                else:
                    overflow = True
        except OSError as exc:
            raise Wh09RuntimeEvidenceError("WH09 decision evidence inventory is unreadable") from exc

        if overflow:
            return None

        latest: tuple[int, dict[str, Any]] | None = None
        for path in paths:
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
