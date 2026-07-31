from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ai_platform.wickhunter import production_market_evidence as v1_core
from ai_platform.wickhunter import production_market_evidence_service as v1_service
from ai_platform.wickhunter import production_market_evidence_v2 as v2


PACKAGE_DIR_NAME = "immutable-package"
PARTIAL_DIR_NAME = ".immutable-package.partial"
MANIFEST_NAME = "manifest.json"
CHECKSUM_NAME = "artifact-sha256.txt"
VERIFICATION_NAME = "verification-report.json"
REQUEST_NAME = "request.json"
STATE_NAME = "run-state.json"
BINDING_NAME = "source-package-binding.json"
LINEAGE_NAME = "geometry-intersection-lineage.json"
SOURCE_ROWS_NAME = "source-snapshots.ndjson"
QUALITY_ROWS_NAME = "market-quality-observations.ndjson"
INSTRUMENT_ROWS_NAME = "instrument-snapshots.ndjson"
CANDLE_INDEX_NAME = "completed-candles-index.json"

TIMEFRAME_MS = 300_000
MINIMUM_PRE_ROLL_MS = 86_400_000
MINIMUM_DECISION_SAMPLES = 120
RUN_ID_PATTERN = re.compile(r"^wickhunter-production-market-evidence-\d{8}-v3-r\d+$")
BASE_SOURCES = tuple(v1_core.EXPECTED_SOURCES)
EXPECTED_SOURCES = tuple(v2.EXPECTED_SOURCES)
EXPECTED_SYMBOLS = tuple(v1_core.EXPECTED_SYMBOLS)


