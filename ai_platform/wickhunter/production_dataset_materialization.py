from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import AvailableMetric, MarketContextSnapshot
from ai_platform.wickhunter.dataset import (
    DATASET_MANIFEST_SCHEMA_VERSION,
    DatasetSplitGeometry,
    DatasetSplitWindow,
    WickHunterDatasetBuildRequest,
    build_wickhunter_dataset,
    load_accepted_import,
)
from ai_platform.wickhunter.production_market_evidence_intersection import (
    CANDLE_INDEX_NAME,
    QUALITY_ROWS_NAME,
    SOURCE_ROWS_NAME,
    TIMEFRAME_MS,
    verify_intersection_package,
)
from ai_platform.wickhunter.production_market_evidence_intersection import (
    MANIFEST_NAME as MARKET_MANIFEST_NAME,
)
from ai_platform.wickhunter.production_market_evidence_wh01 import (
    MetricLookbacks,
    WickHunterInputAdapterError,
    _source_metrics,
)
from ai_platform.wickhunter.universe import (
    DynamicUniverseSnapshot,
    UniverseInstrumentDecision,
)


MATERIALIZATION_SCHEMA_VERSION = "wickhunter-production-materialization-v1"
BINDING_SCHEMA_VERSION = "wickhunter-production-source-binding-v1"
DATASET_DIR_NAME = "dataset"
BINDING_NAME = "source-binding.json"
MATERIALIZATION_MANIFEST_NAME = "materialization-manifest.json"
CHECKSUM_NAME = "artifact-sha256.txt"
VERIFICATION_NAME = "verification-report.json"
DEFAULT_SPLIT_VERSION = "wickhunter-production-splits-20260731-v1"
DEFAULT_DATASET_VERSION = "wickhunter-production-dataset-20260731-v1"
DEFAULT_BURST_WINDOW_MS = 15 * 60 * 1000
DEFAULT_PARTITION_SPAN_MS = 60 * 60 * 1000
DEFAULT_MINIMUM_HISTORY_EVENTS = 1
DEFAULT_MAXIMUM_SOURCE_AGE_MS = 60 * 60 * 1000
DEFAULT_LABEL_HORIZON_MS = 15 * 60 * 1000
DEFAULT_EMBARGO_MS = 30 * 60 * 1000
PRIMARY_CANDLE_SOURCE = "binance-usdm"
PRODUCTION_METRIC_POLICY_VERSION = "wickhunter-production-market-evidence-v3-wh01-metric-binding-v1"
PRODUCTION_METRIC_LOOKBACKS = MetricLookbacks(
    quote_volume_rows=288,
    vwap_rows=288,
    vwma_rows=288,
    atr_rows=14,
    volatility_rows=287,
    wick_rows=288,
    trend_rows=288,
)
PRODUCTION_SPREAD_AGGREGATION = "source_balanced_mean_require_all"
PRODUCTION_LIQUIDATION_INTENSITY_POLICY = (
    "current_burst_over_mean_complete_prior_bursts_since_accepted_import_start"
)


class ProductionDatasetMaterializationError(RuntimeError):
    """Raised when WH-01 production evidence cannot be bound safely."""


def _canonical_bytes(value: object) -> bytes:
    return canonical_json(value).encode("utf-8")


def _self_hash(payload: Mapping[str, object], *, field: str) -> str:
    seed = dict(payload)
    seed.pop(field, None)
    return hashlib.sha256(_canonical_bytes(seed)).hexdigest()


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ProductionDatasetMaterializationError(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, payload: object) -> None:
    _write_new(path, _canonical_bytes(payload) + b"\n")


