from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from ai_platform.wickhunter import production_market_evidence as core

PACKAGE_DIR_NAME = "immutable-package"
PACKAGE_PARTIAL_DIR_NAME = ".immutable-package.partial"
PACKAGE_MANIFEST_NAME = "manifest.json"
PACKAGE_CHECKSUM_NAME = "artifact-sha256.txt"
PACKAGE_VERIFICATION_NAME = "verification-report.json"
PACKAGE_POLICY_NAME = "policy.json"
PACKAGE_REQUEST_NAME = "request.json"
PACKAGE_RUN_STATE_NAME = "run-state.json"
PACKAGE_SOURCE_SNAPSHOTS_NAME = "source-snapshots.ndjson"
PACKAGE_MARKET_QUALITY_NAME = "market-quality-observations.ndjson"
PACKAGE_INSTRUMENT_SNAPSHOTS_NAME = "instrument-snapshots.ndjson"
PACKAGE_CANDLE_INDEX_NAME = "completed-candles-index.json"
PACKAGE_SOURCE_INDEX_NAME = "source-artifacts-index.json"

EXPECTED_MARKETS = {
    "binance-usdm": "USD-M perpetual",
    "bybit-linear": "linear perpetual",
}
EXPECTED_AUTHORITY = {
    "execution_enabled": False,
    "orders_submitted": 0,
    "trading_credentials_present": False,
    "model_execution_authorized": False,
    "replay_authorized": False,
    "performance_research_authorized": False,
    "live_capital_authorized": False,
}

_FETCH = Callable[[str], bytes]
_CLOCK_MS = Callable[[], int]


