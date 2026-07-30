from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.wickhunter import production_market_evidence as core
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import AvailableMetric, MarketContextSnapshot
from ai_platform.wickhunter.dataset import load_accepted_import, normalize_historical_event
from ai_platform.wickhunter.materialization import (
    MARKET_CONTEXT_ROW_SCHEMA,
    MATERIALIZATION_REQUEST_SCHEMA,
    UNIVERSE_HISTORY_ROW_SCHEMA,
    load_materialization_request,
    preflight_materialization_package,
)
from ai_platform.wickhunter.production_market_evidence_service import (
    EXPECTED_AUTHORITY,
    PACKAGE_CANDLE_INDEX_NAME,
    PACKAGE_INSTRUMENT_SNAPSHOTS_NAME,
    PACKAGE_MANIFEST_NAME,
    PACKAGE_MARKET_QUALITY_NAME,
    verify_immutable_package,
)
from ai_platform.wickhunter.universe import DynamicUniverseSnapshot, UniverseInstrumentDecision


POLICY_SCHEMA = "wickhunter-production-market-evidence-wh01-policy-v1"
INPUT_MANIFEST_SCHEMA = "wickhunter-production-market-evidence-wh01-input-manifest-v1"
REPORT_SCHEMA = "wickhunter-production-market-evidence-wh01-report-v1"
MATERIALIZATION_REQUEST_NAME = "materialization-request.json"
MARKET_CONTEXT_NAME = "market-context.jsonl"
UNIVERSE_HISTORY_NAME = "universe-history.jsonl"
INPUT_MANIFEST_NAME = "wh01-input-manifest.json"
CHECKSUM_NAME = "artifact-sha256.txt"
REPORT_NAME = "verification-report.json"
TIMEFRAME_MS = 300_000


class WickHunterInputAdapterError(RuntimeError):
    """Raised when WH-01 inputs cannot be created without ambiguity or leakage."""


@dataclass(frozen=True, slots=True)
class MetricLookbacks:
    quote_volume_rows: int
    vwap_rows: int
    vwma_rows: int
    atr_rows: int
    volatility_rows: int
    wick_rows: int
    trend_rows: int

    @property
    def maximum_rows(self) -> int:
        return max(
            self.quote_volume_rows,
            self.vwap_rows,
            self.vwma_rows,
            self.atr_rows + 1,
            self.volatility_rows + 1,
            self.wick_rows,
            self.trend_rows,
        )


@dataclass(frozen=True, slots=True)
class Wh01AdapterPolicy:
    schema_version: str
    policy_version: str
    code_sha: str
    timeframe: str
    decision_cadence_ms: int
    lookbacks: MetricLookbacks
    source_aggregation: str
    required_sources: tuple[str, ...]
    burst_window_ms: int
    partition_span_ms: int
    minimum_history_events: int
    maximum_source_age_ms: int
    minimum_quote_volume_24h_usd: Decimal
    maximum_spread_bps: Decimal | None
    minimum_candle_history_rows: int
    minimum_healthy_liquidation_sources: int
    split_name: str
    split_start_ms: int
    split_end_ms: int
    label_horizon_ms: int
    embargo_ms: int
    protected_holdout_start_ms: int

    def __post_init__(self) -> None:
        if self.schema_version != POLICY_SCHEMA:
            raise WickHunterInputAdapterError(f"schema_version must be {POLICY_SCHEMA}")
        if not self.policy_version or self.timeframe != "5m":
            raise WickHunterInputAdapterError("policy identity or timeframe is invalid")
        if len(self.code_sha) != 40 or any(character not in "0123456789abcdef" for character in self.code_sha):
            raise WickHunterInputAdapterError("code_sha must be a lowercase 40-character Git SHA")
        if self.decision_cadence_ms != TIMEFRAME_MS:
            raise WickHunterInputAdapterError("WH-01 decision cadence must be 5m")
        if self.required_sources != core.EXPECTED_SOURCES:
            raise WickHunterInputAdapterError("policy must require source-separated Bybit and Binance evidence")
        if self.source_aggregation != "source_balanced_mean_require_all":
            raise WickHunterInputAdapterError("unsupported source aggregation policy")
        if self.lookbacks.maximum_rows < 288:
            raise WickHunterInputAdapterError("metric policy must require at least 24 hours of 5m data")
        for value in (
            self.burst_window_ms,
            self.partition_span_ms,
            self.minimum_history_events,
            self.maximum_source_age_ms,
            self.minimum_candle_history_rows,
            self.minimum_healthy_liquidation_sources,
        ):
            if value <= 0:
                raise WickHunterInputAdapterError("positive policy values must be greater than zero")
        if self.minimum_quote_volume_24h_usd < 0:
            raise WickHunterInputAdapterError("minimum quote volume must be non-negative")
        if self.maximum_spread_bps is not None and self.maximum_spread_bps < 0:
            raise WickHunterInputAdapterError("maximum spread must be non-negative")
        if self.split_start_ms <= 0 or self.split_end_ms <= self.split_start_ms:
            raise WickHunterInputAdapterError("split geometry is invalid")
        if self.split_end_ms > self.protected_holdout_start_ms:
            raise WickHunterInputAdapterError("split geometry overlaps the protected holdout")
        if self.label_horizon_ms < 0 or self.embargo_ms < 0:
            raise WickHunterInputAdapterError("label horizon and embargo must be non-negative")


