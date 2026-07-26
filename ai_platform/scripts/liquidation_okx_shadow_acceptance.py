from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
import urllib.parse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ai_platform.research.liquidations.contracts import event_from_json_dict
from ai_platform.research.liquidations.staging import GateResult, sha256_file, write_json_atomic
from ai_platform.scripts.liquidation_okx_collector import (
    collect_okx_liquidations,
    fetch_okx_instruments,
    probe_okx_clock,
    trading_credentials_present,
)
from ai_platform.scripts.liquidation_okx_shadow_smoke import (
    EVENTS_NAME,
    INSTRUMENTS_NAME,
    SOURCE_ID,
    SUMMARY_NAME,
    _artifact_entry,
    _bounded_error,
    _canonical_hash,
    _instrument_contracts,
    _integer,
    _latency_over_ratio,
    _load_json,
    _mapping,
    _number,
    _sequence,
    _text,
    _valid_commit,
    _valid_file_name,
)


POLICY_PATH = Path(
    "ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json"
)
MANIFEST_NAME = "okx-shadow-acceptance-manifest.json"
REPORT_NAME = "okx-shadow-acceptance-report.json"
SHA256_NAME = "artifact-sha256.txt"
PACKAGE_FILES = (
    EVENTS_NAME,
    SUMMARY_NAME,
    INSTRUMENTS_NAME,
    MANIFEST_NAME,
    REPORT_NAME,
)
ACTIVITY_GATES = frozenset(
    {
        "minimum_latency_samples",
        "minimum_events_total",
        "minimum_observed_symbols",
    }
)


@dataclass(frozen=True, slots=True)
class OkxShadowAcceptancePolicy:
    policy_id: str
    source: str
    symbols: tuple[str, ...]
    minimum_duration_seconds: int
    required_host_class: str
    github_hosted_runner_allowed: bool
    websocket_endpoint: str
    clock_endpoint: str
    instruments_endpoint: str
    source_semantics: Mapping[str, object]
    thresholds: Mapping[str, object]
    requirements: Mapping[str, object]
    durability: Mapping[str, object]
    outcomes: Mapping[str, object]

    @classmethod
    def load(  # noqa: C901 - frozen policy validation stays fail-closed in one loader
        cls, path: Path = POLICY_PATH
    ) -> OkxShadowAcceptancePolicy:
        payload = _load_json(path, field="policy")
        if _integer(payload.get("schema_version"), field="schema_version") != 1:
            raise ValueError("policy schema_version must be 1")
        if payload.get("classification") != "shadow_source_operational_acceptance":
            raise ValueError("unexpected policy classification")
        endpoints = _mapping(payload.get("endpoints"), field="endpoints")
        host = _mapping(payload.get("host"), field="host")
        symbols = tuple(
            _text(item, field="symbols[]").upper()
            for item in _sequence(payload.get("symbols"), field="symbols")
        )
        if not symbols or len(symbols) != len(set(symbols)):
            raise ValueError("policy symbols must be non-empty and unique")
        minimum_duration_seconds = _integer(
            payload.get("minimum_duration_seconds"),
            field="minimum_duration_seconds",
        )
        if minimum_duration_seconds < 86_400:
            raise ValueError("minimum_duration_seconds must be at least 86400")
        github_hosted_runner_allowed = host.get("github_hosted_runner_allowed")
        if github_hosted_runner_allowed is not False:
            raise ValueError("GitHub-hosted runners must remain forbidden")
        if host.get("exact_host_id_required") is not True:
            raise ValueError("policy must require an exact host_id")
        thresholds = dict(_mapping(payload.get("thresholds"), field="thresholds"))
        if (
            _integer(
                thresholds.get("minimum_duration_seconds"),
                field="thresholds.minimum_duration_seconds",
            )
            != minimum_duration_seconds
        ):
            raise ValueError("policy duration thresholds disagree")
        requirements = dict(_mapping(payload.get("requirements"), field="requirements"))
        for key, expected in (
            ("execution_enabled", False),
            ("trading_credentials_present", False),
            ("performance_research_authorized", False),
            ("replay_authorized", False),
            ("model_training_authorized", False),
            ("orders_submitted", 0),
        ):
            if requirements.get(key) != expected:
                raise ValueError(f"policy requirement {key} must equal {expected!r}")
        durability = dict(_mapping(payload.get("durability"), field="durability"))
        if durability.get("immutable_storage_uri_required") is not True:
            raise ValueError("policy must require an immutable storage URI")
        if durability.get("ephemeral_ci_artifact_alone_is_sufficient") is not False:
            raise ValueError("ephemeral CI evidence must remain insufficient")
        outcomes = dict(_mapping(payload.get("outcomes"), field="outcomes"))
        expected_outcomes = {
            "accepted",
            "rejected",
            "inconclusive_insufficient_activity",
        }
        if set(outcomes) != expected_outcomes:
            raise ValueError("policy outcomes do not match the frozen outcome model")
        return cls(
            policy_id=_text(payload.get("policy_id"), field="policy_id"),
            source=_text(payload.get("source"), field="source"),
            symbols=symbols,
            minimum_duration_seconds=minimum_duration_seconds,
            required_host_class=_text(host.get("required_class"), field="host.required_class"),
            github_hosted_runner_allowed=github_hosted_runner_allowed,
            websocket_endpoint=_text(endpoints.get("websocket"), field="endpoints.websocket"),
            clock_endpoint=_text(endpoints.get("clock"), field="endpoints.clock"),
            instruments_endpoint=_text(
                endpoints.get("instruments"),
                field="endpoints.instruments",
            ),
            source_semantics=dict(
                _mapping(payload.get("source_semantics"), field="source_semantics")
            ),
            thresholds=thresholds,
            requirements=requirements,
            durability=durability,
            outcomes=outcomes,
        )