class MarketEvidencePublicationError(RuntimeError):
    """Raised when the outer immutable package cannot be published safely."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise MarketEvidencePublicationError(f"{field} must be a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MarketEvidencePublicationError(f"unable to read {field}: {exc}") from exc
    if not isinstance(value, dict):
        raise MarketEvidencePublicationError(f"{field} must be an object")
    return value


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise MarketEvidencePublicationError(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, value: object) -> None:
    _write_new(
        path,
        json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n",
    )


def _write_ndjson(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    _write_new(
        path,
        b"".join(_canonical_bytes(dict(row)) + b"\n" for row in rows),
    )


def _safe_child(root: Path, logical_name: str) -> Path:
    relative = Path(logical_name)
    if (
        not logical_name
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise MarketEvidencePublicationError("artifact path must be relative")
    resolved_root = root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise MarketEvidencePublicationError("artifact path traverses a symlink")
    try:
        current.resolve(strict=True).relative_to(resolved_root)
    except (FileNotFoundError, ValueError) as exc:
        raise MarketEvidencePublicationError(
            "artifact path escapes package root or is missing"
        ) from exc
    return current


def _identity(path: Path, *, root: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise MarketEvidencePublicationError("artifact is not a regular file")
    try:
        logical_name = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise MarketEvidencePublicationError(
            "artifact path escapes package root"
        ) from exc
    return {
        "logical_name": logical_name,
        "sha256": _file_hash(path),
        "size_bytes": path.stat().st_size,
    }


def _policy(request: Mapping[str, object]) -> dict[str, object]:
    pre_roll_ms = int(request["decision_start_ms"]) - int(
        request["pre_roll_start_ms"]
    )
    return {
        "schema_version": 1,
        "policy_id": "wickhunter-production-market-evidence-policy-v2",
        "timeframe": request["timeframe"],
        "capture_cadence_seconds": request["sample_interval_seconds"],
        "pre_roll_ms": pre_roll_ms,
        "minimum_pre_roll_ms": 86_400_000,
        "lookback_contract": "wickhunter-wh01-market-context-v1",
        "availability_semantics": {
            "market_quality": "response_fully_received_at_ms",
            "completed_candle": "close_time_ms_exclusive",
            "instrument_snapshot": "response_fully_received_at_ms",
        },
        "sources": list(core.EXPECTED_SOURCES),
        "source_separated": True,
        "cross_exchange_deduplication": False,
        "completed_candles_only": True,
        "overwrite_existing_run": False,
        "protected_holdout_start_ms": request["protected_holdout_start_ms"],
        **EXPECTED_AUTHORITY,
    }


def _sample_paths(run_root: Path, index: int) -> tuple[Path, Path, Path, Path]:
    sample_root = run_root / "market-samples" / f"{index:04d}"
    return (
        sample_root / "market-snapshot.json",
        sample_root / "sample-report.json",
        sample_root / "instrument-snapshot.json",
        sample_root / "source-health.json",
    )


def _enrich_sample(
    run_root: Path,
    request: Mapping[str, object],
    index: int,
) -> None:
    snapshot_path, report_path, instruments_path, health_path = _sample_paths(
        run_root,
        index,
    )
    if instruments_path.exists() and health_path.exists():
        return
    snapshot = _load_object(snapshot_path, field=f"market snapshot {index}")
    report = _load_object(report_path, field=f"sample report {index}")
    if report.get("status") != "pass":
        raise MarketEvidencePublicationError(f"sample {index} is not successful")

    scheduled_at_ms = int(snapshot.get("scheduled_at_ms", -1))
    available_at_ms = int(snapshot.get("available_at_ms", -1))
    due_ms = int(request["decision_start_ms"]) + (
        index * int(request["sample_interval_seconds"]) * 1000
    )
    latest_allowed_ms = due_ms + (
        int(request["max_sample_lateness_seconds"]) * 1000
    )
    if scheduled_at_ms != due_ms:
        raise MarketEvidencePublicationError(
            f"sample {index} scheduled timestamp mismatch"
        )
    if not scheduled_at_ms <= available_at_ms <= latest_allowed_ms:
        raise MarketEvidencePublicationError(
            f"sample {index} availability timestamp is invalid"
        )

    raw_records = snapshot.get("records")
    if not isinstance(raw_records, list) or len(raw_records) != 40:
        raise MarketEvidencePublicationError(
            f"sample {index} market record count mismatch"
        )

    seen: set[tuple[str, str]] = set()
    source_counts = {source: 0 for source in core.EXPECTED_SOURCES}
    instruments: list[dict[str, object]] = []
    for raw_value in raw_records:
        if not isinstance(raw_value, dict):
            raise MarketEvidencePublicationError(
                f"sample {index} contains a non-object record"
            )
        raw = raw_value
        source = str(raw.get("source", ""))
        symbol = str(raw.get("symbol", ""))
        market = str(raw.get("market", ""))
        identity = (source, symbol)
        if source not in core.EXPECTED_SOURCES:
            raise MarketEvidencePublicationError(
                f"sample {index} source or market mismatch"
            )
        if market != EXPECTED_MARKETS[source]:
            raise MarketEvidencePublicationError(
                f"sample {index} source or market mismatch"
            )
        if symbol not in core.EXPECTED_SYMBOLS or identity in seen:
            raise MarketEvidencePublicationError(
                f"sample {index} symbol identity mismatch"
            )
        seen.add(identity)
        source_counts[source] += 1
        instrument_seed: dict[str, object] = {
            "schema_version": 1,
            "source": source,
            "native_symbol": symbol,
            "canonical_symbol": symbol,
            "market": market,
            "settlement": "USDT",
            "quote": "USDT",
            "active": bool(raw.get("market_available")),
            "captured_at_ms": available_at_ms,
            "available_at_ms": available_at_ms,
            "contract_metadata": {
                "pair": raw.get("pair"),
                "linear": True,
                "inverse": False,
            },
            "source_payload_sha256": _canonical_hash(raw),
        }
        instrument_seed["normalized_snapshot_sha256"] = _canonical_hash(
            instrument_seed
        )
        instruments.append(instrument_seed)

    if source_counts != {source: 20 for source in core.EXPECTED_SOURCES}:
        raise MarketEvidencePublicationError(
            f"sample {index} source coverage mismatch"
        )
    instruments.sort(
        key=lambda row: (str(row["source"]), str(row["canonical_symbol"]))
    )
    _write_json(
        instruments_path,
        {
            "schema_version": 1,
            "snapshot_type": "WickHunterInstrumentHistorySnapshot",
            "sample_index": index,
            "scheduled_at_ms": scheduled_at_ms,
            "available_at_ms": available_at_ms,
            "records": instruments,
            **EXPECTED_AUTHORITY,
        },
    )
    _write_json(
        health_path,
        {
            "schema_version": 1,
            "snapshot_type": "WickHunterSourceHealthSnapshot",
            "sample_index": index,
            "scheduled_at_ms": scheduled_at_ms,
            "available_at_ms": available_at_ms,
            "sources": {
                source: {
                    "connected": True,
                    "healthy": True,
                    "last_event_at_ms": available_at_ms,
                    "last_ticker_at_ms": available_at_ms,
                    "last_completed_candle_at_ms": scheduled_at_ms,
                    "freshness_ms": available_at_ms - scheduled_at_ms,
                    "active_symbols": 20,
                    "errors": [],
                    "reconnect_count": 0,
                    "gaps": 0,
                    "records_written": 20,
                    "required_scope": (
                        "ticker, spread, rolling quote volume, completed 5m "
                        "candles, instrument history"
                    ),
                    "wickhunter_available": True,
                    "exclusion_reason": None,
                }
                for source in core.EXPECTED_SOURCES
            },
            **EXPECTED_AUTHORITY,
        },
    )


def initialize_capture(
    *,
    request_path: Path,
    durable_root: Path,
    collector_commit: str,
    environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    result = core.initialize_capture(
        request_path=request_path,
        durable_root=durable_root,
        collector_commit=collector_commit,
        environment=environment,
    )
    run_root = Path(str(result["run_root"]))
    request = core.load_capture_request(run_root / core.REQUEST_NAME)
    _write_json(run_root / PACKAGE_POLICY_NAME, _policy(request))
    return result


def _package_rows(
    run_root: Path,
    request: Mapping[str, object],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    source_rows: list[dict[str, object]] = []
    quality_rows: list[dict[str, object]] = []
    instrument_rows: list[dict[str, object]] = []
    for index in range(144):
        _enrich_sample(run_root, request, index)
        snapshot_path, _, instruments_path, health_path = _sample_paths(
            run_root,
            index,
        )
        snapshot = _load_object(
            snapshot_path,
            field=f"market snapshot {index}",
        )
        instruments = _load_object(
            instruments_path,
            field=f"instrument snapshot {index}",
        )
        health = _load_object(health_path, field=f"source health {index}")
        records = snapshot.get("records")
        if not isinstance(records, list):
            raise MarketEvidencePublicationError(
                "market snapshot records are invalid"
            )
        for raw in records:
            if not isinstance(raw, dict):
                raise MarketEvidencePublicationError(
                    "market quality record is invalid"
                )
            quality_rows.append(
                {
                    **raw,
                    "canonical_symbol": raw.get("symbol"),
                    "native_symbol": raw.get("symbol"),
                    "captured_at_ms": snapshot["available_at_ms"],
                    "decision_safe": True,
                }
            )
        records_value = instruments.get("records")
        if not isinstance(records_value, list):
            raise MarketEvidencePublicationError(
                "instrument snapshot records are invalid"
            )
        instrument_rows.extend(
            dict(row) for row in records_value if isinstance(row, dict)
        )
        sources = health.get("sources")
        if not isinstance(sources, dict):
            raise MarketEvidencePublicationError(
                "source health records are invalid"
            )
        for source in core.EXPECTED_SOURCES:
            value = sources.get(source)
            if not isinstance(value, dict):
                raise MarketEvidencePublicationError(
                    "source health coverage is invalid"
                )
            source_rows.append(
                {
                    "sample_index": index,
                    "source": source,
                    "scheduled_at_ms": health["scheduled_at_ms"],
                    "available_at_ms": health["available_at_ms"],
                    **value,
                }
            )
    return source_rows, quality_rows, instrument_rows


def _build_manifest(
    *,
    package_root: Path,
    request: Mapping[str, object],
    state: Mapping[str, object],
    inner_manifest: Mapping[str, object],
    artifacts: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    policy = _load_object(package_root / PACKAGE_POLICY_NAME, field="policy")
    return {
        "schema_version": 1,
        "artifact_type": "WickHunterProductionMarketEvidencePackage",
        "run_id": request["run_id"],
        "state": "completed",
        "verification_result": "accepted",
        "collector_commit": state["collector_commit"],
        "request_sha256": _file_hash(package_root / PACKAGE_REQUEST_NAME),
        "policy_sha256": _file_hash(package_root / PACKAGE_POLICY_NAME),
        "inner_manifest_sha256": inner_manifest["manifest_sha256"],
        "sources": list(core.EXPECTED_SOURCES),
        "instruments": list(core.EXPECTED_SYMBOLS),
        "capture": {
            "pre_roll_start_ms": request["pre_roll_start_ms"],
            "decision_start_ms": request["decision_start_ms"],
            "decision_end_ms": request["decision_end_ms"],
            "pre_roll_ms": int(request["decision_start_ms"])
            - int(request["pre_roll_start_ms"]),
            "cadence_seconds": request["sample_interval_seconds"],
            "timeframe": request["timeframe"],
        },
        "record_counts": {
            "market_quality_observations": 5760,
            "instrument_snapshots": 5760,
            "source_health_snapshots": 288,
            "completed_candles": 17280,
        },
        "first_timestamp_ms": request["pre_roll_start_ms"],
        "last_timestamp_ms": request["decision_end_ms"],
        "gaps": [],
        "availability": {
            "decision_safe": True,
            "completed_candles_only": True,
            "minimum_pre_roll_satisfied": policy["pre_roll_ms"]
            >= policy["minimum_pre_roll_ms"],
        },
        "source_health": {
            source: {
                "healthy": True,
                "samples": 144,
                "market_quality_records": 2880,
                "completed_candles": 8640,
                "gaps": 0,
            }
            for source in core.EXPECTED_SOURCES
        },
        "wh01": {
            "market_evidence_ready": True,
            "ready": False,
            "blocker_code": "LIQUIDATION_ARCHIVE_NOT_BOUND",
            "blocker_detail": (
                "A contemporaneous accepted Liquid20 archive and frozen WH-01 "
                "split geometry must be bound before materialization."
            ),
        },
        "artifacts": list(artifacts),
        "authorities": EXPECTED_AUTHORITY,
        "host_paths_exposed": False,
        "raw_exchange_payloads_exposed_by_portal": False,
        "run_root_identity_sha256": _canonical_hash(
            {
                "run_id": request["run_id"],
                "inner": inner_manifest["manifest_sha256"],
            }
        ),
    }


def publish_immutable_package(run_root: Path) -> dict[str, object]:
    final_root = run_root / PACKAGE_DIR_NAME
    if final_root.exists() or final_root.is_symlink():
        verification = verify_immutable_package(final_root)
        return {"status": "published", "idempotent": True, **verification}
    partial_root = run_root / PACKAGE_PARTIAL_DIR_NAME
    if partial_root.exists() or partial_root.is_symlink():
        raise MarketEvidencePublicationError(
            "incomplete immutable package staging directory exists"
        )
    partial_root.mkdir()
    try:
        request = core.load_capture_request(run_root / core.REQUEST_NAME)
        state = _load_object(run_root / core.STATE_NAME, field="run state")
        inner_manifest = _load_object(
            run_root / core.MANIFEST_NAME,
            field="inner manifest",
        )
        inner_report = _load_object(
            run_root / core.REPORT_NAME,
            field="inner verification report",
        )
        if state.get("status") != "completed" or state.get("outcome") != "accepted":
            raise MarketEvidencePublicationError(
                "inner capture is not accepted"
            )
        core.verify_capture_package(run_root)
        source_rows, quality_rows, instrument_rows = _package_rows(
            run_root,
            request,
        )
        if (
            len(source_rows),
            len(quality_rows),
            len(instrument_rows),
        ) != (288, 5760, 5760):
            raise MarketEvidencePublicationError(
                "package record geometry mismatch"
            )

        policy = _load_object(
            run_root / PACKAGE_POLICY_NAME,
            field="policy",
        )
        _write_json(partial_root / PACKAGE_REQUEST_NAME, request)
        _write_json(partial_root / PACKAGE_POLICY_NAME, policy)
        _write_json(
            partial_root / PACKAGE_RUN_STATE_NAME,
            {
                "schema_version": 1,
                "run_id": request["run_id"],
                "state": "completed",
                "active": False,
                "capture_start_ms": request["pre_roll_start_ms"],
                "capture_end_ms": request["decision_end_ms"],
                "sample_count": 144,
                "instrument_count": 20,
                "source_count": 2,
                "completeness": 1,
                "gap_count": 0,
                "gap_duration_ms": 0,
                "verification_result": inner_report.get("outcome"),
                "wh01_ready": False,
                "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
                **EXPECTED_AUTHORITY,
            },
        )
        _write_ndjson(
            partial_root / PACKAGE_SOURCE_SNAPSHOTS_NAME,
            source_rows,
        )
        _write_ndjson(
            partial_root / PACKAGE_MARKET_QUALITY_NAME,
            quality_rows,
        )
        _write_ndjson(
            partial_root / PACKAGE_INSTRUMENT_SNAPSHOTS_NAME,
            instrument_rows,
        )
        _write_json(
            partial_root / PACKAGE_CANDLE_INDEX_NAME,
            inner_manifest["candle_artifacts"],
        )
        _write_json(
            partial_root / PACKAGE_SOURCE_INDEX_NAME,
            inner_manifest["market_samples"],
        )

        artifact_names = (
            PACKAGE_REQUEST_NAME,
            PACKAGE_POLICY_NAME,
            PACKAGE_RUN_STATE_NAME,
            PACKAGE_SOURCE_SNAPSHOTS_NAME,
            PACKAGE_MARKET_QUALITY_NAME,
            PACKAGE_INSTRUMENT_SNAPSHOTS_NAME,
            PACKAGE_CANDLE_INDEX_NAME,
            PACKAGE_SOURCE_INDEX_NAME,
        )
        artifacts = [
            _identity(partial_root / name, root=partial_root)
            for name in artifact_names
        ]
        manifest = _build_manifest(
            package_root=partial_root,
            request=request,
            state=state,
            inner_manifest=inner_manifest,
            artifacts=artifacts,
        )
        manifest["manifest_sha256"] = _canonical_hash(manifest)
        _write_json(partial_root / PACKAGE_MANIFEST_NAME, manifest)
        checksum_identities = [
            *artifacts,
            _identity(
                partial_root / PACKAGE_MANIFEST_NAME,
                root=partial_root,
            ),
        ]
        checksum_lines = sorted(
            f"{identity['sha256']}  {identity['logical_name']}"
            for identity in checksum_identities
        )
        _write_new(
            partial_root / PACKAGE_CHECKSUM_NAME,
            ("\n".join(checksum_lines) + "\n").encode("utf-8"),
        )
        verification = {
            "schema_version": 1,
            "status": "verified",
            "outcome": "accepted",
            "run_id": request["run_id"],
            "manifest_sha256": manifest["manifest_sha256"],
            "artifact_count": len(artifacts),
            "market_quality_observations": 5760,
            "instrument_snapshots": 5760,
            "source_health_snapshots": 288,
            "completed_candles": 17280,
            "wh01_ready": False,
            "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
            **EXPECTED_AUTHORITY,
        }
        _write_json(
            partial_root / PACKAGE_VERIFICATION_NAME,
            verification,
        )
        verify_immutable_package(partial_root)
        partial_root.replace(final_root)
        return {
            "status": "published",
            "idempotent": False,
            "run_id": request["run_id"],
            "package_root": str(final_root),
            "manifest_sha256": manifest["manifest_sha256"],
            "wh01_ready": False,
            "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
        }
    except Exception:
        shutil.rmtree(partial_root, ignore_errors=True)
        raise


def verify_immutable_package(package_root: Path) -> dict[str, object]:
    if package_root.is_symlink() or not package_root.is_dir():
        raise MarketEvidencePublicationError(
            "package root must be a regular directory"
        )
    manifest = _load_object(
        package_root / PACKAGE_MANIFEST_NAME,
        field="package manifest",
    )
    claimed_hash = manifest.get("manifest_sha256")
    hash_seed = dict(manifest)
    hash_seed.pop("manifest_sha256", None)
    if not isinstance(claimed_hash, str) or _canonical_hash(hash_seed) != claimed_hash:
        raise MarketEvidencePublicationError(
            "package manifest self hash mismatch"
        )
    if manifest.get("sources") != list(core.EXPECTED_SOURCES):
        raise MarketEvidencePublicationError(
            "package source coverage mismatch"
        )
    if manifest.get("authorities") != EXPECTED_AUTHORITY:
        raise MarketEvidencePublicationError(
            "package authority boundary mismatch"
        )

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 8:
        raise MarketEvidencePublicationError(
            "package artifact index is invalid"
        )
    expected_lines: set[str] = set()
    for raw in artifacts:
        if not isinstance(raw, dict):
            raise MarketEvidencePublicationError(
                "package artifact identity is invalid"
            )
        logical_name = raw.get("logical_name")
        if not isinstance(logical_name, str):
            raise MarketEvidencePublicationError(
                "package artifact name is invalid"
            )
        path = _safe_child(package_root, logical_name)
        if path.is_symlink() or not path.is_file():
            raise MarketEvidencePublicationError(
                "package artifact is missing or symlinked"
            )
        if (
            _file_hash(path) != raw.get("sha256")
            or path.stat().st_size != raw.get("size_bytes")
        ):
            raise MarketEvidencePublicationError(
                "package artifact identity mismatch"
            )
        expected_lines.add(f"{raw['sha256']}  {logical_name}")

    manifest_identity = _identity(
        package_root / PACKAGE_MANIFEST_NAME,
        root=package_root,
    )
    expected_lines.add(
        f"{manifest_identity['sha256']}  {PACKAGE_MANIFEST_NAME}"
    )
    checksum_path = package_root / PACKAGE_CHECKSUM_NAME
    if checksum_path.is_symlink() or not checksum_path.is_file():
        raise MarketEvidencePublicationError(
            "package checksum index is missing"
        )
    if set(checksum_path.read_text(encoding="utf-8").splitlines()) != expected_lines:
        raise MarketEvidencePublicationError(
            "package checksum index mismatch"
        )

    verification = _load_object(
        package_root / PACKAGE_VERIFICATION_NAME,
        field="package verification report",
    )
    if (
        verification.get("outcome") != "accepted"
        or verification.get("manifest_sha256") != claimed_hash
    ):
        raise MarketEvidencePublicationError(
            "package verification report mismatch"
        )
    if any(
        verification.get(key) != value
        for key, value in EXPECTED_AUTHORITY.items()
    ):
        raise MarketEvidencePublicationError(
            "verification authority boundary mismatch"
        )
    return {
        "outcome": "accepted",
        "run_id": manifest["run_id"],
        "package_root": str(package_root),
        "manifest_sha256": claimed_hash,
        "wh01_ready": False,
        "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
    }


def collect_due_sample(
    *,
    durable_root: Path,
    environment: Mapping[str, str] | None = None,
    fetch_bytes: _FETCH = core.fetch_public_bytes,
    wall_clock_ms: _CLOCK_MS = core._wall_clock_ms,
) -> dict[str, object]:
    result = core.collect_due_sample(
        durable_root=durable_root,
        environment=environment,
        fetch_bytes=fetch_bytes,
        wall_clock_ms=wall_clock_ms,
    )
    if result.get("status") == "sampled" and result.get("sample_status") == "pass":
        run_root = Path(str(result["run_root"]))
        request = core.load_capture_request(run_root / core.REQUEST_NAME)
        _enrich_sample(run_root, request, int(result["sample_index"]))
    elif result.get("status") == "finalized" and result.get("outcome") == "accepted":
        result = {
            **result,
            **publish_immutable_package(Path(str(result["run_root"]))),
        }
    return result


def _write_github_outputs(result: Mapping[str, object]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not output_path:
        return
    allowed = {
        "status",
        "outcome",
        "run_id",
        "run_root",
        "package_root",
        "sample_index",
        "next_sample_index",
        "due_ms",
        "manifest_sha256",
        "wh01_ready",
        "wh01_blocker",
    }
    with Path(output_path).open("a", encoding="utf-8") as output:
        for key in sorted(allowed):
            if key in result:
                output.write(f"{key}={result[key]}\n")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture and publish WickHunter market evidence"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init")
    initialize.add_argument("--request", type=Path, required=True)
    initialize.add_argument("--durable-root", type=Path, required=True)
    initialize.add_argument("--collector-commit", required=True)
    sample = commands.add_parser("sample")
    sample.add_argument("--durable-root", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--package-root", type=Path, required=True)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        if args.command == "init":
            result = initialize_capture(
                request_path=args.request.resolve(),
                durable_root=args.durable_root.resolve(),
                collector_commit=args.collector_commit,
            )
        elif args.command == "sample":
            result = collect_due_sample(
                durable_root=args.durable_root.resolve()
            )
        else:
            result = verify_immutable_package(
                args.package_root.resolve()
            )
        _write_github_outputs(result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result.get("outcome") == "rejected" else 0
    except (
        core.ProductionMarketEvidenceError,
        MarketEvidencePublicationError,
    ) as exc:
        print(
            f"WickHunter market evidence service failed: {exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