def _load_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ProductionDatasetMaterializationError(f"{field} must be a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionDatasetMaterializationError(f"unable to read {field}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProductionDatasetMaterializationError(f"{field} must contain an object")
    return payload


def _load_rows(path: Path, *, field: str) -> list[dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise ProductionDatasetMaterializationError(f"{field} must be a regular file")
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    raise ProductionDatasetMaterializationError(
                        f"{field} contains a blank line at {line_number}"
                    )
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ProductionDatasetMaterializationError(
                        f"{field} row {line_number} must be an object"
                    )
                rows.append(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionDatasetMaterializationError(f"unable to read {field}: {exc}") from exc
    return rows


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ProductionDatasetMaterializationError(f"{field} must be an integer")
    try:
        return int(value)
    except ValueError as exc:
        raise ProductionDatasetMaterializationError(f"{field} must be an integer") from exc


def _decimal(value: object, *, field: str, positive: bool = False) -> Decimal:
    if isinstance(value, bool):
        raise ProductionDatasetMaterializationError(f"{field} must be decimal-compatible")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ProductionDatasetMaterializationError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite() or (positive and parsed <= 0):
        raise ProductionDatasetMaterializationError(f"{field} has an invalid value")
    return parsed


def _mean(values: Sequence[Decimal], *, field: str) -> Decimal:
    if not values:
        raise ProductionDatasetMaterializationError(f"{field} has no values")
    return sum(values, Decimal(0)) / Decimal(len(values))


def _market_metric_policy() -> dict[str, object]:
    payload: dict[str, object] = {
        "policy_version": PRODUCTION_METRIC_POLICY_VERSION,
        "timeframe": "5m",
        "primary_candle_source": PRIMARY_CANDLE_SOURCE,
        "metric_lookback_rows": asdict(PRODUCTION_METRIC_LOOKBACKS),
        "spread_aggregation": PRODUCTION_SPREAD_AGGREGATION,
        "liquidation_intensity": PRODUCTION_LIQUIDATION_INTENSITY_POLICY,
        "burst_window_ms": DEFAULT_BURST_WINDOW_MS,
    }
    payload["policy_sha256"] = canonical_sha256(payload)
    return payload


def _market_wide_liquidation_intensity(
    events: Sequence[Any],
    *,
    decision_timestamp_ms: int,
    history_start_ms: int,
) -> Decimal:
    current_start_ms = decision_timestamp_ms - DEFAULT_BURST_WINDOW_MS
    complete_bucket_count = (current_start_ms - history_start_ms) // DEFAULT_BURST_WINDOW_MS
    if complete_bucket_count < 1:
        raise ProductionDatasetMaterializationError(
            "market-wide liquidation intensity lacks a complete history bucket"
        )
    aligned_history_start_ms = current_start_ms - complete_bucket_count * DEFAULT_BURST_WINDOW_MS
    current_notional = Decimal(0)
    history_buckets = [Decimal(0) for _ in range(complete_bucket_count)]
    for event in events:
        available_at_ms = _integer(
            getattr(event, "available_at_ms", None),
            field="liquidation available_at_ms",
        )
        if available_at_ms > decision_timestamp_ms:
            continue
        notional = _decimal(
            getattr(event, "notional_usd", None),
            field="liquidation notional_usd",
        )
        if notional < 0:
            raise ProductionDatasetMaterializationError(
                "liquidation notional_usd must be non-negative"
            )
        if current_start_ms <= available_at_ms <= decision_timestamp_ms:
            current_notional += notional
        elif aligned_history_start_ms <= available_at_ms < current_start_ms:
            bucket_index = (available_at_ms - aligned_history_start_ms) // DEFAULT_BURST_WINDOW_MS
            if 0 <= bucket_index < complete_bucket_count:
                history_buckets[bucket_index] += notional
    baseline = _mean(
        history_buckets,
        field="market-wide liquidation burst history",
    )
    if baseline <= 0:
        raise ProductionDatasetMaterializationError(
            "market-wide liquidation intensity lacks positive history"
        )
    return current_notional / baseline


def _safe_member(root: Path, logical_name: str) -> Path:
    relative = Path(logical_name)
    if (
        not logical_name
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ProductionDatasetMaterializationError("artifact path must remain relative")
    resolved_root = root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ProductionDatasetMaterializationError("artifact path traverses a symlink")
    try:
        current.resolve(strict=True).relative_to(resolved_root)
    except (FileNotFoundError, ValueError) as exc:
        raise ProductionDatasetMaterializationError("artifact path escapes package root") from exc
    if not current.is_file():
        raise ProductionDatasetMaterializationError("artifact member is not a regular file")
    return current


def _market_geometry(manifest: Mapping[str, object]) -> tuple[int, int, int, int]:
    capture = manifest.get("capture")
    if not isinstance(capture, dict):
        raise ProductionDatasetMaterializationError("market manifest capture is missing")
    pre_roll_start_ms = _integer(capture.get("pre_roll_start_ms"), field="pre_roll_start_ms")
    decision_start_ms = _integer(capture.get("decision_start_ms"), field="decision_start_ms")
    decision_end_ms = _integer(capture.get("decision_end_ms"), field="decision_end_ms")
    holdout_start_ms = _integer(
        manifest.get("protected_holdout_start_ms"),
        field="protected_holdout_start_ms",
    )
    if decision_start_ms - pre_roll_start_ms < 86_400_000:
        raise ProductionDatasetMaterializationError("market pre-roll is shorter than 24h")
    if decision_end_ms > holdout_start_ms:
        raise ProductionDatasetMaterializationError("market geometry overlaps holdout")
    if any(
        value % TIMEFRAME_MS for value in (pre_roll_start_ms, decision_start_ms, decision_end_ms)
    ):
        raise ProductionDatasetMaterializationError("market geometry is not 5m-aligned")
    return pre_roll_start_ms, decision_start_ms, decision_end_ms, holdout_start_ms


def production_split_geometry(
    *,
    decision_start_ms: int,
    decision_end_ms: int,
    protected_holdout_start_ms: int,
) -> DatasetSplitGeometry:
    duration_ms = decision_end_ms - decision_start_ms
    if duration_ms < 10 * 60 * 60 * 1000:
        raise ProductionDatasetMaterializationError(
            "production geometry requires at least ten decision hours"
        )
    train_end_ms = decision_start_ms + 6 * 60 * 60 * 1000
    validation_start_ms = train_end_ms + DEFAULT_EMBARGO_MS
    validation_end_ms = validation_start_ms + 2 * 60 * 60 * 1000
    test_start_ms = validation_end_ms + DEFAULT_EMBARGO_MS
    if test_start_ms >= decision_end_ms:
        raise ProductionDatasetMaterializationError("production split leaves no test window")
    return DatasetSplitGeometry(
        geometry_version=DEFAULT_SPLIT_VERSION,
        windows=(
            DatasetSplitWindow(
                name="train",
                start_ms=decision_start_ms,
                end_ms=train_end_ms,
            ),
            DatasetSplitWindow(
                name="validation",
                start_ms=validation_start_ms,
                end_ms=validation_end_ms,
            ),
            DatasetSplitWindow(
                name="test",
                start_ms=test_start_ms,
                end_ms=decision_end_ms,
            ),
        ),
        label_horizon_ms=DEFAULT_LABEL_HORIZON_MS,
        embargo_ms=DEFAULT_EMBARGO_MS,
        protected_holdout_start_ms=protected_holdout_start_ms,
    )


def _candle_maps(  # noqa: C901
    market_root: Path,
    *,
    manifest: Mapping[str, object],
) -> dict[str, dict[int, dict[str, Any]]]:
    symbols = manifest.get("instruments")
    if not isinstance(symbols, list) or not symbols:
        raise ProductionDatasetMaterializationError("market instruments are missing")
    index = _load_json(market_root / CANDLE_INDEX_NAME, field="candle index")
    artifacts = index.get("artifacts")
    if not isinstance(artifacts, list):
        raise ProductionDatasetMaterializationError("candle index artifacts are missing")
    result: dict[str, dict[int, dict[str, Any]]] = {}
    seen: set[str] = set()
    for raw in artifacts:
        if not isinstance(raw, dict) or raw.get("source") != PRIMARY_CANDLE_SOURCE:
            continue
        symbol = str(raw.get("symbol", "")).upper()
        if symbol not in symbols or symbol in seen:
            raise ProductionDatasetMaterializationError("primary candle identity mismatch")
        normalized = raw.get("normalized_file")
        if not isinstance(normalized, dict):
            raise ProductionDatasetMaterializationError("normalized candle identity is missing")
        path = _safe_member(market_root, str(normalized.get("logical_name", "")))
        if sha256_file(path) != normalized.get("sha256"):
            raise ProductionDatasetMaterializationError("primary candle hash mismatch")
        rows = _load_rows(path, field=f"{symbol} candles")
        by_open: dict[int, dict[str, Any]] = {}
        for row in rows:
            if row.get("source") != PRIMARY_CANDLE_SOURCE or row.get("symbol") != symbol:
                raise ProductionDatasetMaterializationError("primary candle row identity mismatch")
            open_ms = _integer(row.get("open_time_ms"), field="candle open_time_ms")
            if open_ms in by_open:
                raise ProductionDatasetMaterializationError("duplicate candle open timestamp")
            close_ms = _integer(
                row.get("close_time_ms_exclusive"),
                field="candle close_time_ms_exclusive",
            )
            if close_ms != open_ms + TIMEFRAME_MS:
                raise ProductionDatasetMaterializationError("candle close boundary mismatch")
            _decimal(row.get("close"), field="candle close", positive=True)
            by_open[open_ms] = row
        result[symbol] = by_open
        seen.add(symbol)
    if seen != set(str(symbol) for symbol in symbols):
        raise ProductionDatasetMaterializationError("primary candle symbol coverage mismatch")
    return result


def _market_inputs(  # noqa: C901
    market_root: Path,
    *,
    accepted_events: Sequence[Any],
    liquidation_history_start_ms: int,
) -> tuple[
    tuple[MarketContextSnapshot, ...],
    tuple[DynamicUniverseSnapshot, ...],
    dict[str, object],
]:
    verification = verify_intersection_package(market_root)
    manifest = _load_json(market_root / MARKET_MANIFEST_NAME, field="market manifest")
    pre_roll_start_ms, decision_start_ms, decision_end_ms, holdout_start_ms = _market_geometry(
        manifest
    )
    del pre_roll_start_ms
    sources = manifest.get("sources")
    symbols = manifest.get("instruments")
    if not isinstance(sources, list) or not sources:
        raise ProductionDatasetMaterializationError("market sources are missing")
    if not isinstance(symbols, list) or not symbols:
        raise ProductionDatasetMaterializationError("market instruments are missing")
    if not accepted_events:
        raise ProductionDatasetMaterializationError("accepted Liquid20 import contains no events")

    source_rows = _load_rows(market_root / SOURCE_ROWS_NAME, field="source rows")
    quality_rows = _load_rows(market_root / QUALITY_ROWS_NAME, field="quality rows")
    source_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    for row in source_rows:
        scheduled = _integer(
            row.get("scheduled_at_ms"),
            field="source scheduled_at_ms",
        )
        source = str(row.get("source", ""))
        source_key = (scheduled, source)
        if source_key in source_by_key:
            raise ProductionDatasetMaterializationError("duplicate source health key")
        source_by_key[source_key] = row
    quality_by_key: dict[tuple[int, str, str], dict[str, Any]] = {}
    for row in quality_rows:
        scheduled = _integer(
            row.get("scheduled_at_ms"),
            field="quality scheduled_at_ms",
        )
        source = str(row.get("source", ""))
        symbol = str(row.get("canonical_symbol") or row.get("symbol") or "").upper()
        quality_key = (scheduled, source, symbol)
        if quality_key in quality_by_key:
            raise ProductionDatasetMaterializationError("duplicate market-quality key")
        quality_by_key[quality_key] = row
    candles = _candle_maps(market_root, manifest=manifest)
    ordered_candles = {
        symbol: [by_open[key] for key in sorted(by_open)] for symbol, by_open in candles.items()
    }
    metric_policy = _market_metric_policy()

    markets: list[MarketContextSnapshot] = []
    universes: list[DynamicUniverseSnapshot] = []
    for scheduled in range(decision_start_ms, decision_end_ms, TIMEFRAME_MS):
        availability_values: list[int] = []
        healthy_sources: set[str] = set()
        for source in sources:
            try:
                row = source_by_key[(scheduled, str(source))]
            except KeyError as exc:
                raise ProductionDatasetMaterializationError(
                    "source health coverage is incomplete"
                ) from exc
            available = _integer(
                row.get("available_at_ms"),
                field="source available_at_ms",
            )
            availability_values.append(available)
            if (
                row.get("healthy") is True
                and row.get("connected") is True
                and row.get("wickhunter_available") is True
                and row.get("gaps") == 0
            ):
                healthy_sources.add(str(source))
        quality_for_symbol: dict[str, list[dict[str, Any]]] = {}
        for symbol in symbols:
            records: list[dict[str, Any]] = []
            for source in sources:
                try:
                    row = quality_by_key[(scheduled, str(source), str(symbol))]
                except KeyError as exc:
                    raise ProductionDatasetMaterializationError(
                        "market-quality coverage is incomplete"
                    ) from exc
                availability_values.append(
                    _integer(
                        row.get("available_at_ms"),
                        field="quality available_at_ms",
                    )
                )
                records.append(row)
            quality_for_symbol[str(symbol)] = records
        decision_timestamp_ms = max(availability_values)
        if decision_timestamp_ms >= holdout_start_ms:
            raise ProductionDatasetMaterializationError(
                "market availability crosses protected holdout"
            )
        liquidation_intensity = _market_wide_liquidation_intensity(
            accepted_events,
            decision_timestamp_ms=decision_timestamp_ms,
            history_start_ms=liquidation_history_start_ms,
        )

        decisions: list[UniverseInstrumentDecision] = []
        for symbol in sorted(str(value) for value in symbols):
            records = quality_for_symbol[symbol]
            reasons: list[str] = []
            if healthy_sources != set(str(source) for source in sources):
                reasons.append("source_health_incomplete")
            if any(record.get("market_available") is not True for record in records):
                reasons.append("market_quality_unavailable")
            candle = candles[symbol].get(scheduled - TIMEFRAME_MS)
            if candle is None:
                reasons.append("completed_candle_missing")
            included = not reasons
            decisions.append(
                UniverseInstrumentDecision(
                    canonical_instrument_id=f"perpetual:{symbol}",
                    canonical_symbol=symbol,
                    included=included,
                    reason_codes=(("eligible",) if included else tuple(sorted(set(reasons)))),
                )
            )
            if not included:
                continue
            try:
                candle_metrics = _source_metrics(
                    ordered_candles[symbol],
                    scheduled,
                    PRODUCTION_METRIC_LOOKBACKS,
                )
            except WickHunterInputAdapterError as exc:
                raise ProductionDatasetMaterializationError(
                    f"unable to derive canonical WH-01 candle metrics: {exc}"
                ) from exc
            quality_available_at_ms = max(
                _integer(
                    record.get("available_at_ms"),
                    field="quality available_at_ms",
                )
                for record in records
            )
            spread_bps = _mean(
                [
                    _decimal(
                        record.get("spread_bps"),
                        field=f"{record.get('source')}.spread_bps",
                    )
                    for record in records
                ],
                field="source-balanced spread_bps",
            )
            metric_values = {
                name: candle_metrics[name]
                for name in (
                    "quote_volume_24h_usd",
                    "vwap",
                    "vwma",
                    "atr_ratio",
                    "volatility_ratio",
                    "wick_ratio",
                    "trend_return_ratio",
                )
            }
            metric_values["spread_bps"] = spread_bps
            metric_values["market_wide_liquidation_intensity"] = liquidation_intensity
            metrics: list[AvailableMetric] = []
            for name, value in sorted(metric_values.items()):
                if name == "spread_bps":
                    available_at_ms = quality_available_at_ms
                    source_name = (
                        "market_quality:"
                        + "+".join(sorted(str(source) for source in sources))
                        + ":source_balanced_mean"
                    )
                elif name == "market_wide_liquidation_intensity":
                    available_at_ms = decision_timestamp_ms
                    source_name = (
                        "accepted_liquidation_archive:market_wide:"
                        + PRODUCTION_METRIC_POLICY_VERSION
                    )
                else:
                    available_at_ms = scheduled
                    source_name = (
                        f"completed_candle:{PRIMARY_CANDLE_SOURCE}:"
                        f"{PRODUCTION_METRIC_POLICY_VERSION}"
                    )
                if available_at_ms > decision_timestamp_ms:
                    raise ProductionDatasetMaterializationError(
                        "derived market metric is unavailable at decision time"
                    )
                metrics.append(
                    AvailableMetric(
                        name=name,
                        value=value,
                        available_at_ms=available_at_ms,
                        source=source_name,
                    )
                )
            markets.append(
                MarketContextSnapshot(
                    symbol=symbol,
                    decision_timestamp_ms=decision_timestamp_ms,
                    decision_price=candle_metrics["decision_price"],
                    completed_candle_close_ms=scheduled,
                    metrics=tuple(metrics),
                )
            )
        universes.append(
            DynamicUniverseSnapshot(
                schema_version="wickhunter-dynamic-universe-v1",
                policy_version=("market-evidence-v3-observed-eligibility-v1"),
                selected_at_ms=decision_timestamp_ms,
                decisions=tuple(decisions),
            )
        )
    if not markets or not universes:
        raise ProductionDatasetMaterializationError("market evidence produced no eligible inputs")
    market_keys = {(item.decision_timestamp_ms, item.symbol) for item in markets}
    if len(market_keys) != len(markets):
        raise ProductionDatasetMaterializationError("market context keys are not unique")
    return (
        tuple(markets),
        tuple(universes),
        {
            "market_verification": verification,
            "market_manifest": manifest,
            "market_context_count": len(markets),
            "universe_snapshot_count": len(universes),
            "market_metric_policy": metric_policy,
            "market_metric_policy_sha256": metric_policy["policy_sha256"],
        },
    )


def _dataset_request(
    *,
    code_sha: str,
    geometry: DatasetSplitGeometry,
) -> WickHunterDatasetBuildRequest:
    return WickHunterDatasetBuildRequest(
        dataset_version=DEFAULT_DATASET_VERSION,
        code_sha=code_sha,
        burst_window_ms=DEFAULT_BURST_WINDOW_MS,
        partition_span_ms=DEFAULT_PARTITION_SPAN_MS,
        minimum_history_events=DEFAULT_MINIMUM_HISTORY_EVENTS,
        maximum_source_age_ms=DEFAULT_MAXIMUM_SOURCE_AGE_MS,
        split_geometry=geometry,
    )


def _dataset_manifest(path: Path) -> dict[str, Any]:
    manifest = _load_json(path, field="dataset manifest")
    if manifest.get("schema_version") != DATASET_MANIFEST_SCHEMA_VERSION:
        raise ProductionDatasetMaterializationError("dataset manifest schema mismatch")
    if manifest.get("model_execution_authorized") is not False:
        raise ProductionDatasetMaterializationError("dataset authorizes model execution")
    total_rows = manifest.get("total_rows")
    if isinstance(total_rows, bool) or not isinstance(total_rows, int) or total_rows <= 0:
        raise ProductionDatasetMaterializationError("dataset is empty")
    claimed = manifest.get("manifest_sha256")
    seed = dict(manifest)
    seed.pop("manifest_sha256", None)
    if not isinstance(claimed, str) or canonical_sha256(seed) != claimed:
        raise ProductionDatasetMaterializationError("dataset manifest self hash mismatch")
    return manifest


def _verify_partitions(dataset_root: Path, manifest: Mapping[str, object]) -> None:
    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise ProductionDatasetMaterializationError("dataset partitions are missing")
    total = 0
    for raw in partitions:
        if not isinstance(raw, dict):
            raise ProductionDatasetMaterializationError("dataset partition is invalid")
        relative = Path(str(raw.get("relative_path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise ProductionDatasetMaterializationError("dataset partition path escapes root")
        path = dataset_root / relative
        if path.is_symlink() or not path.is_file():
            raise ProductionDatasetMaterializationError("dataset partition is missing")
        if sha256_file(path) != raw.get("sha256"):
            raise ProductionDatasetMaterializationError("dataset partition hash mismatch")
        count = raw.get("row_count")
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ProductionDatasetMaterializationError("dataset partition row count is invalid")
        total += count
    if total != manifest.get("total_rows"):
        raise ProductionDatasetMaterializationError("dataset partition totals mismatch")


def materialize_production_dataset(
    *,
    output_root: Path,
    market_package_root: Path,
    accepted_import_root: Path,
    code_sha: str,
) -> dict[str, object]:
    output_root = output_root.resolve()
    if output_root.exists() or output_root.is_symlink():
        return verify_production_materialization(output_root)
    if len(code_sha) != 40 or any(character not in "0123456789abcdef" for character in code_sha):
        raise ProductionDatasetMaterializationError("code_sha must be a lowercase Git SHA")
    accepted = load_accepted_import(accepted_import_root.resolve(strict=True))
    markets, universes, market_evidence = _market_inputs(
        market_package_root.resolve(strict=True),
        accepted_events=accepted.events,
        liquidation_history_start_ms=accepted.selection.requested_start_ms,
    )
    market_manifest = market_evidence["market_manifest"]
    if not isinstance(market_manifest, dict):
        raise ProductionDatasetMaterializationError("market manifest is unavailable")
    _, decision_start_ms, decision_end_ms, holdout_start_ms = _market_geometry(market_manifest)
    if accepted.selection.protected_holdout_start_ms != holdout_start_ms:
        raise ProductionDatasetMaterializationError(
            "Liquid20 import and market package disagree on holdout"
        )
    if accepted.selection.requested_start_ms > decision_start_ms - DEFAULT_BURST_WINDOW_MS:
        raise ProductionDatasetMaterializationError("Liquid20 import lacks required pre-roll")
    if accepted.selection.requested_end_ms < decision_end_ms:
        raise ProductionDatasetMaterializationError(
            "Liquid20 import does not cover the decision interval"
        )
    geometry = production_split_geometry(
        decision_start_ms=decision_start_ms,
        decision_end_ms=decision_end_ms,
        protected_holdout_start_ms=holdout_start_ms,
    )
    request = _dataset_request(code_sha=code_sha, geometry=geometry)

    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent))
    try:
        dataset_root = temporary_root / DATASET_DIR_NAME
        artifacts = build_wickhunter_dataset(
            output_root=dataset_root,
            request=request,
            accepted_import_roots=(accepted_import_root,),
            market_snapshots=markets,
            universe_snapshots=universes,
        )
        dataset_manifest = _dataset_manifest(dataset_root / "manifest.json")
        _verify_partitions(dataset_root, dataset_manifest)
        market_verification = market_evidence["market_verification"]
        if not isinstance(market_verification, dict):
            raise ProductionDatasetMaterializationError("market verification is unavailable")
        binding: dict[str, object] = {
            "schema_version": BINDING_SCHEMA_VERSION,
            "market_evidence": {
                "run_id": market_manifest.get("run_id"),
                "manifest_sha256": market_manifest.get("manifest_sha256"),
                "binding_sha256": market_verification.get("binding_sha256"),
                "lineage_sha256": market_verification.get("lineage_sha256"),
                "package_root_identity": market_package_root.name,
            },
            "liquid20": asdict(accepted.selection),
            "liquid20_selection_sha256": accepted.selection.selection_sha256,
            "split_geometry": asdict(geometry),
            "split_geometry_sha256": geometry.geometry_sha256,
            "dataset_request_sha256": request.request_sha256,
            "market_metric_policy": market_evidence["market_metric_policy"],
            "market_metric_policy_sha256": market_evidence["market_metric_policy_sha256"],
            "dataset_manifest_sha256": dataset_manifest["manifest_sha256"],
            "dataset_manifest_file_sha256": artifacts.manifest_file_sha256,
            "code_sha": code_sha,
            "protected_holdout_accessed": False,
            "immutable_inputs_mutated": False,
            "model_execution_authorized": False,
            "execution_enabled": False,
            "live_capital_authorized": False,
            "orders_submitted": 0,
        }
        binding["binding_sha256"] = _self_hash(binding, field="binding_sha256")
        _write_json(temporary_root / BINDING_NAME, binding)

        materialization: dict[str, object] = {
            "schema_version": MATERIALIZATION_SCHEMA_VERSION,
            "status": "completed",
            "outcome": "accepted",
            "dataset_version": DEFAULT_DATASET_VERSION,
            "dataset_root": DATASET_DIR_NAME,
            "dataset_manifest_sha256": dataset_manifest["manifest_sha256"],
            "dataset_manifest_file_sha256": artifacts.manifest_file_sha256,
            "source_binding_sha256": binding["binding_sha256"],
            "split_geometry_sha256": geometry.geometry_sha256,
            "market_context_count": market_evidence["market_context_count"],
            "universe_snapshot_count": market_evidence["universe_snapshot_count"],
            "market_metric_policy_sha256": market_evidence["market_metric_policy_sha256"],
            "total_rows": dataset_manifest["total_rows"],
            "earliest_decision_timestamp_ms": dataset_manifest["earliest_decision_timestamp_ms"],
            "latest_decision_timestamp_ms": dataset_manifest["latest_decision_timestamp_ms"],
            "wh01_ready": True,
            "wh01_blocker": None,
            "protected_holdout_accessed": False,
            "immutable_inputs_mutated": False,
            "model_execution_authorized": False,
            "execution_enabled": False,
            "live_capital_authorized": False,
            "orders_submitted": 0,
        }
        materialization["materialization_sha256"] = _self_hash(
            materialization,
            field="materialization_sha256",
        )
        _write_json(temporary_root / MATERIALIZATION_MANIFEST_NAME, materialization)
        checksum_paths = [
            temporary_root / BINDING_NAME,
            temporary_root / MATERIALIZATION_MANIFEST_NAME,
            dataset_root / "manifest.json",
            dataset_root / "sources.json",
            dataset_root / "universe" / "history.jsonl",
            *(
                dataset_root / Path(str(item["relative_path"]))
                for item in dataset_manifest["partitions"]
            ),
        ]
        checksum_lines = [
            f"{sha256_file(path)}  {path.relative_to(temporary_root).as_posix()}"
            for path in sorted(checksum_paths)
        ]
        _write_new(
            temporary_root / CHECKSUM_NAME,
            ("\n".join(checksum_lines) + "\n").encode("utf-8"),
        )
        _write_json(
            temporary_root / VERIFICATION_NAME,
            {
                "schema_version": MATERIALIZATION_SCHEMA_VERSION,
                "status": "verified",
                "outcome": "accepted",
                "materialization_sha256": materialization["materialization_sha256"],
                "source_binding_sha256": binding["binding_sha256"],
                "dataset_manifest_sha256": dataset_manifest["manifest_sha256"],
                "total_rows": dataset_manifest["total_rows"],
                "wh01_ready": True,
                "protected_holdout_accessed": False,
                "orders_submitted": 0,
            },
        )
        verify_production_materialization(temporary_root)
        temporary_root.replace(output_root)
        return verify_production_materialization(output_root)
    except Exception:
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise


def verify_production_materialization(output_root: Path) -> dict[str, object]:  # noqa: C901
    if output_root.is_symlink() or not output_root.is_dir():
        raise ProductionDatasetMaterializationError(
            "materialization root must be a regular directory"
        )
    dataset_root = output_root / DATASET_DIR_NAME
    binding = _load_json(output_root / BINDING_NAME, field="source binding")
    binding_hash = binding.get("binding_sha256")
    if (
        not isinstance(binding_hash, str)
        or _self_hash(binding, field="binding_sha256") != binding_hash
    ):
        raise ProductionDatasetMaterializationError("source binding self hash mismatch")
    materialization = _load_json(
        output_root / MATERIALIZATION_MANIFEST_NAME,
        field="materialization manifest",
    )
    materialization_hash = materialization.get("materialization_sha256")
    if (
        not isinstance(materialization_hash, str)
        or _self_hash(
            materialization,
            field="materialization_sha256",
        )
        != materialization_hash
    ):
        raise ProductionDatasetMaterializationError("materialization manifest self hash mismatch")
    dataset_manifest = _dataset_manifest(dataset_root / "manifest.json")
    _verify_partitions(dataset_root, dataset_manifest)
    if binding.get("dataset_manifest_sha256") != dataset_manifest.get("manifest_sha256"):
        raise ProductionDatasetMaterializationError("binding dataset identity mismatch")
    if materialization.get("dataset_manifest_sha256") != dataset_manifest.get("manifest_sha256"):
        raise ProductionDatasetMaterializationError("materialization dataset identity mismatch")
    if binding.get("source_binding_sha256") is not None:
        raise ProductionDatasetMaterializationError("unexpected nested binding identity")
    if materialization.get("source_binding_sha256") != binding_hash:
        raise ProductionDatasetMaterializationError("materialization source binding mismatch")
    metric_policy = binding.get("market_metric_policy")
    metric_policy_sha256 = binding.get("market_metric_policy_sha256")
    if not isinstance(metric_policy, dict) or not isinstance(metric_policy_sha256, str):
        raise ProductionDatasetMaterializationError("market metric policy binding is missing")
    policy_seed = dict(metric_policy)
    claimed_policy_sha256 = policy_seed.pop("policy_sha256", None)
    if (
        claimed_policy_sha256 != metric_policy_sha256
        or canonical_sha256(policy_seed) != metric_policy_sha256
    ):
        raise ProductionDatasetMaterializationError("market metric policy hash mismatch")
    if materialization.get("market_metric_policy_sha256") != metric_policy_sha256:
        raise ProductionDatasetMaterializationError("materialization metric policy mismatch")
    for payload, field in (
        (binding, "source binding"),
        (materialization, "materialization manifest"),
    ):
        if payload.get("protected_holdout_accessed") is not False:
            raise ProductionDatasetMaterializationError(f"{field} accessed holdout")
        if payload.get("immutable_inputs_mutated") is not False:
            raise ProductionDatasetMaterializationError(f"{field} mutated immutable inputs")
        if payload.get("model_execution_authorized") is not False:
            raise ProductionDatasetMaterializationError(f"{field} authorizes model execution")
        if payload.get("execution_enabled") is not False:
            raise ProductionDatasetMaterializationError(f"{field} enables execution")
        if payload.get("live_capital_authorized") is not False:
            raise ProductionDatasetMaterializationError(f"{field} authorizes live capital")
        if payload.get("orders_submitted") != 0:
            raise ProductionDatasetMaterializationError(f"{field} submitted orders")
    if (
        materialization.get("wh01_ready") is not True
        or materialization.get("wh01_blocker") is not None
    ):
        raise ProductionDatasetMaterializationError("WH-01 terminal state mismatch")
    checksum_path = output_root / CHECKSUM_NAME
    if checksum_path.is_symlink() or not checksum_path.is_file():
        raise ProductionDatasetMaterializationError("materialization checksum is missing")
    expected_lines: set[str] = set()
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, separator, logical_name = line.partition("  ")
        if not separator:
            raise ProductionDatasetMaterializationError("invalid checksum line")
        path = _safe_member(output_root, logical_name)
        if sha256_file(path) != digest:
            raise ProductionDatasetMaterializationError("materialization checksum mismatch")
        expected_lines.add(line)
    if not expected_lines:
        raise ProductionDatasetMaterializationError("materialization checksum is empty")
    verification = _load_json(output_root / VERIFICATION_NAME, field="verification report")
    if (
        verification.get("outcome") != "accepted"
        or verification.get("materialization_sha256") != materialization_hash
        or verification.get("source_binding_sha256") != binding_hash
        or verification.get("dataset_manifest_sha256") != dataset_manifest.get("manifest_sha256")
        or verification.get("wh01_ready") is not True
        or verification.get("protected_holdout_accessed") is not False
        or verification.get("orders_submitted") != 0
    ):
        raise ProductionDatasetMaterializationError("verification report mismatch")
    return {
        "status": "completed",
        "outcome": "accepted",
        "output_root": str(output_root),
        "materialization_sha256": materialization_hash,
        "source_binding_sha256": binding_hash,
        "dataset_manifest_sha256": dataset_manifest["manifest_sha256"],
        "dataset_manifest_file_sha256": sha256_file(dataset_root / "manifest.json"),
        "total_rows": dataset_manifest["total_rows"],
        "partition_count": len(dataset_manifest["partitions"]),
        "earliest_decision_timestamp_ms": dataset_manifest["earliest_decision_timestamp_ms"],
        "latest_decision_timestamp_ms": dataset_manifest["latest_decision_timestamp_ms"],
        "wh01_ready": True,
        "wh01_blocker": None,
        "protected_holdout_accessed": False,
        "model_execution_authorized": False,
        "execution_enabled": False,
        "live_capital_authorized": False,
        "orders_submitted": 0,
    }


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bind production Market Evidence and Liquid20, then materialize WH-01."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    materialize = commands.add_parser("materialize")
    materialize.add_argument("--output-root", type=Path, required=True)
    materialize.add_argument("--market-package-root", type=Path, required=True)
    materialize.add_argument("--accepted-import-root", type=Path, required=True)
    materialize.add_argument("--code-sha", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        if args.command == "materialize":
            result = materialize_production_dataset(
                output_root=args.output_root,
                market_package_root=args.market_package_root,
                accepted_import_root=args.accepted_import_root,
                code_sha=args.code_sha,
            )
        else:
            result = verify_production_materialization(args.output_root)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, ProductionDatasetMaterializationError) as exc:
        print(f"WH-01 production materialization failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