class MarketEvidenceIntersectionError(RuntimeError):
    """Raised when immutable market-evidence packages cannot be intersected safely."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise MarketEvidenceIntersectionError(f"{field} must be an integer")
    try:
        return int(value)
    except ValueError as exc:
        raise MarketEvidenceIntersectionError(f"{field} must be an integer") from exc


def _object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MarketEvidenceIntersectionError(f"{field} must be an object")
    return value


def _sequence(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise MarketEvidenceIntersectionError(f"{field} must be a list")
    return value


def _load_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise MarketEvidenceIntersectionError(f"{field} must be a regular file")
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MarketEvidenceIntersectionError(f"unable to read {field}: {exc}") from exc
    return _object(parsed, field=field)


def _read_ndjson(path: Path, *, field: str) -> list[dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise MarketEvidenceIntersectionError(f"{field} must be a regular file")
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for index, line in enumerate(handle, 1):
                if not line.strip():
                    raise MarketEvidenceIntersectionError(
                        f"{field} contains a blank row at line {index}"
                    )
                rows.append(_object(json.loads(line), field=f"{field} row {index}"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MarketEvidenceIntersectionError(f"unable to read {field}: {exc}") from exc
    return rows


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise MarketEvidenceIntersectionError(f"refusing to overwrite {path}")
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


def _safe_member(root: Path, logical_name: str) -> Path:
    relative = Path(logical_name)
    if (
        not logical_name
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise MarketEvidenceIntersectionError("artifact path must remain relative")
    resolved_root = root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise MarketEvidenceIntersectionError("artifact path traverses a symlink")
    try:
        current.resolve(strict=True).relative_to(resolved_root)
    except (FileNotFoundError, ValueError) as exc:
        raise MarketEvidenceIntersectionError("artifact path escapes immutable root") from exc
    if not current.is_file():
        raise MarketEvidenceIntersectionError("artifact member is not a regular file")
    return current


def _identity(path: Path, *, root: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise MarketEvidenceIntersectionError("artifact is not a regular file")
    try:
        logical_name = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise MarketEvidenceIntersectionError("artifact path escapes package root") from exc
    return {
        "logical_name": logical_name,
        "sha256": _file_hash(path),
        "size_bytes": path.stat().st_size,
    }


def _capture_geometry(manifest: Mapping[str, object]) -> dict[str, int]:
    capture = _object(manifest.get("capture"), field="manifest.capture")
    return {
        "pre_roll_start_ms": _integer(
            capture.get("pre_roll_start_ms"),
            field="pre_roll_start_ms",
        ),
        "decision_start_ms": _integer(
            capture.get("decision_start_ms"),
            field="decision_start_ms",
        ),
        "decision_end_ms": _integer(
            capture.get("decision_end_ms"),
            field="decision_end_ms",
        ),
    }


def _holdout_start(request: Mapping[str, object], *, field: str) -> int:
    return _integer(
        request.get("protected_holdout_start_ms"),
        field=f"{field}.protected_holdout_start_ms",
    )


def derive_common_geometry(
    *,
    base_manifest: Mapping[str, object],
    supplement_manifest: Mapping[str, object],
    base_request: Mapping[str, object],
    supplement_request: Mapping[str, object],
) -> dict[str, int]:
    base = _capture_geometry(base_manifest)
    supplement = _capture_geometry(supplement_manifest)
    if base == supplement:
        raise MarketEvidenceIntersectionError(
            "equal source geometry must use the canonical v2 merge path"
        )
    holdout_start_ms = _holdout_start(base_request, field="base request")
    if _holdout_start(supplement_request, field="supplement request") != holdout_start_ms:
        raise MarketEvidenceIntersectionError("source holdout identities differ")
    geometry = {
        "pre_roll_start_ms": max(
            base["pre_roll_start_ms"],
            supplement["pre_roll_start_ms"],
        ),
        "decision_start_ms": max(
            base["decision_start_ms"],
            supplement["decision_start_ms"],
        ),
        "decision_end_ms": min(
            base["decision_end_ms"],
            supplement["decision_end_ms"],
        ),
        "protected_holdout_start_ms": holdout_start_ms,
    }
    pre_roll_ms = geometry["decision_start_ms"] - geometry["pre_roll_start_ms"]
    decision_ms = geometry["decision_end_ms"] - geometry["decision_start_ms"]
    if pre_roll_ms < MINIMUM_PRE_ROLL_MS:
        raise MarketEvidenceIntersectionError("common pre-roll is shorter than 24 hours")
    if decision_ms < MINIMUM_DECISION_SAMPLES * TIMEFRAME_MS:
        raise MarketEvidenceIntersectionError("common decision interval is too short")
    if geometry["decision_end_ms"] > holdout_start_ms:
        raise MarketEvidenceIntersectionError("common geometry overlaps protected holdout")
    if any(
        geometry[key] % TIMEFRAME_MS
        for key in ("pre_roll_start_ms", "decision_start_ms", "decision_end_ms")
    ):
        raise MarketEvidenceIntersectionError("common geometry is not aligned to 5m")
    return geometry


def _authority_is_safe(manifest: Mapping[str, object], *, field: str) -> None:
    authorities = _object(manifest.get("authorities"), field=f"{field}.authorities")
    if authorities != v2.AUTHORITY:
        raise MarketEvidenceIntersectionError(f"{field} authority boundary mismatch")


def _selected_source_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    start_ms: int,
    end_ms: int,
    expected_sources: set[str],
    field: str,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        source = str(row.get("source", ""))
        scheduled = _integer(row.get("scheduled_at_ms"), field=f"{field}.scheduled_at_ms")
        if start_ms <= scheduled < end_ms:
            if source not in expected_sources:
                raise MarketEvidenceIntersectionError(f"{field} source coverage mismatch")
            selected.append(row)
    selected.sort(
        key=lambda row: (
            _integer(row["scheduled_at_ms"], field="scheduled"),
            str(row["source"]),
        )
    )
    return selected


def _selected_quality_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    start_ms: int,
    end_ms: int,
    expected_sources: set[str],
) -> list[dict[str, Any]]:
    selected = _selected_source_rows(
        rows,
        start_ms=start_ms,
        end_ms=end_ms,
        expected_sources=expected_sources,
        field="market quality",
    )
    selected.sort(
        key=lambda row: (
            _integer(row["scheduled_at_ms"], field="scheduled"),
            str(row["source"]),
            str(row.get("canonical_symbol") or row.get("symbol") or ""),
        )
    )
    return selected


def _selected_instrument_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_keys: set[tuple[str, int]],
    expected_sources: set[str],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        source = str(row.get("source", ""))
        available = _integer(
            row.get("available_at_ms", row.get("captured_at_ms")),
            field="instrument available_at_ms",
        )
        if (source, available) in sample_keys:
            if source not in expected_sources:
                raise MarketEvidenceIntersectionError("instrument source coverage mismatch")
            selected.append(row)
    selected.sort(
        key=lambda row: (
            _integer(
                row.get("available_at_ms", row.get("captured_at_ms")),
                field="instrument available_at_ms",
            ),
            str(row["source"]),
            str(row.get("canonical_symbol") or row.get("native_symbol") or ""),
        )
    )
    return selected


def _candle_artifacts(index: object) -> list[dict[str, Any]]:
    raw = index.get("artifacts") if isinstance(index, dict) else index
    return [_object(item, field="candle artifact") for item in _sequence(raw, field="candle index")]


def _filtered_candle_rows(
    path: Path,
    *,
    source: str,
    symbol: str,
    start_ms: int,
    end_ms: int,
) -> list[dict[str, Any]]:
    rows = _read_ndjson(path, field=f"{source} {symbol} candles")
    selected = [
        row
        for row in rows
        if start_ms <= _integer(row.get("open_time_ms"), field="candle open_time_ms") < end_ms
    ]
    selected.sort(key=lambda row: _integer(row["open_time_ms"], field="candle open_time_ms"))
    expected_times = list(range(start_ms, end_ms, TIMEFRAME_MS))
    actual_times = [
        _integer(row.get("open_time_ms"), field="candle open_time_ms") for row in selected
    ]
    if actual_times != expected_times:
        raise MarketEvidenceIntersectionError(
            f"incomplete common candle coverage for {source} {symbol}"
        )
    for row in selected:
        if row.get("source") != source or str(row.get("symbol", "")).upper() != symbol:
            raise MarketEvidenceIntersectionError("candle source or symbol identity mismatch")
        close_ms = _integer(
            row.get("close_time_ms_exclusive"),
            field="candle close_time_ms_exclusive",
        )
        open_ms = _integer(row.get("open_time_ms"), field="candle open_time_ms")
        if close_ms != open_ms + TIMEFRAME_MS:
            raise MarketEvidenceIntersectionError("candle close boundary mismatch")
    return selected


def _copy_filtered_candles(
    *,
    artifacts: Sequence[Mapping[str, Any]],
    source_root: Path,
    destination_root: Path,
    expected_sources: set[str],
    start_ms: int,
    end_ms: int,
) -> list[dict[str, object]]:
    copied: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for artifact in artifacts:
        source = str(artifact.get("source", ""))
        symbol = str(artifact.get("symbol", "")).upper()
        if source not in expected_sources or symbol not in EXPECTED_SYMBOLS:
            raise MarketEvidenceIntersectionError("candle artifact identity mismatch")
        source_symbol = (source, symbol)
        if source_symbol in seen:
            raise MarketEvidenceIntersectionError("duplicate candle source-symbol identity")
        seen.add(source_symbol)
        normalized = _object(
            artifact.get("normalized_file"),
            field="normalized candle file",
        )
        source_path = _safe_member(source_root, str(normalized.get("logical_name", "")))
        if _file_hash(source_path) != normalized.get("sha256"):
            raise MarketEvidenceIntersectionError("source candle hash mismatch")
        rows = _filtered_candle_rows(
            source_path,
            source=source,
            symbol=symbol,
            start_ms=start_ms,
            end_ms=end_ms,
        )
        destination = destination_root / "candles" / source / f"{symbol}-5m.ndjson"
        _write_ndjson(destination, rows)
        copied.append(
            {
                "source": source,
                "symbol": symbol,
                "record_count": len(rows),
                "first_open_time_ms": start_ms,
                "last_open_time_ms": end_ms - TIMEFRAME_MS,
                "normalized_file": _identity(destination, root=destination_root),
            }
        )
    expected = {(source, symbol) for source in expected_sources for symbol in EXPECTED_SYMBOLS}
    if seen != expected:
        raise MarketEvidenceIntersectionError("candle source-symbol coverage mismatch")
    return copied


def _row_counts(
    *,
    sample_count: int,
    candle_count_per_source_symbol: int,
) -> dict[str, int]:
    source_count = len(EXPECTED_SOURCES)
    symbol_count = len(EXPECTED_SYMBOLS)
    return {
        "source_health_snapshots": sample_count * source_count,
        "market_quality_observations": sample_count * source_count * symbol_count,
        "instrument_snapshots": sample_count * source_count * symbol_count,
        "completed_candles": candle_count_per_source_symbol * source_count * symbol_count,
    }


def build_intersection_package(
    *,
    base_package_root: Path,
    supplement_root: Path,
    output_run_root: Path,
    run_id: str,
) -> dict[str, object]:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise MarketEvidenceIntersectionError("run_id must be a v3 market-evidence identity")
    base_package = base_package_root.resolve(strict=True)
    supplement = supplement_root.resolve(strict=True)
    base_verification = v1_service.verify_immutable_package(base_package)
    supplement_verification = v2.verify_supplement(supplement)
    base_manifest = _load_json(base_package / MANIFEST_NAME, field="base manifest")
    supplement_manifest = _load_json(supplement / MANIFEST_NAME, field="supplement manifest")
    base_request = _load_json(base_package / REQUEST_NAME, field="base request")
    supplement_request = _load_json(supplement / REQUEST_NAME, field="supplement request")
    if base_manifest.get("run_id") != supplement_manifest.get("base_v1_run_id"):
        raise MarketEvidenceIntersectionError("supplement is not bound to the verified base run")
    if base_manifest.get("sources") != list(BASE_SOURCES):
        raise MarketEvidenceIntersectionError("base source coverage mismatch")
    _authority_is_safe(base_manifest, field="base package")
    if supplement_manifest.get("authorities") not in (None, v2.AUTHORITY):
        raise MarketEvidenceIntersectionError("supplement authority boundary mismatch")
    geometry = derive_common_geometry(
        base_manifest=base_manifest,
        supplement_manifest=supplement_manifest,
        base_request=base_request,
        supplement_request=supplement_request,
    )
    start_ms = geometry["decision_start_ms"]
    end_ms = geometry["decision_end_ms"]
    pre_roll_start_ms = geometry["pre_roll_start_ms"]
    sample_count = (end_ms - start_ms) // TIMEFRAME_MS
    candle_count = (end_ms - pre_roll_start_ms) // TIMEFRAME_MS
    expected_counts = _row_counts(
        sample_count=sample_count,
        candle_count_per_source_symbol=candle_count,
    )

    final_root = output_run_root / PACKAGE_DIR_NAME
    if final_root.exists() and not final_root.is_symlink():
        return verify_intersection_package(final_root)
    if final_root.exists() or final_root.is_symlink():
        raise MarketEvidenceIntersectionError("intersection package root is unsafe")
    partial_root = output_run_root / PARTIAL_DIR_NAME
    if partial_root.exists() or partial_root.is_symlink():
        raise MarketEvidenceIntersectionError("partial intersection package already exists")
    output_run_root.mkdir(parents=True, exist_ok=True)
    partial_root.mkdir()
    try:
        base_source_rows = _read_ndjson(
            base_package / SOURCE_ROWS_NAME,
            field="base source snapshots",
        )
        supplement_source_rows = _read_ndjson(
            supplement / SOURCE_ROWS_NAME,
            field="supplement source snapshots",
        )
        source_rows = [
            *_selected_source_rows(
                base_source_rows,
                start_ms=start_ms,
                end_ms=end_ms,
                expected_sources=set(BASE_SOURCES),
                field="base source snapshots",
            ),
            *_selected_source_rows(
                supplement_source_rows,
                start_ms=start_ms,
                end_ms=end_ms,
                expected_sources={v2.OKX_SOURCE},
                field="supplement source snapshots",
            ),
        ]
        source_rows.sort(
            key=lambda row: (
                _integer(row["scheduled_at_ms"], field="scheduled"),
                str(row["source"]),
            )
        )
        sample_keys = {
            (
                str(row["source"]),
                _integer(row.get("available_at_ms"), field="source available_at_ms"),
            )
            for row in source_rows
        }

        quality_rows = [
            *_selected_quality_rows(
                _read_ndjson(
                    base_package / QUALITY_ROWS_NAME,
                    field="base market quality",
                ),
                start_ms=start_ms,
                end_ms=end_ms,
                expected_sources=set(BASE_SOURCES),
            ),
            *_selected_quality_rows(
                _read_ndjson(
                    supplement / QUALITY_ROWS_NAME,
                    field="supplement market quality",
                ),
                start_ms=start_ms,
                end_ms=end_ms,
                expected_sources={v2.OKX_SOURCE},
            ),
        ]
        quality_rows.sort(
            key=lambda row: (
                _integer(row["scheduled_at_ms"], field="scheduled"),
                str(row["source"]),
                str(row.get("canonical_symbol") or row.get("symbol") or ""),
            )
        )

        instrument_rows = [
            *_selected_instrument_rows(
                _read_ndjson(
                    base_package / INSTRUMENT_ROWS_NAME,
                    field="base instrument history",
                ),
                sample_keys=sample_keys,
                expected_sources=set(BASE_SOURCES),
            ),
            *_selected_instrument_rows(
                _read_ndjson(
                    supplement / INSTRUMENT_ROWS_NAME,
                    field="supplement instrument history",
                ),
                sample_keys=sample_keys,
                expected_sources={v2.OKX_SOURCE},
            ),
        ]
        instrument_rows.sort(
            key=lambda row: (
                _integer(
                    row.get("available_at_ms", row.get("captured_at_ms")),
                    field="instrument available_at_ms",
                ),
                str(row["source"]),
                str(row.get("canonical_symbol") or row.get("native_symbol") or ""),
            )
        )
        actual_row_counts = {
            "source_health_snapshots": len(source_rows),
            "market_quality_observations": len(quality_rows),
            "instrument_snapshots": len(instrument_rows),
        }
        for key, actual in actual_row_counts.items():
            if actual != expected_counts[key]:
                raise MarketEvidenceIntersectionError(
                    f"intersection {key} count mismatch: {actual}"
                )

        request_payload: dict[str, object] = {
            "schema_version": 3,
            "request_type": "WickHunterMarketEvidenceGeometryIntersection",
            "run_id": run_id,
            "base_v1_run_id": base_manifest["run_id"],
            "okx_supplement_run_id": supplement_manifest["run_id"],
            "geometry": geometry,
            "derivation_policy": "max-start-min-end-no-backfill-v1",
            "minimum_pre_roll_ms": MINIMUM_PRE_ROLL_MS,
            "minimum_decision_samples": MINIMUM_DECISION_SAMPLES,
            "immutable_inputs_mutated": False,
            "protected_holdout_accessed": False,
            **v2.AUTHORITY,
        }
        _write_json(partial_root / REQUEST_NAME, request_payload)
        binding: dict[str, object] = {
            "schema_version": 3,
            "binding_type": "WickHunterMarketEvidenceGeometryIntersectionBinding",
            "run_id": run_id,
            "base_v1": {
                "run_id": base_manifest["run_id"],
                "manifest_sha256": base_manifest["manifest_sha256"],
                "request_sha256": _file_hash(base_package / REQUEST_NAME),
                "verification_manifest_sha256": base_verification["manifest_sha256"],
            },
            "okx_supplement": {
                "run_id": supplement_manifest["run_id"],
                "manifest_sha256": supplement_manifest["manifest_sha256"],
                "request_sha256": _file_hash(supplement / REQUEST_NAME),
                "verification_manifest_sha256": supplement_verification["manifest_sha256"],
            },
            "geometry": geometry,
            "immutable_inputs_mutated": False,
            "backfill_performed": False,
            "synthetic_observations_added": False,
            **v2.AUTHORITY,
        }
        binding["binding_sha256"] = _canonical_hash(binding)
        _write_json(partial_root / BINDING_NAME, binding)
        lineage = {
            "schema_version": 3,
            "run_id": run_id,
            "derivation_type": "verified_geometry_intersection",
            "source_geometries": {
                "base_v1": _capture_geometry(base_manifest),
                "okx_supplement": _capture_geometry(supplement_manifest),
            },
            "derived_geometry": geometry,
            "discarded_ranges": {
                "base_v1_pre_roll": [
                    _capture_geometry(base_manifest)["pre_roll_start_ms"],
                    pre_roll_start_ms,
                ],
                "base_v1_decision": [
                    _capture_geometry(base_manifest)["decision_start_ms"],
                    start_ms,
                ],
                "okx_supplement_decision": [
                    end_ms,
                    _capture_geometry(supplement_manifest)["decision_end_ms"],
                ],
            },
            "immutable_inputs_mutated": False,
            "protected_holdout_accessed": False,
        }
        lineage["lineage_sha256"] = _canonical_hash(lineage)
        _write_json(partial_root / LINEAGE_NAME, lineage)
        _write_ndjson(partial_root / SOURCE_ROWS_NAME, source_rows)
        _write_ndjson(partial_root / QUALITY_ROWS_NAME, quality_rows)
        _write_ndjson(partial_root / INSTRUMENT_ROWS_NAME, instrument_rows)

        base_index = json.loads((base_package / CANDLE_INDEX_NAME).read_text(encoding="utf-8"))
        supplement_index = json.loads((supplement / CANDLE_INDEX_NAME).read_text(encoding="utf-8"))
        candle_artifacts = [
            *_copy_filtered_candles(
                artifacts=_candle_artifacts(base_index),
                source_root=base_package.parent,
                destination_root=partial_root,
                expected_sources=set(BASE_SOURCES),
                start_ms=pre_roll_start_ms,
                end_ms=end_ms,
            ),
            *_copy_filtered_candles(
                artifacts=_candle_artifacts(supplement_index),
                source_root=supplement,
                destination_root=partial_root,
                expected_sources={v2.OKX_SOURCE},
                start_ms=pre_roll_start_ms,
                end_ms=end_ms,
            ),
        ]
        if (
            sum(
                _integer(item.get("record_count"), field="candle record_count")
                for item in candle_artifacts
            )
            != expected_counts["completed_candles"]
        ):
            raise MarketEvidenceIntersectionError("intersection candle count mismatch")
        _write_json(
            partial_root / CANDLE_INDEX_NAME,
            {"schema_version": 3, "artifacts": candle_artifacts},
        )
        _write_json(
            partial_root / STATE_NAME,
            {
                "schema_version": 3,
                "run_id": run_id,
                "state": "completed",
                "active": False,
                "sample_count": sample_count,
                "instrument_count": len(EXPECTED_SYMBOLS),
                "source_count": len(EXPECTED_SOURCES),
                "completeness": 1,
                "gap_count": 0,
                "verification_result": "accepted",
                "derivation_type": "verified_geometry_intersection",
                "wh01_ready": False,
                "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
                **v2.AUTHORITY,
            },
        )

        top_level_names = (
            REQUEST_NAME,
            BINDING_NAME,
            LINEAGE_NAME,
            STATE_NAME,
            SOURCE_ROWS_NAME,
            QUALITY_ROWS_NAME,
            INSTRUMENT_ROWS_NAME,
            CANDLE_INDEX_NAME,
        )
        artifacts = [_identity(partial_root / name, root=partial_root) for name in top_level_names]
        artifacts.extend(
            _identity(path, root=partial_root)
            for path in sorted((partial_root / "candles").rglob("*.ndjson"))
        )
        source_health = {
            source: {
                "healthy": True,
                "samples": sample_count,
                "market_quality_records": sample_count * len(EXPECTED_SYMBOLS),
                "completed_candles": candle_count * len(EXPECTED_SYMBOLS),
                "gaps": 0,
            }
            for source in EXPECTED_SOURCES
        }
        manifest: dict[str, object] = {
            "schema_version": 3,
            "artifact_type": "WickHunterProductionMarketEvidencePackage",
            "contract_id": v2.CONTRACT_ID,
            "run_id": run_id,
            "state": "completed",
            "verification_result": "accepted",
            "derivation_type": "verified_geometry_intersection",
            "source_package_binding_sha256": binding["binding_sha256"],
            "lineage_sha256": lineage["lineage_sha256"],
            "sources": list(EXPECTED_SOURCES),
            "instruments": list(EXPECTED_SYMBOLS),
            "capture": {
                "pre_roll_start_ms": pre_roll_start_ms,
                "decision_start_ms": start_ms,
                "decision_end_ms": end_ms,
                "pre_roll_ms": start_ms - pre_roll_start_ms,
                "cadence_seconds": 300,
                "timeframe": "5m",
            },
            "protected_holdout_start_ms": geometry["protected_holdout_start_ms"],
            "record_counts": expected_counts,
            "first_timestamp_ms": pre_roll_start_ms,
            "last_timestamp_ms": end_ms,
            "gaps": [],
            "availability": {
                "decision_safe": True,
                "completed_candles_only": True,
                "minimum_pre_roll_satisfied": True,
            },
            "source_health": source_health,
            "wh01": {
                "market_evidence_ready": True,
                "ready": False,
                "blocker_code": "LIQUIDATION_ARCHIVE_NOT_BOUND",
                "blocker_detail": (
                    "A compatible accepted immutable Liquid20 archive and "
                    "prospective WH-01 split binding are still required."
                ),
            },
            "artifacts": artifacts,
            "authorities": v2.AUTHORITY,
            "immutable_inputs_mutated": False,
            "backfill_performed": False,
            "synthetic_observations_added": False,
            "protected_holdout_accessed": False,
            "host_paths_exposed": False,
            "raw_exchange_payloads_exposed_by_portal": False,
        }
        manifest["manifest_sha256"] = _canonical_hash(manifest)
        _write_json(partial_root / MANIFEST_NAME, manifest)
        checksum_identities = [
            *artifacts,
            _identity(partial_root / MANIFEST_NAME, root=partial_root),
        ]
        checksum_lines = sorted(
            f"{item['sha256']}  {item['logical_name']}" for item in checksum_identities
        )
        _write_new(
            partial_root / CHECKSUM_NAME,
            ("\n".join(checksum_lines) + "\n").encode("utf-8"),
        )
        _write_json(
            partial_root / VERIFICATION_NAME,
            {
                "schema_version": 3,
                "status": "verified",
                "outcome": "accepted",
                "run_id": run_id,
                "manifest_sha256": manifest["manifest_sha256"],
                "binding_sha256": binding["binding_sha256"],
                "lineage_sha256": lineage["lineage_sha256"],
                "artifact_count": len(artifacts),
                **expected_counts,
                "wh01_ready": False,
                "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
                "immutable_inputs_mutated": False,
                "protected_holdout_accessed": False,
                **v2.AUTHORITY,
            },
        )
        verify_intersection_package(partial_root)
        partial_root.replace(final_root)
        return verify_intersection_package(final_root)
    except Exception:
        shutil.rmtree(partial_root, ignore_errors=True)
        raise


def verify_intersection_package(  # noqa: C901
    package_root: Path,
) -> dict[str, object]:
    if package_root.is_symlink() or not package_root.is_dir():
        raise MarketEvidenceIntersectionError("package root must be a regular directory")
    manifest = _load_json(package_root / MANIFEST_NAME, field="intersection manifest")
    claimed = manifest.get("manifest_sha256")
    seed = dict(manifest)
    seed.pop("manifest_sha256", None)
    if not isinstance(claimed, str) or _canonical_hash(seed) != claimed:
        raise MarketEvidenceIntersectionError("intersection manifest self hash mismatch")
    run_id = str(manifest.get("run_id", ""))
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise MarketEvidenceIntersectionError("intersection run identity mismatch")
    if manifest.get("derivation_type") != "verified_geometry_intersection":
        raise MarketEvidenceIntersectionError("intersection derivation type mismatch")
    if manifest.get("sources") != list(EXPECTED_SOURCES):
        raise MarketEvidenceIntersectionError("intersection source coverage mismatch")
    if manifest.get("instruments") != list(EXPECTED_SYMBOLS):
        raise MarketEvidenceIntersectionError("intersection symbol coverage mismatch")
    if manifest.get("authorities") != v2.AUTHORITY:
        raise MarketEvidenceIntersectionError("intersection authority boundary mismatch")
    if (
        manifest.get("immutable_inputs_mutated") is not False
        or manifest.get("backfill_performed") is not False
        or manifest.get("synthetic_observations_added") is not False
        or manifest.get("protected_holdout_accessed") is not False
    ):
        raise MarketEvidenceIntersectionError("intersection safety boundary mismatch")
    capture = _capture_geometry(manifest)
    protected_holdout_start_ms = _integer(
        manifest.get("protected_holdout_start_ms"),
        field="protected_holdout_start_ms",
    )
    if (
        capture["decision_start_ms"] - capture["pre_roll_start_ms"] < MINIMUM_PRE_ROLL_MS
        or capture["decision_end_ms"] > protected_holdout_start_ms
    ):
        raise MarketEvidenceIntersectionError("intersection geometry safety mismatch")
    sample_count = (capture["decision_end_ms"] - capture["decision_start_ms"]) // TIMEFRAME_MS
    candle_count = (capture["decision_end_ms"] - capture["pre_roll_start_ms"]) // TIMEFRAME_MS
    expected_counts = _row_counts(
        sample_count=sample_count,
        candle_count_per_source_symbol=candle_count,
    )
    if manifest.get("record_counts") != expected_counts:
        raise MarketEvidenceIntersectionError("intersection record counts mismatch")

    binding = _load_json(package_root / BINDING_NAME, field="intersection binding")
    binding_claim = binding.get("binding_sha256")
    binding_seed = dict(binding)
    binding_seed.pop("binding_sha256", None)
    if (
        not isinstance(binding_claim, str)
        or _canonical_hash(binding_seed) != binding_claim
        or manifest.get("source_package_binding_sha256") != binding_claim
    ):
        raise MarketEvidenceIntersectionError("intersection binding identity mismatch")
    lineage = _load_json(package_root / LINEAGE_NAME, field="intersection lineage")
    lineage_claim = lineage.get("lineage_sha256")
    lineage_seed = dict(lineage)
    lineage_seed.pop("lineage_sha256", None)
    if (
        not isinstance(lineage_claim, str)
        or _canonical_hash(lineage_seed) != lineage_claim
        or manifest.get("lineage_sha256") != lineage_claim
    ):
        raise MarketEvidenceIntersectionError("intersection lineage identity mismatch")

    actual_counts = {
        "source_health_snapshots": len(
            _read_ndjson(package_root / SOURCE_ROWS_NAME, field="source snapshots")
        ),
        "market_quality_observations": len(
            _read_ndjson(package_root / QUALITY_ROWS_NAME, field="market quality")
        ),
        "instrument_snapshots": len(
            _read_ndjson(package_root / INSTRUMENT_ROWS_NAME, field="instrument history")
        ),
    }
    for key, actual in actual_counts.items():
        if actual != expected_counts[key]:
            raise MarketEvidenceIntersectionError(f"intersection {key} count mismatch")

    index = _load_json(package_root / CANDLE_INDEX_NAME, field="candle index")
    candle_artifacts = _candle_artifacts(index)
    expected_identities = {
        (source, symbol) for source in EXPECTED_SOURCES for symbol in EXPECTED_SYMBOLS
    }
    seen: set[tuple[str, str]] = set()
    total_candles = 0
    for artifact in candle_artifacts:
        source = str(artifact.get("source", ""))
        symbol = str(artifact.get("symbol", "")).upper()
        source_symbol = (source, symbol)
        if source_symbol in seen or source_symbol not in expected_identities:
            raise MarketEvidenceIntersectionError("candle index identity mismatch")
        seen.add(source_symbol)
        count = _integer(artifact.get("record_count"), field="candle record_count")
        if count != candle_count:
            raise MarketEvidenceIntersectionError("candle file row count mismatch")
        normalized = _object(
            artifact.get("normalized_file"),
            field="normalized candle file",
        )
        path = _safe_member(package_root, str(normalized.get("logical_name", "")))
        if _file_hash(path) != normalized.get("sha256") or path.stat().st_size != normalized.get(
            "size_bytes"
        ):
            raise MarketEvidenceIntersectionError("candle file identity mismatch")
        rows = _filtered_candle_rows(
            path,
            source=source,
            symbol=symbol,
            start_ms=capture["pre_roll_start_ms"],
            end_ms=capture["decision_end_ms"],
        )
        if len(rows) != count:
            raise MarketEvidenceIntersectionError("candle row count mismatch")
        total_candles += count
    if seen != expected_identities or total_candles != expected_counts["completed_candles"]:
        raise MarketEvidenceIntersectionError("candle coverage mismatch")

    artifacts = _sequence(manifest.get("artifacts"), field="manifest artifacts")
    expected_lines: set[str] = set()
    for raw in artifacts:
        artifact_identity = _object(raw, field="artifact identity")
        logical_name = str(artifact_identity.get("logical_name", ""))
        path = _safe_member(package_root, logical_name)
        if _file_hash(path) != artifact_identity.get(
            "sha256"
        ) or path.stat().st_size != artifact_identity.get("size_bytes"):
            raise MarketEvidenceIntersectionError("intersection artifact identity mismatch")
        expected_lines.add(f"{artifact_identity['sha256']}  {logical_name}")
    manifest_identity = _identity(package_root / MANIFEST_NAME, root=package_root)
    expected_lines.add(f"{manifest_identity['sha256']}  {MANIFEST_NAME}")
    checksum = package_root / CHECKSUM_NAME
    if checksum.is_symlink() or not checksum.is_file():
        raise MarketEvidenceIntersectionError("intersection checksum is missing")
    if set(checksum.read_text(encoding="utf-8").splitlines()) != expected_lines:
        raise MarketEvidenceIntersectionError("intersection checksum mismatch")

    verification = _load_json(
        package_root / VERIFICATION_NAME,
        field="intersection verification",
    )
    if (
        verification.get("outcome") != "accepted"
        or verification.get("manifest_sha256") != claimed
        or any(verification.get(key) != value for key, value in v2.AUTHORITY.items())
    ):
        raise MarketEvidenceIntersectionError("intersection verification mismatch")
    return {
        "status": "published",
        "outcome": "accepted",
        "run_id": run_id,
        "package_root": str(package_root),
        "manifest_sha256": claimed,
        "binding_sha256": binding_claim,
        "lineage_sha256": lineage_claim,
        "record_counts": expected_counts,
        "wh01_ready": False,
        "wh01_blocker": "LIQUIDATION_ARCHIVE_NOT_BOUND",
        "protected_holdout_accessed": False,
        **v2.AUTHORITY,
    }


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Derive and verify an immutable common-geometry market-evidence package."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    derive = commands.add_parser("derive")
    derive.add_argument("--base-package-root", type=Path, required=True)
    derive.add_argument("--supplement-root", type=Path, required=True)
    derive.add_argument("--output-run-root", type=Path, required=True)
    derive.add_argument("--run-id", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--package-root", type=Path, required=True)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        if args.command == "derive":
            result = build_intersection_package(
                base_package_root=args.base_package_root,
                supplement_root=args.supplement_root,
                output_run_root=args.output_run_root,
                run_id=args.run_id,
            )
        else:
            result = verify_intersection_package(args.package_root)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (
        MarketEvidenceIntersectionError,
        v1_service.MarketEvidencePublicationError,
        v2.ProductionMarketEvidenceV2Error,
        OSError,
        ValueError,
    ) as exc:
        print(f"WickHunter geometry intersection failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