def _valid_identity(value: str, *, field: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", value):
        raise ValueError(f"{field} contains unsupported characters")
    return value


def _validated_durable_uri(value: object) -> str:
    uri = _text(value, field="request.durable_storage_uri")
    if len(uri) > 300:
        raise ValueError("request.durable_storage_uri is too long")
    parsed = urllib.parse.urlsplit(uri)
    if not parsed.scheme:
        raise ValueError("request.durable_storage_uri must be an absolute URI")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("request.durable_storage_uri must not contain credentials or query data")
    if parsed.scheme == "file":
        if not parsed.path.startswith("/"):
            raise ValueError("file durable URI must contain an absolute path")
    elif not parsed.netloc:
        raise ValueError("non-file durable URI must contain an authority")
    return uri


def validate_request(
    request: Mapping[str, object],
    *,
    policy: OkxShadowAcceptancePolicy,
) -> dict[str, object]:
    if _integer(request.get("schema_version"), field="request.schema_version") != 1:
        raise ValueError("request schema_version must be 1")
    request_id = _valid_identity(
        _text(request.get("request_id"), field="request.request_id"),
        field="request.request_id",
    )
    run_id = _valid_identity(
        _text(request.get("run_id"), field="request.run_id"),
        field="request.run_id",
    )
    host_id = _valid_identity(
        _text(request.get("host_id"), field="request.host_id"),
        field="request.host_id",
    )
    if request.get("policy_id") != policy.policy_id:
        raise ValueError("request policy_id does not match policy")
    symbols = tuple(
        _text(item, field="request.symbols[]").upper()
        for item in _sequence(request.get("symbols"), field="request.symbols")
    )
    if symbols != policy.symbols:
        raise ValueError("request symbols do not match frozen policy order")
    duration_seconds = _integer(
        request.get("duration_seconds"),
        field="request.duration_seconds",
    )
    if duration_seconds < policy.minimum_duration_seconds:
        raise ValueError("request duration is shorter than the frozen minimum")
    if request.get("host_class") != policy.required_host_class:
        raise ValueError("request host_class does not match frozen policy")
    if request.get("github_hosted_runner") is not False:
        raise ValueError("request github_hosted_runner must be false")
    for key, expected in (
        ("execution_enabled", False),
        ("performance_research_authorized", False),
        ("replay_authorized", False),
        ("model_training_authorized", False),
        ("orders_submitted", 0),
    ):
        if request.get(key) != expected:
            raise ValueError(f"request {key} must equal {expected!r}")
    return {
        "request_id": request_id,
        "run_id": run_id,
        "host_id": host_id,
        "host_class": policy.required_host_class,
        "duration_seconds": duration_seconds,
        "durable_storage_uri": _validated_durable_uri(request.get("durable_storage_uri")),
    }


def _inspect_events(
    path: Path,
    *,
    allowed_symbols: frozenset[str],
) -> tuple[int, int, dict[str, int]]:
    line_count = 0
    invalid = 0
    counts = {symbol: 0 for symbol in sorted(allowed_symbols)}
    source_event_ids: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            if not raw_line.strip():
                continue
            line_count += 1
            try:
                payload = _mapping(json.loads(raw_line), field=f"events[{line_count}]")
                event = event_from_json_dict(payload)
                symbol = event.symbol.upper()
                if event.source != SOURCE_ID:
                    raise ValueError("unexpected source")
                if symbol not in allowed_symbols:
                    raise ValueError("unexpected symbol")
                if event.notional_usd != event.quantity * event.price:
                    raise ValueError("notional does not equal quantity times price")
                if event.source_event_id in source_event_ids:
                    raise ValueError("duplicate persisted source_event_id")
                source_event_ids.add(event.source_event_id)
                counts[symbol] += 1
            except (TypeError, ValueError):
                invalid += 1
    return line_count, invalid, counts


def _write_manifest(
    path: Path,
    *,
    request: Mapping[str, object],
    collector_commit: str,
    policy: OkxShadowAcceptancePolicy,
    started_at_ms: int,
    ended_at_ms: int,
    start_clock: Mapping[str, object] | None,
    end_clock: Mapping[str, object] | None,
    status: str,
    collector_error: str | None,
    artifacts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "schema_version": 1,
        "manifest_type": "okx_liquidation_shadow_acceptance",
        "request_id": request["request_id"],
        "policy_id": policy.policy_id,
        "run_id": request["run_id"],
        "host_id": request["host_id"],
        "host_class": request["host_class"],
        "github_hosted_runner": False,
        "durable_storage_uri": request["durable_storage_uri"],
        "collector_commit": collector_commit,
        "source": policy.source,
        "symbols": list(policy.symbols),
        "duration_seconds": request["duration_seconds"],
        "endpoints": {
            "websocket": policy.websocket_endpoint,
            "clock": policy.clock_endpoint,
            "instruments": policy.instruments_endpoint,
        },
        "source_semantics": dict(policy.source_semantics),
        "started_at_ms": started_at_ms,
        "ended_at_ms": ended_at_ms,
        "status": status,
        "collector_error": collector_error,
        "clock_probes": {"start": start_clock, "end": end_clock},
        "artifacts": dict(artifacts),
        "safety": {
            "execution_enabled": False,
            "trading_credentials_present": False,
            "performance_research_authorized": False,
            "replay_authorized": False,
            "model_training_authorized": False,
            "orders_submitted": 0,
        },
    }
    manifest["manifest_sha256"] = _canonical_hash(manifest, field="manifest_sha256")
    write_json_atomic(path, manifest)
    return manifest


class _Gates:
    def __init__(self) -> None:
        self.items: list[GateResult] = []

    def add(self, name: str, passed: bool, actual: object, expected: object) -> None:
        self.items.append(GateResult(name, passed, actual, expected))

    def equal(self, name: str, actual: object, expected: object) -> None:
        self.add(name, actual == expected, actual, expected)

    def at_least(self, name: str, actual: float, expected: float) -> None:
        self.add(name, actual >= expected, actual, expected)

    def at_most(self, name: str, actual: float, expected: float) -> None:
        self.add(name, actual <= expected, actual, expected)


def _artifact_paths(
    run_root: Path,
    manifest: Mapping[str, object],
) -> tuple[Path, Path, Path]:
    artifacts = _mapping(manifest.get("artifacts"), field="manifest.artifacts")
    paths: list[Path] = []
    for key in ("events", "summary", "instruments"):
        entry = _mapping(artifacts.get(key), field=f"manifest.artifacts.{key}")
        name = _valid_file_name(
            entry.get("file_name"),
            field=f"manifest.artifacts.{key}.file_name",
        )
        paths.append(run_root / name)
    return paths[0], paths[1], paths[2]


def _outcome(
    failed_gates: Sequence[str],
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    activity_failures = tuple(
        gate
        for gate in failed_gates
        if gate in ACTIVITY_GATES or gate.startswith("minimum_events_per_observed_symbol_")
    )
    non_activity_failures = tuple(gate for gate in failed_gates if gate not in activity_failures)
    if non_activity_failures:
        outcome = "rejected"
    elif activity_failures:
        outcome = "inconclusive_insufficient_activity"
    else:
        outcome = "accepted"
    return outcome, activity_failures, non_activity_failures


def evaluate_run(
    run_root: Path,
    *,
    policy: OkxShadowAcceptancePolicy,
) -> dict[str, object]:
    manifest_path = run_root / MANIFEST_NAME
    manifest = _load_json(manifest_path, field="manifest")
    events_path, summary_path, instruments_path = _artifact_paths(run_root, manifest)
    summary = _load_json(summary_path, field="summary")
    instrument_snapshot = _load_json(instruments_path, field="instrument_snapshot")
    source = _mapping(summary.get("source"), field="summary.source")
    semantics = _mapping(source.get("semantics"), field="summary.source.semantics")
    output = _mapping(summary.get("output"), field="summary.output")
    stats = _mapping(summary.get("stats"), field="summary.stats")
    latency = _mapping(stats.get("latency"), field="summary.stats.latency")
    events_by_symbol = _mapping(
        stats.get("events_by_symbol"),
        field="summary.stats.events_by_symbol",
    )
    summary_instruments = _mapping(
        summary.get("instrument_metadata"),
        field="summary.instrument_metadata",
    )
    clocks = _mapping(manifest.get("clock_probes"), field="manifest.clock_probes")
    start_clock = _mapping(clocks.get("start"), field="manifest.clock_probes.start")
    end_clock = _mapping(clocks.get("end"), field="manifest.clock_probes.end")
    safety = _mapping(manifest.get("safety"), field="manifest.safety")
    threshold = policy.thresholds
    manifest_artifacts = _mapping(manifest.get("artifacts"), field="manifest.artifacts")

    event_lines, invalid_events, persisted_by_symbol = _inspect_events(
        events_path,
        allowed_symbols=frozenset(policy.symbols),
    )
    instrument_symbols, invalid_contracts = _instrument_contracts(instrument_snapshot)
    events_parsed = _integer(stats.get("events_parsed"), field="stats.events_parsed")
    events_written = _integer(stats.get("events_written"), field="stats.events_written")
    duplicates = _integer(stats.get("duplicates"), field="stats.duplicates")
    duplicate_ratio = duplicates / events_parsed if events_parsed else 0.0
    latency_count, latency_over_ratio = _latency_over_ratio(
        latency,
        threshold_ms=_integer(
            threshold.get("latency_threshold_ms"),
            field="thresholds.latency_threshold_ms",
        ),
    )
    summary_symbol_counts = {
        str(symbol).upper(): _integer(
            count,
            field=f"stats.events_by_symbol.{symbol}",
        )
        for symbol, count in events_by_symbol.items()
    }
    observed_symbols = tuple(
        sorted(symbol for symbol, count in persisted_by_symbol.items() if count > 0)
    )
    actual_hashes = {
        "events": sha256_file(events_path),
        "summary": sha256_file(summary_path),
        "instruments": sha256_file(instruments_path),
    }
    actual_sizes = {
        "events": events_path.stat().st_size,
        "summary": summary_path.stat().st_size,
        "instruments": instruments_path.stat().st_size,
    }
    artifact_entries = {
        key: _mapping(manifest_artifacts.get(key), field=f"manifest.artifacts.{key}")
        for key in ("events", "summary", "instruments")
    }

    gates = _Gates()
    expected_manifest_hash = _canonical_hash(manifest, field="manifest_sha256")
    collector_commit = str(manifest.get("collector_commit", ""))
    duration_request = _integer(
        manifest.get("duration_seconds"),
        field="manifest.duration_seconds",
    )
    duration_seconds = _number(stats.get("duration_ms"), field="stats.duration_ms") / 1000
    messages_received = _integer(
        stats.get("messages_received"),
        field="stats.messages_received",
    )
    control_messages = _integer(
        stats.get("control_messages"),
        field="stats.control_messages",
    )
    connections = _integer(stats.get("connections"), field="stats.connections")
    parse_failures = _integer(
        stats.get("parse_failures"),
        field="stats.parse_failures",
    )
    availability_ratio = _number(
        stats.get("availability_ratio"),
        field="stats.availability_ratio",
    )
    disconnects_per_hour = _number(
        stats.get("disconnects_per_hour"),
        field="stats.disconnects_per_hour",
    )
    output_line_count = _integer(output.get("line_count"), field="output.line_count")
    output_initial_size = _integer(
        output.get("initial_size_bytes"),
        field="output.initial_size_bytes",
    )
    output_final_size = _integer(
        output.get("final_size_bytes"),
        field="output.final_size_bytes",
    )
    manifest_started = _integer(
        manifest.get("started_at_ms"),
        field="manifest.started_at_ms",
    )
    manifest_ended = _integer(
        manifest.get("ended_at_ms"),
        field="manifest.ended_at_ms",
    )
    collection_started = _integer(
        stats.get("started_at_ms"),
        field="stats.started_at_ms",
    )
    collection_ended = _integer(
        stats.get("ended_at_ms"),
        field="stats.ended_at_ms",
    )
    start_clock_checked = _integer(
        start_clock.get("checked_at_ms"),
        field="manifest.clock_probes.start.checked_at_ms",
    )
    end_clock_checked = _integer(
        end_clock.get("checked_at_ms"),
        field="manifest.clock_probes.end.checked_at_ms",
    )
    manifest_endpoints = _mapping(manifest.get("endpoints"), field="manifest.endpoints")

    gates.equal("manifest_schema_version", manifest.get("schema_version"), 1)
    gates.equal(
        "manifest_type",
        manifest.get("manifest_type"),
        "okx_liquidation_shadow_acceptance",
    )
    gates.equal("manifest_self_hash", manifest.get("manifest_sha256"), expected_manifest_hash)
    gates.equal("collector_status", manifest.get("status"), "completed")
    gates.equal("collector_error", manifest.get("collector_error"), None)
    gates.equal("policy_id", manifest.get("policy_id"), policy.policy_id)
    gates.equal("source_id", manifest.get("source"), policy.source)
    gates.equal("symbols", tuple(manifest.get("symbols", ())), policy.symbols)
    gates.at_least(
        "duration_request",
        duration_request,
        policy.minimum_duration_seconds,
    )
    gates.equal("host_class", manifest.get("host_class"), policy.required_host_class)
    gates.equal("github_hosted_runner_disabled", manifest.get("github_hosted_runner"), False)
    gates.add(
        "host_id",
        bool(re.fullmatch(r"[A-Za-z0-9._-]{3,80}", str(manifest.get("host_id", "")))),
        manifest.get("host_id"),
        "exact non-sensitive host identity",
    )
    try:
        durable_uri = _validated_durable_uri(manifest.get("durable_storage_uri"))
        gates.add("durable_storage_uri", True, durable_uri, "absolute credential-free URI")
    except (TypeError, ValueError) as exc:
        durable_uri = str(manifest.get("durable_storage_uri", ""))
        gates.add("durable_storage_uri", False, durable_uri, str(exc))
    gates.equal(
        "websocket_endpoint",
        manifest_endpoints.get("websocket"),
        policy.websocket_endpoint,
    )
    gates.equal("clock_endpoint", manifest_endpoints.get("clock"), policy.clock_endpoint)
    gates.equal(
        "instruments_endpoint",
        manifest_endpoints.get("instruments"),
        policy.instruments_endpoint,
    )
    gates.equal(
        "source_semantics",
        manifest.get("source_semantics"),
        policy.source_semantics,
    )
    gates.add(
        "collector_commit",
        _valid_commit(collector_commit),
        collector_commit,
        "40 lowercase hexadecimal characters",
    )
    gates.equal(
        "execution_disabled",
        [safety.get("execution_enabled"), summary.get("execution_enabled")],
        [False, False],
    )
    gates.equal(
        "trading_credentials_absent",
        [
            safety.get("trading_credentials_present"),
            summary.get("trading_credentials_present"),
        ],
        [False, False],
    )
    gates.equal(
        "performance_research_disabled",
        safety.get("performance_research_authorized"),
        False,
    )
    gates.equal("replay_disabled", safety.get("replay_authorized"), False)
    gates.equal("model_training_disabled", safety.get("model_training_authorized"), False)
    gates.equal("orders_zero", safety.get("orders_submitted"), 0)
    gates.equal("summary_schema_version", summary.get("schema_version"), 1)
    gates.equal(
        "summary_type",
        summary.get("summary_type"),
        "liquidation_data_only_staging",
    )
    gates.equal("summary_source", source.get("id"), policy.source)
    gates.equal("summary_endpoint", source.get("endpoint"), policy.websocket_endpoint)
    gates.equal(
        "summary_symbols",
        tuple(source.get("symbols", ())),
        tuple(sorted(policy.symbols)),
    )
    gates.equal("summary_commit", summary.get("collector_commit"), collector_commit)
    gates.equal(
        "shadow_status",
        semantics.get("status"),
        "shadow_only_not_in_liquid20_v1",
    )
    gates.equal("run_status", stats.get("run_status"), "completed_duration")
    gates.add(
        "manifest_time_order",
        manifest_started <= manifest_ended,
        [manifest_started, manifest_ended],
        "started_at_ms <= ended_at_ms",
    )
    gates.add(
        "collection_within_manifest",
        manifest_started <= collection_started <= collection_ended <= manifest_ended,
        [manifest_started, collection_started, collection_ended, manifest_ended],
        "manifest start <= collection start <= collection end <= manifest end",
    )
    gates.add(
        "start_clock_brackets_collection",
        manifest_started <= start_clock_checked <= collection_started,
        [manifest_started, start_clock_checked, collection_started],
        "manifest start <= start clock <= collection start",
    )
    gates.add(
        "end_clock_brackets_collection",
        collection_ended <= end_clock_checked <= manifest_ended,
        [collection_ended, end_clock_checked, manifest_ended],
        "collection end <= end clock <= manifest end",
    )

    gates.at_least(
        "minimum_duration_seconds",
        duration_seconds,
        _number(
            threshold.get("minimum_duration_seconds"),
            field="thresholds.minimum_duration_seconds",
        ),
    )
    gates.at_least(
        "minimum_messages_received",
        messages_received,
        _integer(
            threshold.get("minimum_messages_received"),
            field="thresholds.minimum_messages_received",
        ),
    )
    gates.at_least(
        "minimum_control_messages",
        control_messages,
        _integer(
            threshold.get("minimum_control_messages"),
            field="thresholds.minimum_control_messages",
        ),
    )
    gates.at_least(
        "minimum_connections",
        connections,
        _integer(
            threshold.get("minimum_connections"),
            field="thresholds.minimum_connections",
        ),
    )
    gates.at_most(
        "maximum_parse_failures",
        parse_failures,
        _integer(
            threshold.get("maximum_parse_failures"),
            field="thresholds.maximum_parse_failures",
        ),
    )
    gates.at_most(
        "maximum_invalid_normalized_events",
        invalid_events,
        _integer(
            threshold.get("maximum_invalid_normalized_events"),
            field="thresholds.maximum_invalid_normalized_events",
        ),
    )
    gates.at_least(
        "minimum_availability_ratio",
        availability_ratio,
        _number(
            threshold.get("minimum_availability_ratio"),
            field="thresholds.minimum_availability_ratio",
        ),
    )
    gates.at_most(
        "maximum_disconnects_per_hour",
        disconnects_per_hour,
        _number(
            threshold.get("maximum_disconnects_per_hour"),
            field="thresholds.maximum_disconnects_per_hour",
        ),
    )
    gates.at_most(
        "maximum_duplicate_ratio",
        duplicate_ratio,
        _number(
            threshold.get("maximum_duplicate_ratio"),
            field="thresholds.maximum_duplicate_ratio",
        ),
    )
    gates.at_most(
        "maximum_latency_over_threshold_ratio",
        latency_over_ratio,
        _number(
            threshold.get("maximum_latency_over_threshold_ratio"),
            field="thresholds.maximum_latency_over_threshold_ratio",
        ),
    )
    gates.at_least(
        "minimum_latency_samples",
        latency_count,
        _integer(
            threshold.get("minimum_latency_samples"),
            field="thresholds.minimum_latency_samples",
        ),
    )
    gates.equal("events_parsed_accounting", events_written + duplicates, events_parsed)
    gates.equal(
        "event_line_count",
        [event_lines, events_written, output_line_count],
        [events_written, events_written, events_written],
    )
    gates.equal("new_output", output_initial_size, 0)
    gates.equal(
        "summary_event_symbol_accounting",
        sum(summary_symbol_counts.values()),
        events_parsed,
    )
    gates.add(
        "summary_symbols_bounded",
        set(summary_symbol_counts).issubset(policy.symbols),
        tuple(sorted(summary_symbol_counts)),
        f"subset of {policy.symbols}",
    )
    gates.add(
        "persisted_symbol_accounting",
        all(
            persisted_by_symbol[symbol] <= summary_symbol_counts.get(symbol, 0)
            for symbol in policy.symbols
        ),
        persisted_by_symbol,
        "persisted counts do not exceed parsed counts",
    )
    gates.equal(
        "events_sha256",
        [
            actual_hashes["events"],
            output.get("sha256"),
            artifact_entries["events"].get("sha256"),
        ],
        [actual_hashes["events"]] * 3,
    )
    gates.equal(
        "events_size",
        [
            actual_sizes["events"],
            artifact_entries["events"].get("size_bytes"),
            output_final_size,
        ],
        [actual_sizes["events"]] * 3,
    )
    gates.equal(
        "summary_sha256",
        [actual_hashes["summary"], artifact_entries["summary"].get("sha256")],
        [actual_hashes["summary"]] * 2,
    )
    gates.equal(
        "summary_size",
        [actual_sizes["summary"], artifact_entries["summary"].get("size_bytes")],
        [actual_sizes["summary"]] * 2,
    )
    gates.equal(
        "instrument_sha256",
        [
            actual_hashes["instruments"],
            artifact_entries["instruments"].get("sha256"),
            summary_instruments.get("sha256"),
        ],
        [actual_hashes["instruments"]] * 3,
    )
    gates.equal(
        "instrument_size",
        [
            actual_sizes["instruments"],
            artifact_entries["instruments"].get("size_bytes"),
        ],
        [actual_sizes["instruments"]] * 2,
    )
    gates.equal(
        "instrument_endpoint",
        [
            instrument_snapshot.get("endpoint"),
            summary_instruments.get("endpoint"),
        ],
        [policy.instruments_endpoint] * 2,
    )
    gates.equal("instrument_source", instrument_snapshot.get("source"), policy.source)
    gates.equal("instrument_symbols", instrument_symbols, tuple(sorted(policy.symbols)))
    gates.equal("instrument_contracts_valid", invalid_contracts, 0)
    gates.equal(
        "instrument_count",
        summary_instruments.get("contract_count"),
        len(policy.symbols),
    )
    gates.equal(
        "start_clock_endpoint",
        start_clock.get("server_time_url"),
        policy.clock_endpoint,
    )
    gates.equal(
        "end_clock_endpoint",
        end_clock.get("server_time_url"),
        policy.clock_endpoint,
    )
    gates.equal("start_clock_synchronized", start_clock.get("synchronized"), True)
    gates.equal("end_clock_synchronized", end_clock.get("synchronized"), True)
    gates.equal("summary_start_clock", summary.get("clock_probe"), start_clock)
    gates.equal("latency_samples_match_parsed", latency_count, events_parsed)
    gates.at_least(
        "minimum_events_total",
        events_written,
        _integer(
            threshold.get("minimum_events_total"),
            field="thresholds.minimum_events_total",
        ),
    )
    gates.at_least(
        "minimum_observed_symbols",
        len(observed_symbols),
        _integer(
            threshold.get("minimum_observed_symbols"),
            field="thresholds.minimum_observed_symbols",
        ),
    )
    minimum_per_observed = _integer(
        threshold.get("minimum_events_per_observed_symbol"),
        field="thresholds.minimum_events_per_observed_symbol",
    )
    for symbol in observed_symbols:
        gates.at_least(
            f"minimum_events_per_observed_symbol_{symbol}",
            persisted_by_symbol[symbol],
            minimum_per_observed,
        )

    failed_gates = tuple(item.gate for item in gates.items if not item.passed)
    outcome, activity_failures, non_activity_failures = _outcome(failed_gates)
    report: dict[str, object] = {
        "schema_version": 1,
        "report_type": "okx_liquidation_shadow_acceptance",
        "policy_id": policy.policy_id,
        "request_id": manifest.get("request_id"),
        "run_id": manifest.get("run_id"),
        "host_id": manifest.get("host_id"),
        "durable_storage_uri": durable_uri,
        "collector_commit": collector_commit,
        "outcome": outcome,
        "accepted": outcome == "accepted",
        "failed_gates": list(failed_gates),
        "activity_failed_gates": list(activity_failures),
        "non_activity_failed_gates": list(non_activity_failures),
        "gates": [item.as_json_dict() for item in gates.items],
        "metrics": {
            "duration_seconds": duration_seconds,
            "messages_received": messages_received,
            "control_messages": control_messages,
            "events_parsed": events_parsed,
            "events_written": events_written,
            "events_by_symbol": persisted_by_symbol,
            "observed_symbols": list(observed_symbols),
            "availability_ratio": availability_ratio,
            "disconnects_per_hour": disconnects_per_hour,
            "duplicate_ratio": duplicate_ratio,
            "invalid_normalized_events": invalid_events,
            "latency_samples": latency_count,
            "latency_over_threshold_ratio": latency_over_ratio,
        },
        "artifacts": {
            "events_sha256": actual_hashes["events"],
            "summary_sha256": actual_hashes["summary"],
            "instrument_snapshot_sha256": actual_hashes["instruments"],
            "manifest_sha256": manifest.get("manifest_sha256"),
        },
        "performance_research_authorized": False,
        "replay_authorized": False,
        "model_training_authorized": False,
        "liquid20_membership_authorized": False,
        "orders_submitted": 0,
        "boundary": (
            "Operational source acceptance only. An accepted outcome permits only a later "
            "source-integration research proposal; it does not authorize replay, models, "
            "Liquid20 membership or trading."
        ),
    }
    report["report_sha256"] = _canonical_hash(report, field="report_sha256")
    return report


def _write_checksum_index(run_root: Path) -> None:
    lines = [f"{sha256_file(run_root / name)}  {name}" for name in PACKAGE_FILES]
    (run_root / SHA256_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def materialize_evidence_package(
    run_root: Path,
    *,
    policy: OkxShadowAcceptancePolicy,
) -> dict[str, object]:
    report = evaluate_run(run_root, policy=policy)
    write_json_atomic(run_root / REPORT_NAME, report)
    _write_checksum_index(run_root)
    verify_evidence_package(run_root, policy=policy)
    return report


def _read_checksum_index(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/]+)", raw_line)
        if not match:
            raise ValueError(f"invalid checksum index line {line_number}")
        digest, name = match.groups()
        if name in entries:
            raise ValueError(f"duplicate checksum entry: {name}")
        entries[name] = digest
    return entries


def verify_evidence_package(
    run_root: Path,
    *,
    policy: OkxShadowAcceptancePolicy,
) -> dict[str, object]:
    stored_report = _load_json(run_root / REPORT_NAME, field="report")
    if stored_report.get("report_sha256") != _canonical_hash(
        stored_report,
        field="report_sha256",
    ):
        raise ValueError("report self-hash mismatch")
    recomputed_report = evaluate_run(run_root, policy=policy)
    if stored_report != recomputed_report:
        raise ValueError("stored report does not match independent evaluation")
    entries = _read_checksum_index(run_root / SHA256_NAME)
    if tuple(entries) != PACKAGE_FILES:
        raise ValueError("checksum index does not contain the exact package files")
    for name in PACKAGE_FILES:
        actual = sha256_file(run_root / name)
        if entries[name] != actual:
            raise ValueError(f"checksum mismatch for {name}")
    return {
        "package_valid": True,
        "outcome": stored_report.get("outcome"),
        "report_sha256": stored_report.get("report_sha256"),
        "checksum_entries": len(entries),
    }


async def execute_request(
    request_path: Path,
    *,
    policy_path: Path,
    collector_commit: str,
    output_root: Path,
) -> dict[str, object]:
    if not _valid_commit(collector_commit):
        raise ValueError("collector_commit must be 40 lowercase hexadecimal characters")
    if await asyncio.to_thread(output_root.exists):
        raise FileExistsError(f"output root already exists: {output_root}")
    policy = OkxShadowAcceptancePolicy.load(policy_path)
    if policy.source != SOURCE_ID:
        raise ValueError(f"unsupported policy source: {policy.source}")
    request_payload = _load_json(request_path, field="request")
    request = validate_request(request_payload, policy=policy)
    await asyncio.to_thread(output_root.mkdir, parents=True)
    events_path = output_root / EVENTS_NAME
    summary_path = output_root / SUMMARY_NAME
    instruments_path = output_root / INSTRUMENTS_NAME
    manifest_path = output_root / MANIFEST_NAME
    started_at_ms = time.time_ns() // 1_000_000
    start_clock: Mapping[str, object] | None = None
    end_clock: Mapping[str, object] | None = None
    artifacts: dict[str, Mapping[str, object]] = {}
    try:
        if trading_credentials_present():
            raise RuntimeError("recognized trading credential environment is present")
        instruments = fetch_okx_instruments(
            symbols=policy.symbols,
            instruments_url=policy.instruments_endpoint,
        )
        start_probe = probe_okx_clock(
            server_time_url=policy.clock_endpoint,
            tolerance_ms=_integer(
                policy.thresholds.get("clock_tolerance_ms"),
                field="thresholds.clock_tolerance_ms",
            ),
        )
        start_clock = start_probe.as_json_dict()
        await collect_okx_liquidations(
            endpoint=policy.websocket_endpoint,
            symbols=policy.symbols,
            instruments=instruments,
            instruments_url=policy.instruments_endpoint,
            instrument_metadata_path=instruments_path,
            output_path=events_path,
            duration_seconds=_integer(
                request["duration_seconds"],
                field="request.duration_seconds",
            ),
            summary_path=summary_path,
            collector_commit=collector_commit,
            require_new_output=True,
            clock_probe=start_probe,
            credentials_present=False,
        )
        end_probe = probe_okx_clock(
            server_time_url=policy.clock_endpoint,
            tolerance_ms=_integer(
                policy.thresholds.get("clock_tolerance_ms"),
                field="thresholds.clock_tolerance_ms",
            ),
        )
        end_clock = end_probe.as_json_dict()
        artifacts = {
            "events": _artifact_entry(events_path),
            "summary": _artifact_entry(summary_path),
            "instruments": _artifact_entry(instruments_path),
        }
        _write_manifest(
            manifest_path,
            request=request,
            collector_commit=collector_commit,
            policy=policy,
            started_at_ms=started_at_ms,
            ended_at_ms=time.time_ns() // 1_000_000,
            start_clock=start_clock,
            end_clock=end_clock,
            status="completed",
            collector_error=None,
            artifacts=artifacts,
        )
        return materialize_evidence_package(output_root, policy=policy)
    except Exception as exc:
        for key, candidate in (
            ("events", events_path),
            ("summary", summary_path),
            ("instruments", instruments_path),
        ):
            if await asyncio.to_thread(candidate.exists):
                artifacts[key] = await asyncio.to_thread(_artifact_entry, candidate)
        _write_manifest(
            manifest_path,
            request=request,
            collector_commit=collector_commit,
            policy=policy,
            started_at_ms=started_at_ms,
            ended_at_ms=time.time_ns() // 1_000_000,
            start_clock=start_clock,
            end_clock=end_clock,
            status="failed",
            collector_error=_bounded_error(exc),
            artifacts=artifacts,
        )
        raise


def exit_code_for_outcome(outcome: object) -> int:
    if outcome == "accepted":
        return 0
    if outcome == "inconclusive_insufficient_activity":
        return 2
    return 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run and evaluate frozen 24-hour OKX shadow source acceptance.",
    )
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--collector-commit", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    report = asyncio.run(
        execute_request(
            args.request,
            policy_path=args.policy,
            collector_commit=args.collector_commit,
            output_root=args.output_root,
        )
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(exit_code_for_outcome(report.get("outcome")))


if __name__ == "__main__":
    main()
