from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.contracts import integer_value
from ai_platform.research.liquidations.staging import GateResult, StagingThresholds, sha256_file


DEFAULT_MULTI_SOURCE_ACCEPTANCE_POLICY_PATH = Path(
    "ai_platform/research/liquidations/multi-source-acceptance-policy-v1.json"
)


def _mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be an object")
    return value


def _sequence(value: object, *, field: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a list")
    return value


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field} must be a non-empty string")
    return value.strip()


def _number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise TypeError(f"{field} must be numeric")
    parsed = float(value)
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        raise ValueError(f"{field} must be finite")
    return parsed


def _boolean(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be a boolean")
    return value


def _non_negative_int(value: object, *, field: str) -> int:
    parsed = integer_value(value, field=field)
    if parsed < 0:
        raise ValueError(f"{field} must be >= 0")
    return parsed


def _load_json(path: Path, *, field: str) -> Mapping[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return _mapping(json.load(handle), field=field)


def _artifact_name(value: object, *, field: str) -> str:
    name = _text(value, field=field)
    if Path(name).name != name:
        raise ValueError(f"{field} must not contain directories")
    return name


def _valid_hex(value: str, *, length: int) -> bool:
    return len(value) == length and all(character in "0123456789abcdef" for character in value)


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def _latency_metrics(
    latency: Mapping[str, object],
    *,
    threshold_ms: int,
) -> tuple[int, float]:
    count = integer_value(latency["count"], field="stats.latency.count")
    buckets = _mapping(latency["buckets"], field="stats.latency.buckets")
    over = 0
    for label, raw_count in buckets.items():
        if label.startswith("gt_"):
            bound = int(label.removeprefix("gt_").removesuffix("_ms"))
            if bound >= threshold_ms:
                over += integer_value(raw_count, field=f"stats.latency.buckets.{label}")
        elif label.startswith("le_"):
            bound = int(label.removeprefix("le_").removesuffix("_ms"))
            if bound > threshold_ms:
                over += integer_value(raw_count, field=f"stats.latency.buckets.{label}")
    return count, over / count if count else 0.0


@dataclass(frozen=True, slots=True)
class SourceAcceptancePolicy:
    source_id: str
    endpoint: str
    clock_endpoint: str
    source_semantics: Mapping[str, object]
    minimum_events_total: int
    minimum_observed_symbols: int
    thresholds: StagingThresholds

    @classmethod
    def from_mapping(
        cls,
        source_id: str,
        payload: Mapping[str, object],
    ) -> SourceAcceptancePolicy:
        return cls(
            source_id=source_id,
            endpoint=_text(payload["endpoint"], field=f"sources.{source_id}.endpoint"),
            clock_endpoint=_text(
                payload["clock_endpoint"],
                field=f"sources.{source_id}.clock_endpoint",
            ),
            source_semantics=dict(
                _mapping(
                    payload["source_semantics"],
                    field=f"sources.{source_id}.source_semantics",
                )
            ),
            minimum_events_total=_non_negative_int(
                payload["minimum_events_total"],
                field=f"sources.{source_id}.minimum_events_total",
            ),
            minimum_observed_symbols=_non_negative_int(
                payload["minimum_observed_symbols"],
                field=f"sources.{source_id}.minimum_observed_symbols",
            ),
            thresholds=StagingThresholds.from_mapping(
                _mapping(
                    payload["thresholds"],
                    field=f"sources.{source_id}.thresholds",
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class MultiSourceAcceptancePolicy:
    policy_id: str
    manifest_type: str
    profile_name: str
    symbols: tuple[str, ...]
    minimum_duration_seconds: float
    requirements: Mapping[str, bool]
    deduplicate_between_exchanges: bool
    sum_events_without_source_labels: bool
    minimum_union_observed_symbols: int
    minimum_intersection_observed_symbols: int
    sources: tuple[SourceAcceptancePolicy, ...]

    @classmethod
    def load(
        cls,
        path: Path = DEFAULT_MULTI_SOURCE_ACCEPTANCE_POLICY_PATH,
    ) -> MultiSourceAcceptancePolicy:
        payload = _load_json(path, field="policy")
        if integer_value(payload["schema_version"], field="schema_version") != 1:
            raise ValueError("policy schema_version must be 1")
        symbols = tuple(
            _text(symbol, field="symbols[]").upper()
            for symbol in _sequence(payload["symbols"], field="symbols")
        )
        if not symbols or len(symbols) != len(set(symbols)):
            raise ValueError("policy symbols must be non-empty and unique")
        requirements_raw = _mapping(payload["requirements"], field="requirements")
        requirements = {
            key: _boolean(value, field=f"requirements.{key}")
            for key, value in requirements_raw.items()
        }
        cross = _mapping(payload["cross_source"], field="cross_source")
        source_payloads = _mapping(payload["sources"], field="sources")
        sources = tuple(
            SourceAcceptancePolicy.from_mapping(
                source_id,
                _mapping(source_payload, field=f"sources.{source_id}"),
            )
            for source_id, source_payload in sorted(source_payloads.items())
        )
        if len(sources) < 2:
            raise ValueError("multi-source policy requires at least two sources")
        return cls(
            policy_id=_text(payload["policy_id"], field="policy_id"),
            manifest_type=_text(payload["manifest_type"], field="manifest_type"),
            profile_name=_text(payload["profile_name"], field="profile_name"),
            symbols=symbols,
            minimum_duration_seconds=_number(
                payload["minimum_duration_seconds"],
                field="minimum_duration_seconds",
            ),
            requirements=requirements,
            deduplicate_between_exchanges=_boolean(
                cross["deduplicate_between_exchanges"],
                field="cross_source.deduplicate_between_exchanges",
            ),
            sum_events_without_source_labels=_boolean(
                cross["sum_events_without_source_labels"],
                field="cross_source.sum_events_without_source_labels",
            ),
            minimum_union_observed_symbols=_non_negative_int(
                cross["minimum_union_observed_symbols"],
                field="cross_source.minimum_union_observed_symbols",
            ),
            minimum_intersection_observed_symbols=_non_negative_int(
                cross["minimum_intersection_observed_symbols"],
                field="cross_source.minimum_intersection_observed_symbols",
            ),
            sources=sources,
        )

    def requires(self, name: str) -> bool:
        return self.requirements.get(name, False)


@dataclass(frozen=True, slots=True)
class SourceEvaluation:
    source_id: str
    gates: tuple[GateResult, ...]
    observed_symbols: frozenset[str]
    metrics: Mapping[str, object]
    artifacts: Mapping[str, str]


class _Gates:
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix
        self.results: list[GateResult] = []

    def add(self, name: str, passed: bool, actual: object, expected: object) -> None:
        gate = f"{self.prefix}.{name}" if self.prefix else name
        self.results.append(GateResult(gate, passed, actual, expected))


def _evaluate_source(
    run_root: Path,
    *,
    manifest_source: Mapping[str, object],
    manifest_commit: str,
    expected_symbols: tuple[str, ...],
    policy: SourceAcceptancePolicy,
    require_start_end_clock: bool,
) -> SourceEvaluation:
    source_id = policy.source_id
    gates = _Gates(source_id)
    output_name = _artifact_name(
        manifest_source["output"],
        field=f"manifest.sources.{source_id}.output",
    )
    summary_name = _artifact_name(
        manifest_source["summary"],
        field=f"manifest.sources.{source_id}.summary",
    )
    output_path = run_root / output_name
    summary_path = run_root / summary_name
    summary = _load_json(summary_path, field=f"{source_id}.summary")
    source = _mapping(summary["source"], field=f"{source_id}.summary.source")
    semantics = _mapping(
        summary["source_semantics"],
        field=f"{source_id}.summary.source_semantics",
    )
    output = _mapping(summary["output"], field=f"{source_id}.summary.output")
    stats = _mapping(summary["stats"], field=f"{source_id}.summary.stats")
    latency = _mapping(stats["latency"], field=f"{source_id}.summary.stats.latency")
    events_by_symbol = _mapping(
        stats["events_by_symbol"],
        field=f"{source_id}.summary.stats.events_by_symbol",
    )
    clocks = _mapping(
        manifest_source["clock_probes"],
        field=f"manifest.sources.{source_id}.clock_probes",
    )
    start_clock = _mapping(clocks["start"], field=f"{source_id}.clock_probes.start")
    end_clock = _mapping(clocks["end"], field=f"{source_id}.clock_probes.end")

    thresholds = policy.thresholds
    duration_seconds = _number(stats["duration_ms"], field="stats.duration_ms") / 1_000
    messages = integer_value(stats["messages_received"], field="stats.messages_received")
    failures = integer_value(stats["parse_failures"], field="stats.parse_failures")
    availability = _number(stats["availability_ratio"], field="stats.availability_ratio")
    disconnect_rate = _number(
        stats["disconnects_per_hour"],
        field="stats.disconnects_per_hour",
    )
    events_parsed = integer_value(stats["events_parsed"], field="stats.events_parsed")
    events_written = integer_value(stats["events_written"], field="stats.events_written")
    duplicates = integer_value(stats["duplicates"], field="stats.duplicates")
    duplicate_ratio = duplicates / events_parsed if events_parsed else 0.0
    latency_count, latency_over_ratio = _latency_metrics(
        latency,
        threshold_ms=thresholds.latency_threshold_ms,
    )
    observed = frozenset(
        str(symbol).upper()
        for symbol, count in events_by_symbol.items()
        if integer_value(count, field=f"stats.events_by_symbol.{symbol}") > 0
    )
    expected_set = frozenset(expected_symbols)
    actual_hash = sha256_file(output_path)
    actual_size = output_path.stat().st_size
    actual_lines = _line_count(output_path)
    summary_hash = str(output["sha256"])
    summary_symbols = tuple(
        str(symbol).upper()
        for symbol in _sequence(source["symbols"], field=f"{source_id}.source.symbols")
    )

    gates.add(
        "manifest_endpoint",
        manifest_source.get("endpoint") == policy.endpoint,
        manifest_source.get("endpoint"),
        policy.endpoint,
    )
    gates.add(
        "collector_status",
        manifest_source.get("collector_status") == "completed",
        manifest_source.get("collector_status"),
        "completed",
    )
    gates.add(
        "collector_error",
        manifest_source.get("collector_error") is None,
        manifest_source.get("collector_error"),
        None,
    )
    gates.add(
        "summary_schema_version",
        summary.get("schema_version") == 1,
        summary.get("schema_version"),
        1,
    )
    gates.add(
        "summary_type",
        summary.get("summary_type") == "liquidation_data_only_staging",
        summary.get("summary_type"),
        "liquidation_data_only_staging",
    )
    gates.add(
        "run_status",
        stats.get("run_status") == "completed_duration",
        stats.get("run_status"),
        "completed_duration",
    )
    gates.add(
        "execution_disabled",
        summary.get("execution_enabled") is False,
        summary.get("execution_enabled"),
        False,
    )
    gates.add(
        "trading_credentials_absent",
        summary.get("trading_credentials_present") is False,
        summary.get("trading_credentials_present"),
        False,
    )
    gates.add(
        "collector_commit",
        summary.get("collector_commit") == manifest_commit,
        summary.get("collector_commit"),
        manifest_commit,
    )
    gates.add("source_id", source.get("id") == source_id, source.get("id"), source_id)
    gates.add(
        "endpoint",
        source.get("endpoint") == policy.endpoint,
        source.get("endpoint"),
        policy.endpoint,
    )
    gates.add("symbols", summary_symbols == expected_symbols, summary_symbols, expected_symbols)
    gates.add(
        "source_semantics",
        dict(semantics) == dict(policy.source_semantics),
        dict(semantics),
        dict(policy.source_semantics),
    )
    gates.add(
        "manifest_stats",
        manifest_source.get("stats") == stats,
        manifest_source.get("stats"),
        stats,
    )
    gates.add(
        "summary_clock_matches_start",
        summary.get("clock_probe") == start_clock,
        summary.get("clock_probe"),
        start_clock,
    )
    gates.add(
        "minimum_duration_seconds",
        duration_seconds >= thresholds.minimum_duration_seconds,
        duration_seconds,
        thresholds.minimum_duration_seconds,
    )
    gates.add(
        "minimum_messages_received",
        messages >= thresholds.minimum_messages_received,
        messages,
        thresholds.minimum_messages_received,
    )
    gates.add(
        "maximum_parse_failures",
        failures <= thresholds.maximum_parse_failures,
        failures,
        thresholds.maximum_parse_failures,
    )
    gates.add(
        "minimum_availability_ratio",
        availability >= thresholds.minimum_availability_ratio,
        availability,
        thresholds.minimum_availability_ratio,
    )
    gates.add(
        "maximum_disconnects_per_hour",
        disconnect_rate <= thresholds.maximum_disconnects_per_hour,
        disconnect_rate,
        thresholds.maximum_disconnects_per_hour,
    )
    gates.add(
        "maximum_duplicate_ratio",
        duplicate_ratio <= thresholds.maximum_duplicate_ratio,
        duplicate_ratio,
        thresholds.maximum_duplicate_ratio,
    )
    gates.add(
        "minimum_latency_samples",
        latency_count >= thresholds.minimum_latency_samples,
        latency_count,
        thresholds.minimum_latency_samples,
    )
    gates.add(
        "maximum_latency_over_threshold_ratio",
        latency_over_ratio <= thresholds.maximum_latency_over_threshold_ratio,
        latency_over_ratio,
        thresholds.maximum_latency_over_threshold_ratio,
    )
    gates.add(
        "minimum_events_total",
        events_written >= policy.minimum_events_total,
        events_written,
        policy.minimum_events_total,
    )
    gates.add(
        "minimum_observed_symbols",
        len(observed) >= policy.minimum_observed_symbols,
        len(observed),
        policy.minimum_observed_symbols,
    )
    gates.add(
        "unexpected_symbols",
        not (observed - expected_set),
        tuple(sorted(observed - expected_set)),
        (),
    )
    gates.add(
        "output_hash_format",
        _valid_hex(summary_hash, length=64),
        summary_hash,
        "64 lowercase hexadecimal characters",
    )
    gates.add("output_hash", summary_hash == actual_hash, summary_hash, actual_hash)
    gates.add(
        "output_size",
        integer_value(output["final_size_bytes"], field="output.final_size_bytes") == actual_size,
        output["final_size_bytes"],
        actual_size,
    )
    summary_lines = integer_value(output["line_count"], field="output.line_count")
    gates.add(
        "event_line_count",
        summary_lines == events_written == actual_lines,
        {
            "summary": summary_lines,
            "events_written": events_written,
            "actual": actual_lines,
        },
        "all equal",
    )
    initial_size = integer_value(output["initial_size_bytes"], field="output.initial_size_bytes")
    gates.add(
        "new_output",
        not thresholds.require_new_output or initial_size == 0,
        initial_size,
        0,
    )
    gates.add(
        "clock_start_endpoint",
        start_clock.get("server_time_url") == policy.clock_endpoint,
        start_clock.get("server_time_url"),
        policy.clock_endpoint,
    )
    gates.add(
        "clock_end_endpoint",
        end_clock.get("server_time_url") == policy.clock_endpoint,
        end_clock.get("server_time_url"),
        policy.clock_endpoint,
    )
    if require_start_end_clock:
        gates.add(
            "clock_start_synchronized",
            start_clock.get("synchronized") is True,
            start_clock.get("synchronized"),
            True,
        )
        gates.add(
            "clock_end_synchronized",
            end_clock.get("synchronized") is True,
            end_clock.get("synchronized"),
            True,
        )

    return SourceEvaluation(
        source_id=source_id,
        gates=tuple(gates.results),
        observed_symbols=observed,
        metrics={
            "duration_seconds": duration_seconds,
            "availability_ratio": availability,
            "disconnects_per_hour": disconnect_rate,
            "events_written": events_written,
            "duplicate_ratio": duplicate_ratio,
            "latency_samples": latency_count,
            "latency_over_threshold_ratio": latency_over_ratio,
            "observed_symbol_count": len(observed),
            "observed_symbols": sorted(observed),
            "missing_symbols": sorted(expected_set - observed),
        },
        artifacts={
            "output": actual_hash,
            "summary": sha256_file(summary_path),
        },
    )


def evaluate_multi_source_run(
    run_root: Path,
    *,
    policy: MultiSourceAcceptancePolicy,
) -> dict[str, Any]:
    manifest_path = run_root / "multi-source-manifest.json"
    manifest = _load_json(manifest_path, field="manifest")
    profile = _mapping(manifest["symbol_profile"], field="manifest.symbol_profile")
    manifest_sources = _mapping(manifest["sources"], field="manifest.sources")
    cross = _mapping(manifest["cross_source_policy"], field="manifest.cross_source_policy")
    manifest_commit = str(manifest.get("collector_commit", ""))
    run_id = str(manifest.get("run_id", "")).strip()
    host_id = str(manifest.get("host_id", "")).strip()
    manifest_symbols = tuple(
        str(symbol).upper()
        for symbol in _sequence(profile["symbols"], field="manifest.symbol_profile.symbols")
    )
    duration_seconds = _number(manifest["duration_ms"], field="manifest.duration_ms") / 1_000
    gates = _Gates()

    gates.add(
        "manifest_schema_version",
        manifest.get("schema_version") == 1,
        manifest.get("schema_version"),
        1,
    )
    gates.add(
        "manifest_type",
        manifest.get("manifest_type") == policy.manifest_type,
        manifest.get("manifest_type"),
        policy.manifest_type,
    )
    gates.add(
        "manifest_run_status",
        manifest.get("run_status") == "completed",
        manifest.get("run_status"),
        "completed",
    )
    gates.add(
        "execution_disabled",
        not policy.requires("execution_disabled") or manifest.get("execution_enabled") is False,
        manifest.get("execution_enabled"),
        False,
    )
    gates.add(
        "trading_credentials_absent",
        not policy.requires("trading_credentials_absent")
        or manifest.get("trading_credentials_present") is False,
        manifest.get("trading_credentials_present"),
        False,
    )
    gates.add(
        "collector_commit",
        not policy.requires("collector_commit") or _valid_hex(manifest_commit, length=40),
        manifest_commit,
        "40 lowercase hexadecimal characters",
    )
    gates.add(
        "run_id",
        not policy.requires("run_id")
        or (bool(run_id) and run_id not in {"unknown", "unspecified"}),
        run_id,
        "stable run identifier",
    )
    gates.add(
        "host_id",
        not policy.requires("host_id")
        or (bool(host_id) and host_id not in {"unknown", "unspecified"}),
        host_id,
        "non-sensitive host identifier",
    )
    gates.add(
        "profile_name",
        profile.get("name") == policy.profile_name,
        profile.get("name"),
        policy.profile_name,
    )
    gates.add(
        "profile_symbols",
        manifest_symbols == policy.symbols,
        manifest_symbols,
        policy.symbols,
    )
    gates.add(
        "profile_symbol_count",
        profile.get("symbol_count") == len(policy.symbols),
        profile.get("symbol_count"),
        len(policy.symbols),
    )
    gates.add(
        "minimum_duration_seconds",
        duration_seconds >= policy.minimum_duration_seconds,
        duration_seconds,
        policy.minimum_duration_seconds,
    )
    expected_sources = {source.source_id for source in policy.sources}
    gates.add(
        "source_set",
        set(manifest_sources) == expected_sources,
        tuple(sorted(manifest_sources)),
        tuple(sorted(expected_sources)),
    )
    gates.add(
        "deduplicate_between_exchanges",
        cross.get("deduplicate_between_exchanges") is policy.deduplicate_between_exchanges,
        cross.get("deduplicate_between_exchanges"),
        policy.deduplicate_between_exchanges,
    )
    gates.add(
        "sum_events_without_source_labels",
        cross.get("sum_events_without_source_labels") is policy.sum_events_without_source_labels,
        cross.get("sum_events_without_source_labels"),
        policy.sum_events_without_source_labels,
    )

    source_evaluations = tuple(
        _evaluate_source(
            run_root,
            manifest_source=_mapping(
                manifest_sources[source.source_id],
                field=f"manifest.sources.{source.source_id}",
            ),
            manifest_commit=manifest_commit,
            expected_symbols=policy.symbols,
            policy=source,
            require_start_end_clock=policy.requires("clock_synchronized_at_start_and_end"),
        )
        for source in policy.sources
    )
    for evaluation in source_evaluations:
        gates.results.extend(evaluation.gates)

    observed_sets = [evaluation.observed_symbols for evaluation in source_evaluations]
    union = frozenset().union(*observed_sets)
    intersection = frozenset.intersection(*observed_sets)
    gates.add(
        "minimum_union_observed_symbols",
        len(union) >= policy.minimum_union_observed_symbols,
        len(union),
        policy.minimum_union_observed_symbols,
    )
    gates.add(
        "minimum_intersection_observed_symbols",
        len(intersection) >= policy.minimum_intersection_observed_symbols,
        len(intersection),
        policy.minimum_intersection_observed_symbols,
    )

    passed = all(gate.passed for gate in gates.results)
    return {
        "schema_version": 1,
        "report_type": "liquidation_multi_source_acceptance_evaluation",
        "policy_id": policy.policy_id,
        "run_id": run_id,
        "host_id": host_id,
        "passed": passed,
        "gates": [gate.as_json_dict() for gate in gates.results],
        "failed_gates": [gate.gate for gate in gates.results if not gate.passed],
        "coverage": {
            "union_observed_symbols": sorted(union),
            "intersection_observed_symbols": sorted(intersection),
            "missing_from_union": sorted(set(policy.symbols) - union),
        },
        "sources": {
            evaluation.source_id: {
                "metrics": dict(evaluation.metrics),
                "artifacts": dict(evaluation.artifacts),
            }
            for evaluation in source_evaluations
        },
        "artifacts": {"manifest": sha256_file(manifest_path)},
    }