def _object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WickHunterInputAdapterError(f"{field} must be an object")
    return value


def _list(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise WickHunterInputAdapterError(f"{field} must be a list")
    return value


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise WickHunterInputAdapterError(f"{field} must be an integer")
    try:
        return int(value)
    except ValueError as exc:
        raise WickHunterInputAdapterError(f"{field} must be an integer") from exc


def _decimal(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool):
        raise WickHunterInputAdapterError(f"{field} must be decimal-compatible")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise WickHunterInputAdapterError(f"{field} must be decimal-compatible") from exc
    if not result.is_finite():
        raise WickHunterInputAdapterError(f"{field} must be finite")
    return result


def _load_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise WickHunterInputAdapterError(f"{field} must be a regular file")
    try:
        return _object(json.loads(path.read_text(encoding="utf-8")), field=field)
    except (OSError, json.JSONDecodeError) as exc:
        raise WickHunterInputAdapterError(f"unable to read {field}: {exc}") from exc


def _load_ndjson(path: Path, *, field: str, maximum_rows: int = 100_000) -> list[dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise WickHunterInputAdapterError(f"{field} must be a regular file")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise WickHunterInputAdapterError(f"{field} contains a blank row at {line_number}")
            if line_number > maximum_rows:
                raise WickHunterInputAdapterError(f"{field} exceeded the bounded row limit")
            try:
                rows.append(_object(json.loads(line), field=f"{field} row {line_number}"))
            except json.JSONDecodeError as exc:
                raise WickHunterInputAdapterError(f"{field} row {line_number} is invalid JSON") from exc
    return rows


def load_policy(path: Path) -> Wh01AdapterPolicy:
    payload = _load_json(path, field="WH-01 adapter policy")
    lookbacks = _object(payload.get("metric_lookback_rows"), field="metric_lookback_rows")
    universe = _object(payload.get("universe"), field="universe")
    dataset = _object(payload.get("dataset"), field="dataset")
    split = _object(dataset.get("split"), field="dataset.split")
    maximum_spread = universe.get("maximum_spread_bps")
    return Wh01AdapterPolicy(
        schema_version=str(payload.get("schema_version", "")),
        policy_version=str(payload.get("policy_version", "")),
        code_sha=str(payload.get("code_sha", "")),
        timeframe=str(payload.get("timeframe", "")),
        decision_cadence_ms=_integer(payload.get("decision_cadence_ms"), field="decision_cadence_ms"),
        lookbacks=MetricLookbacks(
            quote_volume_rows=_integer(lookbacks.get("quote_volume_24h_usd"), field="quote_volume_24h_usd"),
            vwap_rows=_integer(lookbacks.get("vwap"), field="vwap"),
            vwma_rows=_integer(lookbacks.get("vwma"), field="vwma"),
            atr_rows=_integer(lookbacks.get("atr_ratio"), field="atr_ratio"),
            volatility_rows=_integer(lookbacks.get("volatility_ratio"), field="volatility_ratio"),
            wick_rows=_integer(lookbacks.get("wick_ratio"), field="wick_ratio"),
            trend_rows=_integer(lookbacks.get("trend_return_ratio"), field="trend_return_ratio"),
        ),
        source_aggregation=str(payload.get("source_aggregation", "")),
        required_sources=tuple(str(source) for source in _list(payload.get("required_sources"), field="required_sources")),
        burst_window_ms=_integer(dataset.get("burst_window_ms"), field="dataset.burst_window_ms"),
        partition_span_ms=_integer(dataset.get("partition_span_ms"), field="dataset.partition_span_ms"),
        minimum_history_events=_integer(dataset.get("minimum_history_events"), field="dataset.minimum_history_events"),
        maximum_source_age_ms=_integer(dataset.get("maximum_source_age_ms"), field="dataset.maximum_source_age_ms"),
        minimum_quote_volume_24h_usd=_decimal(universe.get("minimum_quote_volume_24h_usd"), field="minimum_quote_volume_24h_usd"),
        maximum_spread_bps=(None if maximum_spread is None else _decimal(maximum_spread, field="maximum_spread_bps")),
        minimum_candle_history_rows=_integer(universe.get("minimum_candle_history_rows"), field="minimum_candle_history_rows"),
        minimum_healthy_liquidation_sources=_integer(universe.get("minimum_healthy_liquidation_sources"), field="minimum_healthy_liquidation_sources"),
        split_name=str(split.get("name", "")),
        split_start_ms=_integer(split.get("start_ms"), field="dataset.split.start_ms"),
        split_end_ms=_integer(split.get("end_ms"), field="dataset.split.end_ms"),
        label_horizon_ms=_integer(dataset.get("label_horizon_ms"), field="dataset.label_horizon_ms"),
        embargo_ms=_integer(dataset.get("embargo_ms"), field="dataset.embargo_ms"),
        protected_holdout_start_ms=_integer(dataset.get("protected_holdout_start_ms"), field="dataset.protected_holdout_start_ms"),
    )


def _safe_member(root: Path, logical_name: str) -> Path:
    relative = Path(logical_name)
    if relative.is_absolute() or ".." in relative.parts:
        raise WickHunterInputAdapterError("artifact path must remain relative")
    current = root.resolve()
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise WickHunterInputAdapterError("artifact path traverses a symlink")
    resolved = current.resolve()
    if root.resolve() not in resolved.parents:
        raise WickHunterInputAdapterError("artifact path escapes the run root")
    if not resolved.is_file():
        raise WickHunterInputAdapterError("artifact path is not a regular file")
    return resolved


def _balanced(values: Sequence[Decimal], *, field: str) -> Decimal:
    if len(values) != len(core.EXPECTED_SOURCES):
        raise WickHunterInputAdapterError(f"{field} does not cover every required source")
    return sum(values, Decimal(0)) / Decimal(len(values))


def _mean(values: Sequence[Decimal], *, field: str) -> Decimal:
    if not values:
        raise WickHunterInputAdapterError(f"{field} has no values")
    return sum(values, Decimal(0)) / Decimal(len(values))


def _window(candles: Sequence[Mapping[str, Any]], end_ms: int, rows: int) -> list[Mapping[str, Any]]:
    eligible = [row for row in candles if _integer(row.get("close_time_ms_exclusive"), field="candle close") <= end_ms]
    if len(eligible) < rows:
        raise WickHunterInputAdapterError("missing required completed-candle pre-roll")
    selected = eligible[-rows:]
    expected_start = end_ms - rows * TIMEFRAME_MS
    if _integer(selected[0].get("open_time_ms"), field="candle open") != expected_start:
        raise WickHunterInputAdapterError("completed-candle lookback is discontinuous")
    for index, row in enumerate(selected):
        if _integer(row.get("open_time_ms"), field="candle open") != expected_start + index * TIMEFRAME_MS:
            raise WickHunterInputAdapterError("completed-candle lookback contains a gap")
        if _integer(row.get("close_time_ms_exclusive"), field="candle close") > end_ms:
            raise WickHunterInputAdapterError("incomplete candle entered a completed-candle window")
    return selected


def _source_metrics(candles: Sequence[Mapping[str, Any]], decision_ms: int, lookbacks: MetricLookbacks) -> dict[str, Decimal]:
    quote_rows = _window(candles, decision_ms, lookbacks.quote_volume_rows)
    vwap_rows = _window(candles, decision_ms, lookbacks.vwap_rows)
    vwma_rows = _window(candles, decision_ms, lookbacks.vwma_rows)
    atr_rows = _window(candles, decision_ms, lookbacks.atr_rows + 1)
    volatility_rows = _window(candles, decision_ms, lookbacks.volatility_rows + 1)
    wick_rows = _window(candles, decision_ms, lookbacks.wick_rows)
    trend_rows = _window(candles, decision_ms, lookbacks.trend_rows)

    quote_volume = sum((_decimal(row.get("quote_volume"), field="quote volume") for row in quote_rows), Decimal(0))
    base_volume = sum((_decimal(row.get("base_volume"), field="base volume") for row in vwap_rows), Decimal(0))
    if base_volume <= 0:
        raise WickHunterInputAdapterError("VWAP base volume must be positive")
    vwap = sum((_decimal(row.get("quote_volume"), field="quote volume") for row in vwap_rows), Decimal(0)) / base_volume
    vwma_weight = sum((_decimal(row.get("base_volume"), field="base volume") for row in vwma_rows), Decimal(0))
    if vwma_weight <= 0:
        raise WickHunterInputAdapterError("VWMA base volume must be positive")
    vwma = sum(
        (
            _decimal(row.get("close"), field="close")
            * _decimal(row.get("base_volume"), field="base volume")
            for row in vwma_rows
        ),
        Decimal(0),
    ) / vwma_weight
    true_ranges: list[Decimal] = []
    for previous, current in zip(atr_rows, atr_rows[1:], strict=True):
        previous_close = _decimal(previous.get("close"), field="previous close")
        high = _decimal(current.get("high"), field="high")
        low = _decimal(current.get("low"), field="low")
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    latest_close = _decimal(atr_rows[-1].get("close"), field="latest close")
    atr_ratio = _mean(true_ranges, field="ATR") / latest_close

    returns: list[Decimal] = []
    for previous, current in zip(volatility_rows, volatility_rows[1:], strict=True):
        previous_close = _decimal(previous.get("close"), field="previous close")
        current_close = _decimal(current.get("close"), field="current close")
        returns.append(current_close / previous_close - Decimal(1))
    return_mean = _mean(returns, field="returns")
    variance = _mean([(value - return_mean) ** 2 for value in returns], field="return variance")
    with localcontext() as context:
        context.prec = 28
        return_std = variance.sqrt()
    absolute_mean = _mean([abs(value) for value in returns], field="absolute returns")
    volatility_ratio = Decimal(0) if absolute_mean == 0 else return_std / absolute_mean

    wick_values: list[Decimal] = []
    for row in wick_rows:
        opening = _decimal(row.get("open"), field="open")
        high = _decimal(row.get("high"), field="high")
        low = _decimal(row.get("low"), field="low")
        closing = _decimal(row.get("close"), field="close")
        span = high - low
        wick_values.append(Decimal(0) if span == 0 else ((high - max(opening, closing)) + (min(opening, closing) - low)) / span)
    first_open = _decimal(trend_rows[0].get("open"), field="trend open")
    trend_return = _decimal(trend_rows[-1].get("close"), field="trend close") / first_open - Decimal(1)
    return {
        "quote_volume_24h_usd": quote_volume,
        "vwap": vwap,
        "vwma": vwma,
        "atr_ratio": atr_ratio,
        "volatility_ratio": volatility_ratio,
        "wick_ratio": _mean(wick_values, field="wick ratio"),
        "trend_return_ratio": trend_return,
        "decision_price": _decimal(candles[-1].get("close"), field="decision price"),
    }


def _quality_by_decision(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], list[Mapping[str, Any]]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        source = str(row.get("source", ""))
        symbol = str(row.get("canonical_symbol", row.get("symbol", ""))).upper()
        if source not in core.EXPECTED_SOURCES or symbol not in core.EXPECTED_SYMBOLS:
            raise WickHunterInputAdapterError("market-quality source or symbol mismatch")
        grouped[(source, symbol)].append(row)
    for values in grouped.values():
        values.sort(key=lambda row: _integer(row.get("available_at_ms"), field="quality availability"))
    return grouped


def _latest_quality(rows: Sequence[Mapping[str, Any]], decision_ms: int) -> Mapping[str, Any]:
    eligible = [row for row in rows if _integer(row.get("available_at_ms"), field="quality availability") <= decision_ms]
    if not eligible:
        raise WickHunterInputAdapterError("market-quality observation is unavailable at decision time")
    return eligible[-1]


def _liquidation_intensity(events: Sequence[Any], decision_ms: int, policy: Wh01AdapterPolicy) -> Decimal:
    history_start = decision_ms - policy.lookbacks.maximum_rows * TIMEFRAME_MS
    available = [event for event in events if history_start <= event.received_at_ms <= decision_ms]
    current_start = decision_ms - policy.burst_window_ms
    current = sum((event.notional_usd for event in available if event.received_at_ms >= current_start), Decimal(0))
    buckets: dict[int, Decimal] = defaultdict(Decimal)
    for event in available:
        if event.received_at_ms >= current_start:
            continue
        bucket = (event.received_at_ms // policy.burst_window_ms) * policy.burst_window_ms
        buckets[bucket] += event.notional_usd
    history = [value for _, value in sorted(buckets.items()) if value > 0]
    if not history:
        raise WickHunterInputAdapterError("liquidation intensity lacks historical burst evidence")
    baseline = _mean(history, field="liquidation burst history")
    return current / baseline


def _write_lines(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    if path.exists() or path.is_symlink():
        raise WickHunterInputAdapterError(f"refusing to overwrite {path.name}")
    with path.open("xb") as handle:
        for row in rows:
            handle.write(canonical_json(row).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, value: object) -> None:
    if path.exists() or path.is_symlink():
        raise WickHunterInputAdapterError(f"refusing to overwrite {path.name}")
    with path.open("xb") as handle:
        handle.write(canonical_json(value).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _copy_accepted(root: Path, destination: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise WickHunterInputAdapterError("accepted import root must be a regular directory")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise WickHunterInputAdapterError("accepted import must not contain symlinks")
    shutil.copytree(root, destination, copy_function=shutil.copy2)


def build_wh01_input_package(
    *,
    evidence_package_root: Path,
    accepted_import_roots: Sequence[Path],
    policy_path: Path,
    output_root: Path,
) -> dict[str, object]:
    if output_root.exists() or output_root.is_symlink():
        raise WickHunterInputAdapterError("WH-01 input output root already exists")
    if not accepted_import_roots:
        return {
            "schema_version": REPORT_SCHEMA,
            "status": "blocked",
            "blocker_code": "LIQUIDATION_ARCHIVE_NOT_BOUND",
            "blocker_detail": "At least one real accepted immutable liquidation import must be bound.",
            **EXPECTED_AUTHORITY,
        }
    evidence_package_root = evidence_package_root.resolve()
    verification = verify_immutable_package(evidence_package_root)
    run_root = evidence_package_root.parent
    core.verify_capture_package(run_root)
    policy = load_policy(policy_path)
    manifest = _load_json(evidence_package_root / PACKAGE_MANIFEST_NAME, field="market evidence manifest")
    capture = _object(manifest.get("capture"), field="manifest.capture")
    if manifest.get("collector_commit") != policy.code_sha:
        raise WickHunterInputAdapterError("policy code SHA does not match the captured code identity")
    if policy.split_start_ms != _integer(capture.get("decision_start_ms"), field="decision start") or policy.split_end_ms != _integer(capture.get("decision_end_ms"), field="decision end"):
        raise WickHunterInputAdapterError("policy split does not match the evidence capture interval")
    if policy.protected_holdout_start_ms != _integer(_load_json(evidence_package_root / "request.json", field="request").get("protected_holdout_start_ms"), field="protected holdout"):
        raise WickHunterInputAdapterError("policy protected holdout identity mismatch")
    if _integer(capture.get("pre_roll_ms"), field="pre-roll") < policy.lookbacks.maximum_rows * TIMEFRAME_MS:
        raise WickHunterInputAdapterError("captured pre-roll is shorter than the declared maximum metric lookback")

    candle_index = _load_json(evidence_package_root / PACKAGE_CANDLE_INDEX_NAME, field="candle index")
    artifacts = _list(candle_index, field="candle index")
    candles: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for raw in artifacts:
        artifact = _object(raw, field="candle artifact")
        source = str(artifact.get("source", ""))
        symbol = str(artifact.get("symbol", "")).upper()
        normalized = _object(artifact.get("normalized_file"), field="normalized candle file")
        path = _safe_member(run_root, str(normalized.get("logical_name", "")))
        if sha256_file(path) != normalized.get("sha256"):
            raise WickHunterInputAdapterError("normalized candle SHA-256 mismatch")
        rows = _load_ndjson(path, field=f"{source} {symbol} candles", maximum_rows=1_000)
        if len(rows) != 432:
            raise WickHunterInputAdapterError("completed-candle geometry mismatch")
        candles[(source, symbol)] = rows
    expected_keys = {(source, symbol) for source in core.EXPECTED_SOURCES for symbol in core.EXPECTED_SYMBOLS}
    if set(candles) != expected_keys:
        raise WickHunterInputAdapterError("completed-candle source-symbol coverage mismatch")

    quality_rows = _load_ndjson(evidence_package_root / PACKAGE_MARKET_QUALITY_NAME, field="market quality")
    quality = _quality_by_decision(quality_rows)
    instrument_rows = _load_ndjson(evidence_package_root / PACKAGE_INSTRUMENT_SNAPSHOTS_NAME, field="instrument history")
    active_by_symbol: dict[str, set[str]] = defaultdict(set)
    for row in instrument_rows:
        source = str(row.get("source", ""))
        symbol = str(row.get("canonical_symbol", "")).upper()
        available_at = _integer(row.get("available_at_ms"), field="instrument availability")
        if available_at <= policy.split_end_ms and row.get("active") is True:
            active_by_symbol[symbol].add(source)

    bundles = tuple(load_accepted_import(root.resolve()) for root in accepted_import_roots)
    if len({bundle.selection.selection_sha256 for bundle in bundles}) != len(bundles):
        raise WickHunterInputAdapterError("duplicate accepted liquidation import selection")
    for bundle in bundles:
        selection = bundle.selection
        if selection.requested_start_ms > _integer(capture.get("pre_roll_start_ms"), field="pre-roll start") or selection.requested_end_ms < policy.split_end_ms:
            raise WickHunterInputAdapterError("accepted liquidation import does not cover the market-evidence interval")
        if selection.protected_holdout_start_ms != policy.protected_holdout_start_ms:
            raise WickHunterInputAdapterError("accepted import protected holdout identity mismatch")
    events = sorted(
        (normalize_historical_event(event) for bundle in bundles for event in bundle.events),
        key=lambda event: (event.received_at_ms, event.source, event.symbol, event.source_event_id),
    )
    if len({(event.source, event.source_event_id) for event in events}) != len(events):
        raise WickHunterInputAdapterError("duplicate source-labelled liquidation event")

    market_rows: list[dict[str, object]] = []
    universe_rows: list[dict[str, object]] = []
    for decision_ms in range(policy.split_start_ms, policy.split_end_ms, policy.decision_cadence_ms):
        intensity = _liquidation_intensity(events, decision_ms, policy)
        decisions: list[UniverseInstrumentDecision] = []
        for symbol in core.EXPECTED_SYMBOLS:
            metrics_by_source = {
                source: _source_metrics(candles[(source, symbol)], decision_ms, policy.lookbacks)
                for source in core.EXPECTED_SOURCES
            }
            latest_quality = {
                source: _latest_quality(quality[(source, symbol)], decision_ms)
                for source in core.EXPECTED_SOURCES
            }
            completed_close_ms = decision_ms
            metric_values = {
                name: _balanced([metrics_by_source[source][name] for source in core.EXPECTED_SOURCES], field=name)
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
            metric_values["spread_bps"] = _balanced(
                [_decimal(latest_quality[source].get("spread_bps"), field="spread_bps") for source in core.EXPECTED_SOURCES],
                field="spread_bps",
            )
            metric_values["market_wide_liquidation_intensity"] = intensity
            decision_price = _balanced(
                [metrics_by_source[source]["decision_price"] for source in core.EXPECTED_SOURCES],
                field="decision_price",
            )
            metrics: list[AvailableMetric] = []
            quality_available_at = max(
                _integer(latest_quality[source].get("available_at_ms"), field="quality availability")
                for source in core.EXPECTED_SOURCES
            )
            for name, value in sorted(metric_values.items()):
                if name == "spread_bps":
                    available_at = quality_available_at
                    metric_source = "market_quality:bybit-linear+binance-usdm:source_balanced_mean"
                elif name == "market_wide_liquidation_intensity":
                    available_at = decision_ms
                    metric_source = "accepted_liquidation_archive:market_wide"
                else:
                    available_at = completed_close_ms
                    metric_source = "completed_candle:bybit-linear+binance-usdm:source_balanced_mean"
                if available_at > decision_ms:
                    raise WickHunterInputAdapterError("metric availability exceeds decision time")
                metrics.append(AvailableMetric(name=name, value=value, available_at_ms=available_at, source=metric_source))
            snapshot = MarketContextSnapshot(
                symbol=symbol,
                decision_timestamp_ms=decision_ms,
                decision_price=decision_price,
                completed_candle_close_ms=completed_close_ms,
                metrics=tuple(metrics),
            )
            market_rows.append(
                {
                    "schema_version": MARKET_CONTEXT_ROW_SCHEMA,
                    "snapshot": json.loads(canonical_json(snapshot)),
                    "snapshot_sha256": canonical_sha256(snapshot),
                }
            )

            reasons: list[str] = []
            if active_by_symbol.get(symbol) != set(core.EXPECTED_SOURCES):
                reasons.append("instrument_source_coverage_incomplete")
            if metric_values["quote_volume_24h_usd"] < policy.minimum_quote_volume_24h_usd:
                reasons.append("quote_volume_below_minimum")
            if policy.maximum_spread_bps is not None and metric_values["spread_bps"] > policy.maximum_spread_bps:
                reasons.append("spread_above_maximum")
            if policy.minimum_candle_history_rows > policy.lookbacks.maximum_rows:
                reasons.append("insufficient_candle_history")
            healthy_liquidation_sources = {
                event.source
                for event in events
                if event.symbol.upper() == symbol
                and decision_ms - policy.maximum_source_age_ms <= event.received_at_ms <= decision_ms
            }
            if len(healthy_liquidation_sources) < policy.minimum_healthy_liquidation_sources:
                reasons.append("insufficient_healthy_liquidation_sources")
            decisions.append(
                UniverseInstrumentDecision(
                    canonical_instrument_id=f"wickhunter:source-balanced-perpetual:{symbol}",
                    canonical_symbol=symbol,
                    included=not reasons,
                    reason_codes=("eligible",) if not reasons else tuple(sorted(set(reasons))),
                )
            )
        universe = DynamicUniverseSnapshot(
            schema_version="wickhunter-dynamic-universe-v1",
            policy_version=policy.policy_version,
            selected_at_ms=decision_ms,
            decisions=tuple(sorted(decisions, key=lambda decision: decision.canonical_instrument_id)),
        )
        universe_rows.append(
            {
                "schema_version": UNIVERSE_HISTORY_ROW_SCHEMA,
                "snapshot": json.loads(canonical_json(universe)),
                "snapshot_sha256": universe.snapshot_hash,
            }
        )

    output_parent = output_root.resolve().parent
    output_parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_parent))
    try:
        accepted_references: list[dict[str, str]] = []
        for bundle, source_root in sorted(zip(bundles, accepted_import_roots, strict=True), key=lambda pair: pair[0].selection.import_run_id):
            relative = Path("accepted-imports") / bundle.selection.import_run_id
            _copy_accepted(source_root.resolve(), temporary / relative)
            accepted_references.append(
                {
                    "relative_path": relative.as_posix(),
                    "import_run_id": bundle.selection.import_run_id,
                    "selection_sha256": bundle.selection.selection_sha256,
                }
            )
        market_path = temporary / MARKET_CONTEXT_NAME
        universe_path = temporary / UNIVERSE_HISTORY_NAME
        _write_lines(market_path, market_rows)
        _write_lines(universe_path, universe_rows)
        request = {
            "schema_version": MATERIALIZATION_REQUEST_SCHEMA,
            "accepted_imports": accepted_references,
            "market_context": {"relative_path": MARKET_CONTEXT_NAME, "sha256": sha256_file(market_path)},
            "universe_history": {"relative_path": UNIVERSE_HISTORY_NAME, "sha256": sha256_file(universe_path)},
            "dataset": {
                "dataset_version": f"wickhunter-production-{verification['run_id']}-wh01-v1",
                "code_sha": policy.code_sha,
                "burst_window_ms": policy.burst_window_ms,
                "partition_span_ms": policy.partition_span_ms,
                "minimum_history_events": policy.minimum_history_events,
                "maximum_source_age_ms": policy.maximum_source_age_ms,
                "split_geometry": {
                    "geometry_version": f"{policy.policy_version}-split-v1",
                    "windows": [{"name": policy.split_name, "start_ms": policy.split_start_ms, "end_ms": policy.split_end_ms}],
                    "label_horizon_ms": policy.label_horizon_ms,
                    "embargo_ms": policy.embargo_ms,
                    "protected_holdout_start_ms": policy.protected_holdout_start_ms,
                },
            },
            "trading_credentials_present": False,
            "trading_authorized": False,
            "execution_enabled": False,
            "model_execution_authorized": False,
            "live_capital_authorized": False,
        }
        request_path = temporary / MATERIALIZATION_REQUEST_NAME
        _write_json(request_path, request)
        parsed = load_materialization_request(request_path)
        preflight = preflight_materialization_package(package_root=temporary, request=parsed)
        if preflight.status != "ready":
            raise WickHunterInputAdapterError(f"existing WH-01 preflight blocked the generated package: {preflight.missing_paths}")
        input_manifest = {
            "schema_version": INPUT_MANIFEST_SCHEMA,
            "run_id": verification["run_id"],
            "market_evidence_manifest_sha256": verification["manifest_sha256"],
            "policy_sha256": sha256_file(policy_path),
            "materialization_request_sha256": sha256_file(request_path),
            "market_context_sha256": sha256_file(market_path),
            "universe_history_sha256": sha256_file(universe_path),
            "accepted_import_selection_sha256s": sorted(bundle.selection.selection_sha256 for bundle in bundles),
            "market_snapshot_count": len(market_rows),
            "universe_snapshot_count": len(universe_rows),
            "source_aggregation": policy.source_aggregation,
            "required_sources": list(policy.required_sources),
            "maximum_metric_lookback_rows": policy.lookbacks.maximum_rows,
            "preflight_status": preflight.status,
            "authorities": EXPECTED_AUTHORITY,
        }
        input_manifest["manifest_sha256"] = canonical_sha256(input_manifest)
        manifest_path = temporary / INPUT_MANIFEST_NAME
        _write_json(manifest_path, input_manifest)
        identities = {
            MARKET_CONTEXT_NAME: sha256_file(market_path),
            UNIVERSE_HISTORY_NAME: sha256_file(universe_path),
            MATERIALIZATION_REQUEST_NAME: sha256_file(request_path),
            INPUT_MANIFEST_NAME: sha256_file(manifest_path),
        }
        checksum_path = temporary / CHECKSUM_NAME
        checksum_path.write_text(
            "".join(f"{digest}  {name}\n" for name, digest in sorted(identities.items())),
            encoding="utf-8",
        )
        report = {
            "schema_version": REPORT_SCHEMA,
            "status": "ready",
            "run_id": verification["run_id"],
            "materialization_request": MATERIALIZATION_REQUEST_NAME,
            "market_snapshot_count": len(market_rows),
            "universe_snapshot_count": len(universe_rows),
            "manifest_sha256": input_manifest["manifest_sha256"],
            "existing_wh01_preflight": preflight.as_json_dict(),
            **EXPECTED_AUTHORITY,
        }
        _write_json(temporary / REPORT_NAME, report)
        temporary.replace(output_root)
        return {**report, "output_root": str(output_root)}
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build verified WH-01 inputs from production market evidence")
    parser.add_argument("--evidence-package-root", type=Path, required=True)
    parser.add_argument("--accepted-import-root", type=Path, action="append", default=[])
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = build_wh01_input_package(
            evidence_package_root=args.evidence_package_root,
            accepted_import_roots=args.accepted_import_root,
            policy_path=args.policy,
            output_root=args.output_root,
        )
        print(canonical_json(result))
        return 0 if result.get("status") == "ready" else 2
    except Exception as exc:
        print(
            json.dumps(
                {
                    "schema_version": REPORT_SCHEMA,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    **EXPECTED_AUTHORITY,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
