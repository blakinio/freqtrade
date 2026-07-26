from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.staging import GateResult, sha256_file, write_json_atomic
from ai_platform.scripts.liquidation_okx_collector import (
    collect_okx_liquidations,
    fetch_okx_instruments,
    probe_okx_clock,
    trading_credentials_present,
)


POLICY_PATH = Path("ai_platform/research/liquidations/okx-liquidation-shadow-smoke-policy-v1.json")
SOURCE_ID = "okx-usdt-swap"
MANIFEST_NAME = "okx-shadow-smoke-manifest.json"
REPORT_NAME = "okx-shadow-smoke-report.json"
EVENTS_NAME = "okx-usdt-swap.ndjson"
SUMMARY_NAME = "okx-usdt-swap-summary.json"
INSTRUMENTS_NAME = "okx-usdt-swap-instruments.json"
SHA256_NAME = "artifact-sha256.txt"


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


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field} must be an integer") from exc
    if str(parsed) != str(value).strip() and not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    return parsed


def _number(value: object, *, field: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{field} must be numeric")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field} must be numeric") from exc
    if not parsed == parsed or parsed in (float("inf"), float("-inf")):
        raise ValueError(f"{field} must be finite")
    return parsed


def _load_json(path: Path, *, field: str) -> Mapping[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return _mapping(json.load(handle), field=field)


def _valid_commit(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{40}", value))


def _valid_file_name(value: object, *, field: str) -> str:
    name = _text(value, field=field)
    if Path(name).name != name:
        raise ValueError(f"{field} must be a file name")
    return name


def _canonical_hash(payload: Mapping[str, object], *, field: str) -> str:
    material = dict(payload)
    material.pop(field, None)
    encoded = json.dumps(material, separators=(",", ":"), sort_keys=True).encode()
    return sha256(encoded).hexdigest()


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def _bounded_error(exc: BaseException) -> str:
    message = " ".join(str(exc).split())
    return f"{type(exc).__name__}: {message}"[:400]


@dataclass(frozen=True, slots=True)
class OkxShadowSmokePolicy:
    policy_id: str
    source: str
    symbols: tuple[str, ...]
    duration_seconds: int
    websocket_endpoint: str
    clock_endpoint: str
    instruments_endpoint: str
    thresholds: Mapping[str, object]
    requirements: Mapping[str, object]

    @classmethod
    def load(cls, path: Path = POLICY_PATH) -> OkxShadowSmokePolicy:
        payload = _load_json(path, field="policy")
        if _integer(payload.get("schema_version"), field="schema_version") != 1:
            raise ValueError("policy schema_version must be 1")
        endpoints = _mapping(payload.get("endpoints"), field="endpoints")
        symbols = tuple(
            _text(item, field="symbols[]").upper()
            for item in _sequence(payload.get("symbols"), field="symbols")
        )
        if not symbols or len(symbols) != len(set(symbols)):
            raise ValueError("policy symbols must be non-empty and unique")
        duration_seconds = _integer(payload.get("duration_seconds"), field="duration_seconds")
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be > 0")
        return cls(
            policy_id=_text(payload.get("policy_id"), field="policy_id"),
            source=_text(payload.get("source"), field="source"),
            symbols=symbols,
            duration_seconds=duration_seconds,
            websocket_endpoint=_text(endpoints.get("websocket"), field="endpoints.websocket"),
            clock_endpoint=_text(endpoints.get("clock"), field="endpoints.clock"),
            instruments_endpoint=_text(
                endpoints.get("instruments"),
                field="endpoints.instruments",
            ),
            thresholds=dict(_mapping(payload.get("thresholds"), field="thresholds")),
            requirements=dict(_mapping(payload.get("requirements"), field="requirements")),
        )


def _validate_request(
    request: Mapping[str, object],
    *,
    policy: OkxShadowSmokePolicy,
) -> tuple[str, str]:
    if _integer(request.get("schema_version"), field="request.schema_version") != 1:
        raise ValueError("request schema_version must be 1")
    request_id = _text(request.get("request_id"), field="request.request_id")
    run_id = _text(request.get("run_id"), field="request.run_id")
    host_id = _text(request.get("host_id"), field="request.host_id")
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", run_id):
        raise ValueError("request.run_id contains unsupported characters")
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", host_id):
        raise ValueError("request.host_id contains unsupported characters")
    if request.get("policy_id") != policy.policy_id:
        raise ValueError("request policy_id does not match policy")
    symbols = tuple(
        _text(item, field="request.symbols[]").upper()
        for item in _sequence(request.get("symbols"), field="request.symbols")
    )
    if symbols != policy.symbols:
        raise ValueError("request symbols do not match frozen policy")
    if _integer(request.get("duration_seconds"), field="request.duration_seconds") != (
        policy.duration_seconds
    ):
        raise ValueError("request duration does not match frozen policy")
    for key, expected in (
        ("execution_enabled", False),
        ("performance_research_authorized", False),
        ("orders_submitted", 0),
    ):
        if request.get(key) != expected:
            raise ValueError(f"request {key} must equal {expected!r}")
    return request_id, run_id


def _artifact_entry(path: Path) -> dict[str, object]:
    return {
        "file_name": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _write_manifest(
    path: Path,
    *,
    request_id: str,
    run_id: str,
    host_id: str,
    collector_commit: str,
    policy: OkxShadowSmokePolicy,
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
        "manifest_type": "okx_liquidation_shadow_smoke",
        "request_id": request_id,
        "policy_id": policy.policy_id,
        "run_id": run_id,
        "host_id": host_id,
        "collector_commit": collector_commit,
        "source": policy.source,
        "symbols": list(policy.symbols),
        "duration_seconds": policy.duration_seconds,
        "endpoints": {
            "websocket": policy.websocket_endpoint,
            "clock": policy.clock_endpoint,
            "instruments": policy.instruments_endpoint,
        },
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
            "orders_submitted": 0,
        },
    }
    manifest["manifest_sha256"] = _canonical_hash(manifest, field="manifest_sha256")
    write_json_atomic(path, manifest)
    return manifest


def _latency_over_ratio(
    latency: Mapping[str, object],
    *,
    threshold_ms: int,
) -> tuple[int, float]:
    count = _integer(latency.get("count"), field="stats.latency.count")
    buckets = _mapping(latency.get("buckets"), field="stats.latency.buckets")
    over = 0
    for label, raw_count in buckets.items():
        value = _integer(raw_count, field=f"stats.latency.buckets.{label}")
        if label.startswith("gt_"):
            bound = int(label.removeprefix("gt_").removesuffix("_ms"))
            if bound >= threshold_ms:
                over += value
        elif label.startswith("le_"):
            bound = int(label.removeprefix("le_").removesuffix("_ms"))
            if bound > threshold_ms:
                over += value
    return count, over / count if count else 0.0


def _inspect_events(
    path: Path,
    *,
    allowed_symbols: frozenset[str],
) -> tuple[int, int]:
    line_count = 0
    invalid = 0
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            if not raw_line.strip():
                continue
            line_count += 1
            try:
                event = _mapping(json.loads(raw_line), field=f"events[{line_count}]")
                occurred = _integer(
                    event.get("occurred_at_ms"),
                    field=f"events[{line_count}].occurred_at_ms",
                )
                received = _integer(
                    event.get("received_at_ms"),
                    field=f"events[{line_count}].received_at_ms",
                )
                if event.get("schema_version") != 1:
                    raise ValueError("wrong schema_version")
                if event.get("source") != SOURCE_ID:
                    raise ValueError("wrong source")
                if str(event.get("symbol", "")).upper() not in allowed_symbols:
                    raise ValueError("unexpected symbol")
                if received < occurred:
                    raise ValueError("negative ingest latency")
                for key in ("price", "quantity", "notional_usd"):
                    try:
                        number = Decimal(str(event.get(key)))
                    except (InvalidOperation, ValueError) as exc:
                        raise ValueError(f"invalid {key}") from exc
                    if number <= 0:
                        raise ValueError(f"{key} must be > 0")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                invalid += 1
    return line_count, invalid


def _instrument_contracts(
    snapshot: Mapping[str, object],
) -> tuple[tuple[str, ...], int]:
    rows = _sequence(snapshot.get("contracts"), field="instrument_snapshot.contracts")
    symbols: list[str] = []
    invalid = 0
    for index, raw in enumerate(rows):
        try:
            row = _mapping(raw, field=f"instrument_snapshot.contracts[{index}]")
            symbol = _text(
                row.get("canonical_symbol"),
                field=f"instrument_snapshot.contracts[{index}].canonical_symbol",
            ).upper()
            base = symbol.removesuffix("USDT")
            if not base or row.get("contract_type") != "linear":
                raise ValueError("invalid contract type")
            if row.get("settle_currency") != "USDT":
                raise ValueError("invalid settlement")
            if row.get("contract_value_currency") != base:
                raise ValueError("invalid contract value currency")
            if Decimal(str(row.get("contract_multiplier"))) != Decimal("1"):
                raise ValueError("invalid contract multiplier")
            if Decimal(str(row.get("contract_value"))) <= 0:
                raise ValueError("invalid contract value")
            if row.get("state") != "live":
                raise ValueError("instrument is not live")
            symbols.append(symbol)
        except (InvalidOperation, TypeError, ValueError):
            invalid += 1
    return tuple(sorted(symbols)), invalid


class _Gates:
    def __init__(self) -> None:
        self.items: list[GateResult] = []

    def add(self, name: str, passed: bool, actual: object, expected: object) -> None:
        self.items.append(GateResult(name, passed, actual, expected))


def evaluate_run(
    run_root: Path,
    *,
    policy: OkxShadowSmokePolicy,
) -> dict[str, object]:
    manifest_path = run_root / MANIFEST_NAME
    manifest = _load_json(manifest_path, field="manifest")
    artifacts = _mapping(manifest.get("artifacts"), field="manifest.artifacts")
    events_entry = _mapping(artifacts.get("events"), field="manifest.artifacts.events")
    summary_entry = _mapping(artifacts.get("summary"), field="manifest.artifacts.summary")
    instruments_entry = _mapping(
        artifacts.get("instruments"),
        field="manifest.artifacts.instruments",
    )
    events_path = run_root / _valid_file_name(
        events_entry.get("file_name"),
        field="manifest.artifacts.events.file_name",
    )
    summary_path = run_root / _valid_file_name(
        summary_entry.get("file_name"),
        field="manifest.artifacts.summary.file_name",
    )
    instruments_path = run_root / _valid_file_name(
        instruments_entry.get("file_name"),
        field="manifest.artifacts.instruments.file_name",
    )
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
    event_lines, invalid_events = _inspect_events(
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
    observed_symbols = tuple(
        sorted(
            str(symbol).upper()
            for symbol, count in events_by_symbol.items()
            if _integer(count, field=f"stats.events_by_symbol.{symbol}") > 0
        )
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

    gates = _Gates()

    def equal(name: str, actual: object, expected: object) -> None:
        gates.add(name, actual == expected, actual, expected)

    def at_least(name: str, actual: float, expected: float) -> None:
        gates.add(name, actual >= expected, actual, expected)

    def at_most(name: str, actual: float, expected: float) -> None:
        gates.add(name, actual <= expected, actual, expected)

    manifest_endpoints = _mapping(manifest.get("endpoints"), field="manifest.endpoints")
    expected_manifest_hash = _canonical_hash(manifest, field="manifest_sha256")
    collector_commit = str(manifest.get("collector_commit", ""))
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
    disconnects = _integer(stats.get("disconnects"), field="stats.disconnects")
    output_line_count = _integer(output.get("line_count"), field="output.line_count")
    output_initial_size = _integer(
        output.get("initial_size_bytes"),
        field="output.initial_size_bytes",
    )
    output_final_size = _integer(
        output.get("final_size_bytes"),
        field="output.final_size_bytes",
    )

    equal("manifest_schema_version", manifest.get("schema_version"), 1)
    equal(
        "manifest_type",
        manifest.get("manifest_type"),
        "okx_liquidation_shadow_smoke",
    )
    equal("manifest_self_hash", manifest.get("manifest_sha256"), expected_manifest_hash)
    equal("collector_status", manifest.get("status"), "completed")
    equal("collector_error", manifest.get("collector_error"), None)
    equal("policy_id", manifest.get("policy_id"), policy.policy_id)
    equal("source_id", manifest.get("source"), policy.source)
    equal("symbols", tuple(manifest.get("symbols", ())), policy.symbols)
    equal("duration_request", manifest.get("duration_seconds"), policy.duration_seconds)
    equal(
        "websocket_endpoint",
        manifest_endpoints.get("websocket"),
        policy.websocket_endpoint,
    )
    equal("clock_endpoint", manifest_endpoints.get("clock"), policy.clock_endpoint)
    equal(
        "instruments_endpoint",
        manifest_endpoints.get("instruments"),
        policy.instruments_endpoint,
    )
    gates.add(
        "collector_commit",
        _valid_commit(collector_commit),
        collector_commit,
        "40 lowercase hexadecimal characters",
    )
    equal(
        "execution_disabled",
        [
            safety.get("execution_enabled"),
            summary.get("execution_enabled"),
        ],
        [False, False],
    )
    equal(
        "trading_credentials_absent",
        [
            safety.get("trading_credentials_present"),
            summary.get("trading_credentials_present"),
        ],
        [False, False],
    )
    equal(
        "performance_research_disabled",
        safety.get("performance_research_authorized"),
        False,
    )
    equal("orders_zero", safety.get("orders_submitted"), 0)
    equal("summary_schema_version", summary.get("schema_version"), 1)
    equal(
        "summary_type",
        summary.get("summary_type"),
        "liquidation_data_only_staging",
    )
    equal("summary_source", source.get("id"), policy.source)
    equal("summary_endpoint", source.get("endpoint"), policy.websocket_endpoint)
    equal(
        "summary_symbols",
        tuple(source.get("symbols", ())),
        tuple(sorted(policy.symbols)),
    )
    equal("summary_commit", summary.get("collector_commit"), collector_commit)
    equal(
        "shadow_status",
        semantics.get("status"),
        "shadow_only_not_in_liquid20_v1",
    )
    equal("run_status", stats.get("run_status"), "completed_duration")

    at_least(
        "minimum_duration_seconds",
        duration_seconds,
        _number(
            threshold.get("minimum_duration_seconds"),
            field="thresholds.minimum_duration_seconds",
        ),
    )
    at_least(
        "minimum_messages_received",
        messages_received,
        _integer(
            threshold.get("minimum_messages_received"),
            field="thresholds.minimum_messages_received",
        ),
    )
    at_least(
        "minimum_control_messages",
        control_messages,
        _integer(
            threshold.get("minimum_control_messages"),
            field="thresholds.minimum_control_messages",
        ),
    )
    at_least(
        "minimum_connections",
        connections,
        _integer(
            threshold.get("minimum_connections"),
            field="thresholds.minimum_connections",
        ),
    )
    at_most(
        "maximum_parse_failures",
        parse_failures,
        _integer(
            threshold.get("maximum_parse_failures"),
            field="thresholds.maximum_parse_failures",
        ),
    )
    at_least(
        "minimum_availability_ratio",
        availability_ratio,
        _number(
            threshold.get("minimum_availability_ratio"),
            field="thresholds.minimum_availability_ratio",
        ),
    )
    at_most(
        "maximum_disconnects",
        disconnects,
        _integer(
            threshold.get("maximum_disconnects"),
            field="thresholds.maximum_disconnects",
        ),
    )
    at_most(
        "maximum_duplicate_ratio",
        duplicate_ratio,
        _number(
            threshold.get("maximum_duplicate_ratio"),
            field="thresholds.maximum_duplicate_ratio",
        ),
    )
    at_most(
        "maximum_latency_over_threshold_ratio",
        latency_over_ratio,
        _number(
            threshold.get("maximum_latency_over_threshold_ratio"),
            field="thresholds.maximum_latency_over_threshold_ratio",
        ),
    )
    gates.add(
        "events_written_not_greater_than_parsed",
        events_written <= events_parsed,
        events_written,
        f"<= {events_parsed}",
    )
    equal(
        "event_line_count",
        [event_lines, events_written, output_line_count],
        [events_written, events_written, events_written],
    )
    equal("event_records_valid", invalid_events, 0)
    equal("new_output", output_initial_size, 0)
    equal(
        "events_sha256",
        [actual_hashes["events"], output.get("sha256"), events_entry.get("sha256")],
        [actual_hashes["events"]] * 3,
    )
    equal(
        "events_size",
        [actual_sizes["events"], events_entry.get("size_bytes"), output_final_size],
        [actual_sizes["events"]] * 3,
    )
    equal(
        "summary_sha256",
        [actual_hashes["summary"], summary_entry.get("sha256")],
        [actual_hashes["summary"]] * 2,
    )
    equal(
        "summary_size",
        [actual_sizes["summary"], summary_entry.get("size_bytes")],
        [actual_sizes["summary"]] * 2,
    )
    equal(
        "instrument_sha256",
        [
            actual_hashes["instruments"],
            instruments_entry.get("sha256"),
            summary_instruments.get("sha256"),
        ],
        [actual_hashes["instruments"]] * 3,
    )
    equal(
        "instrument_size",
        [actual_sizes["instruments"], instruments_entry.get("size_bytes")],
        [actual_sizes["instruments"]] * 2,
    )
    equal(
        "instrument_endpoint",
        [
            instrument_snapshot.get("endpoint"),
            summary_instruments.get("endpoint"),
        ],
        [policy.instruments_endpoint] * 2,
    )
    equal("instrument_source", instrument_snapshot.get("source"), policy.source)
    equal("instrument_symbols", instrument_symbols, tuple(sorted(policy.symbols)))
    equal("instrument_contracts_valid", invalid_contracts, 0)
    equal(
        "instrument_count",
        summary_instruments.get("contract_count"),
        len(policy.symbols),
    )
    equal(
        "start_clock_endpoint",
        start_clock.get("server_time_url"),
        policy.clock_endpoint,
    )
    equal(
        "end_clock_endpoint",
        end_clock.get("server_time_url"),
        policy.clock_endpoint,
    )
    equal("start_clock_synchronized", start_clock.get("synchronized"), True)
    equal("end_clock_synchronized", end_clock.get("synchronized"), True)
    equal("summary_start_clock", summary.get("clock_probe"), start_clock)
    equal("latency_samples_match_parsed", latency_count, events_parsed)
    at_least(
        "minimum_events_total",
        events_written,
        _integer(
            threshold.get("minimum_events_total"),
            field="thresholds.minimum_events_total",
        ),
    )
    at_least(
        "minimum_observed_symbols",
        len(observed_symbols),
        _integer(
            threshold.get("minimum_observed_symbols"),
            field="thresholds.minimum_observed_symbols",
        ),
    )

    failed = [item.gate for item in gates.items if not item.passed]
    report: dict[str, object] = {
        "schema_version": 1,
        "report_type": "okx_liquidation_shadow_smoke",
        "policy_id": policy.policy_id,
        "request_id": manifest.get("request_id"),
        "run_id": manifest.get("run_id"),
        "collector_commit": collector_commit,
        "passed": not failed,
        "failed_gates": failed,
        "gates": [item.as_json_dict() for item in gates.items],
        "metrics": {
            "duration_seconds": duration_seconds,
            "messages_received": stats.get("messages_received"),
            "control_messages": stats.get("control_messages"),
            "events_parsed": events_parsed,
            "events_written": events_written,
            "observed_symbols": list(observed_symbols),
            "availability_ratio": stats.get("availability_ratio"),
            "disconnects": stats.get("disconnects"),
            "duplicate_ratio": duplicate_ratio,
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
        "orders_submitted": 0,
        "boundary": (
            "Transport smoke only; no Liquid20 membership, replay, model, order or "
            "performance authorization."
        ),
    }
    report["report_sha256"] = _canonical_hash(report, field="report_sha256")
    return report


def _write_sha256_index(run_root: Path, names: Sequence[str]) -> None:
    lines = [f"{sha256_file(run_root / name)}  {name}" for name in names]
    (run_root / SHA256_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    policy = OkxShadowSmokePolicy.load(policy_path)
    if policy.source != SOURCE_ID:
        raise ValueError(f"unsupported policy source: {policy.source}")
    request = _load_json(request_path, field="request")
    request_id, run_id = _validate_request(request, policy=policy)
    host_id = _text(request.get("host_id"), field="request.host_id")
    await asyncio.to_thread(output_root.mkdir, parents=True)
    events_path = output_root / EVENTS_NAME
    summary_path = output_root / SUMMARY_NAME
    instruments_path = output_root / INSTRUMENTS_NAME
    manifest_path = output_root / MANIFEST_NAME
    report_path = output_root / REPORT_NAME
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
            duration_seconds=policy.duration_seconds,
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
            request_id=request_id,
            run_id=run_id,
            host_id=host_id,
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
        report = evaluate_run(output_root, policy=policy)
        write_json_atomic(report_path, report)
        _write_sha256_index(
            output_root,
            (EVENTS_NAME, SUMMARY_NAME, INSTRUMENTS_NAME, MANIFEST_NAME, REPORT_NAME),
        )
        return report
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
            request_id=request_id,
            run_id=run_id,
            host_id=host_id,
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run and evaluate the frozen public OKX liquidation shadow smoke.",
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
    if not report.get("passed"):
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(1)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
