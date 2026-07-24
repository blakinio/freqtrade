from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.contracts import LiquidationEvent, integer_value


DEFAULT_BYBIT_TIME_URL = "https://api.bybit.com/v5/market/time"
LATENCY_BUCKET_UPPER_BOUNDS_MS = (100, 250, 500, 1_000, 2_000, 5_000, 10_000)
TRADING_CREDENTIAL_ENVIRONMENT_NAMES = (
    "BYBIT_API_KEY",
    "BYBIT_API_SECRET",
    "FT_EXCHANGE_KEY",
    "FT_EXCHANGE_SECRET",
    "FREQTRADE__EXCHANGE__KEY",
    "FREQTRADE__EXCHANGE__SECRET",
)


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


def _require_mapping(value: object, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{field_name} must be an object")
    return value


def _require_sequence(value: object, *, field_name: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list")
    return value


def _number(value: object, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise TypeError(f"{field_name} must be numeric")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not parsed == parsed or parsed in (float("inf"), float("-inf")):
        raise ValueError(f"{field_name} must be finite")
    return parsed


def _boolean(value: object, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean")
    return value


@dataclass(slots=True)
class LatencyHistogram:
    count: int = 0
    total_ms: int = 0
    minimum_ms: int | None = None
    maximum_ms: int | None = None
    bucket_counts: list[int] = field(
        default_factory=lambda: [0] * (len(LATENCY_BUCKET_UPPER_BOUNDS_MS) + 1)
    )

    def observe(self, latency_ms: int) -> None:
        if latency_ms < 0:
            raise ValueError("latency_ms must be >= 0")
        self.count += 1
        self.total_ms += latency_ms
        if self.minimum_ms is None or latency_ms < self.minimum_ms:
            self.minimum_ms = latency_ms
        if self.maximum_ms is None or latency_ms > self.maximum_ms:
            self.maximum_ms = latency_ms

        for index, upper_bound in enumerate(LATENCY_BUCKET_UPPER_BOUNDS_MS):
            if latency_ms <= upper_bound:
                self.bucket_counts[index] += 1
                break
        else:
            self.bucket_counts[-1] += 1

    def count_over(self, threshold_ms: int) -> int:
        if threshold_ms < 0:
            raise ValueError("threshold_ms must be >= 0")
        return sum(
            count
            for upper_bound, count in zip(
                (*LATENCY_BUCKET_UPPER_BOUNDS_MS, None),
                self.bucket_counts,
                strict=True,
            )
            if upper_bound is None or upper_bound > threshold_ms
        )

    def as_json_dict(self) -> dict[str, Any]:
        buckets = {
            f"le_{upper_bound}_ms": self.bucket_counts[index]
            for index, upper_bound in enumerate(LATENCY_BUCKET_UPPER_BOUNDS_MS)
        }
        buckets[f"gt_{LATENCY_BUCKET_UPPER_BOUNDS_MS[-1]}_ms"] = self.bucket_counts[-1]
        return {
            "count": self.count,
            "minimum_ms": self.minimum_ms,
            "maximum_ms": self.maximum_ms,
            "mean_ms": self.total_ms / self.count if self.count else None,
            "buckets": buckets,
        }


@dataclass(frozen=True, slots=True)
class ConnectionInterval:
    opened_at_ms: int
    closed_at_ms: int
    close_reason: str
    disconnected: bool

    @property
    def duration_ms(self) -> int:
        return max(0, self.closed_at_ms - self.opened_at_ms)

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "opened_at_ms": self.opened_at_ms,
            "closed_at_ms": self.closed_at_ms,
            "duration_ms": self.duration_ms,
            "close_reason": self.close_reason,
            "disconnected": self.disconnected,
        }


@dataclass(slots=True)
class CollectorRunStats:
    started_at_ms: int
    messages_received: int = 0
    control_messages: int = 0
    liquidation_messages: int = 0
    events_parsed: int = 0
    events_written: int = 0
    duplicates: int = 0
    parse_failures: int = 0
    connections: int = 0
    disconnects: int = 0
    first_message_at_ms: int | None = None
    last_message_at_ms: int | None = None
    first_event_at_ms: int | None = None
    last_event_at_ms: int | None = None
    events_by_symbol: dict[str, int] = field(default_factory=dict)
    latency: LatencyHistogram = field(default_factory=LatencyHistogram)
    connection_intervals: list[ConnectionInterval] = field(default_factory=list)
    ended_at_ms: int | None = None
    run_status: str = "running"
    _current_connection_opened_at_ms: int | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def connection_opened(self, opened_at_ms: int) -> None:
        if self._current_connection_opened_at_ms is not None:
            raise RuntimeError("connection interval is already open")
        self.connections += 1
        self._current_connection_opened_at_ms = opened_at_ms

    def connection_closed(
        self,
        closed_at_ms: int,
        *,
        reason: str,
        disconnected: bool,
    ) -> None:
        opened_at_ms = self._current_connection_opened_at_ms
        if opened_at_ms is None:
            return
        self.connection_intervals.append(
            ConnectionInterval(
                opened_at_ms=opened_at_ms,
                closed_at_ms=max(closed_at_ms, opened_at_ms),
                close_reason=reason,
                disconnected=disconnected,
            )
        )
        if disconnected:
            self.disconnects += 1
        self._current_connection_opened_at_ms = None

    def record_connection_failure(self) -> None:
        self.disconnects += 1

    def record_message(self, received_at_ms: int, *, message_kind: str) -> None:
        if message_kind not in {"control", "liquidation", "malformed"}:
            raise ValueError(f"unsupported message_kind: {message_kind}")
        self.messages_received += 1
        if self.first_message_at_ms is None:
            self.first_message_at_ms = received_at_ms
        self.last_message_at_ms = received_at_ms
        if message_kind == "liquidation":
            self.liquidation_messages += 1
        elif message_kind == "control":
            self.control_messages += 1

    def record_events(
        self,
        events: Sequence[LiquidationEvent],
        *,
        written_count: int,
        duplicates: int,
    ) -> None:
        self.events_parsed += len(events)
        self.events_written += written_count
        self.duplicates += duplicates
        for event in events:
            symbol = str(event.symbol).upper()
            self.events_by_symbol[symbol] = self.events_by_symbol.get(symbol, 0) + 1
            occurred_at_ms = int(event.occurred_at_ms)
            if self.first_event_at_ms is None or occurred_at_ms < self.first_event_at_ms:
                self.first_event_at_ms = occurred_at_ms
            if self.last_event_at_ms is None or occurred_at_ms > self.last_event_at_ms:
                self.last_event_at_ms = occurred_at_ms
            self.latency.observe(int(event.ingest_latency_ms))

    def finish(self, ended_at_ms: int, *, status: str) -> None:
        if self._current_connection_opened_at_ms is not None:
            self.connection_closed(
                ended_at_ms,
                reason=status,
                disconnected=False,
            )
        self.ended_at_ms = max(ended_at_ms, self.started_at_ms)
        self.run_status = status

    @property
    def duration_ms(self) -> int:
        end = self.ended_at_ms if self.ended_at_ms is not None else _now_ms()
        return max(0, end - self.started_at_ms)

    @property
    def connected_duration_ms(self) -> int:
        return sum(interval.duration_ms for interval in self.connection_intervals)

    @property
    def availability_ratio(self) -> float:
        if self.duration_ms == 0:
            return 0.0
        return min(1.0, self.connected_duration_ms / self.duration_ms)

    @property
    def disconnects_per_hour(self) -> float:
        if self.duration_ms == 0:
            return float(self.disconnects)
        return self.disconnects / (self.duration_ms / 3_600_000)

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "run_status": self.run_status,
            "started_at_ms": self.started_at_ms,
            "ended_at_ms": self.ended_at_ms,
            "duration_ms": self.duration_ms,
            "connected_duration_ms": self.connected_duration_ms,
            "availability_ratio": self.availability_ratio,
            "messages_received": self.messages_received,
            "control_messages": self.control_messages,
            "liquidation_messages": self.liquidation_messages,
            "events_parsed": self.events_parsed,
            "events_written": self.events_written,
            "duplicates": self.duplicates,
            "parse_failures": self.parse_failures,
            "connections": self.connections,
            "disconnects": self.disconnects,
            "disconnects_per_hour": self.disconnects_per_hour,
            "first_message_at_ms": self.first_message_at_ms,
            "last_message_at_ms": self.last_message_at_ms,
            "first_event_at_ms": self.first_event_at_ms,
            "last_event_at_ms": self.last_event_at_ms,
            "events_by_symbol": dict(sorted(self.events_by_symbol.items())),
            "latency": self.latency.as_json_dict(),
            "connection_intervals": [
                interval.as_json_dict() for interval in self.connection_intervals
            ],
        }


@dataclass(frozen=True, slots=True)
class ClockProbeResult:
    checked_at_ms: int
    server_time_url: str
    round_trip_ms: int | None
    absolute_skew_ms: int | None
    tolerance_ms: int
    synchronized: bool | None
    error: str | None = None

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "checked_at_ms": self.checked_at_ms,
            "server_time_url": self.server_time_url,
            "round_trip_ms": self.round_trip_ms,
            "absolute_skew_ms": self.absolute_skew_ms,
            "tolerance_ms": self.tolerance_ms,
            "synchronized": self.synchronized,
            "error": self.error,
        }


def parse_bybit_server_time_response(
    payload: Mapping[str, object],
    *,
    request_started_at_ms: int,
    request_ended_at_ms: int,
    tolerance_ms: int,
    server_time_url: str = DEFAULT_BYBIT_TIME_URL,
) -> ClockProbeResult:
    if request_ended_at_ms < request_started_at_ms:
        raise ValueError("request_ended_at_ms must be >= request_started_at_ms")
    if tolerance_ms < 0:
        raise ValueError("tolerance_ms must be >= 0")
    result = _require_mapping(payload.get("result"), field_name="result")
    server_time_seconds = integer_value(result["timeSecond"], field="result.timeSecond")
    server_time_ms = server_time_seconds * 1_000
    midpoint_ms = request_started_at_ms + (request_ended_at_ms - request_started_at_ms) // 2
    skew_ms = abs(server_time_ms - midpoint_ms)
    return ClockProbeResult(
        checked_at_ms=request_ended_at_ms,
        server_time_url=server_time_url,
        round_trip_ms=request_ended_at_ms - request_started_at_ms,
        absolute_skew_ms=skew_ms,
        tolerance_ms=tolerance_ms,
        synchronized=skew_ms <= tolerance_ms,
    )


def trading_credentials_present_in_environment(
    environment: Mapping[str, str] | None = None,
) -> bool:
    values = environment if environment is not None else os.environ
    return any(values.get(name, "").strip() for name in TRADING_CREDENTIAL_ENVIRONMENT_NAMES)


def _validated_https_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("server_time_url must be an absolute HTTPS URL")
    return url


def probe_bybit_clock(
    *,
    server_time_url: str = DEFAULT_BYBIT_TIME_URL,
    tolerance_ms: int = 2_000,
    timeout_seconds: float = 10.0,
) -> ClockProbeResult:
    started_at_ms = _now_ms()
    try:
        validated_url = _validated_https_url(server_time_url)
        with urllib.request.urlopen(  # noqa: S310 - URL is restricted to absolute HTTPS.
            validated_url,
            timeout=timeout_seconds,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        ended_at_ms = _now_ms()
        mapping = _require_mapping(payload, field_name="server_time_response")
        return parse_bybit_server_time_response(
            mapping,
            request_started_at_ms=started_at_ms,
            request_ended_at_ms=ended_at_ms,
            tolerance_ms=tolerance_ms,
            server_time_url=server_time_url,
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        ended_at_ms = _now_ms()
        return ClockProbeResult(
            checked_at_ms=ended_at_ms,
            server_time_url=server_time_url,
            round_trip_ms=ended_at_ms - started_at_ms,
            absolute_skew_ms=None,
            tolerance_ms=tolerance_ms,
            synchronized=None,
            error=f"{type(exc).__name__}: {exc}",
        )


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def build_collector_summary(
    *,
    stats: CollectorRunStats,
    endpoint: str,
    symbols: Sequence[str],
    output_path: Path,
    output_initial_size_bytes: int,
    collector_commit: str,
    clock_probe: ClockProbeResult,
    trading_credentials_present: bool,
) -> dict[str, Any]:
    output_size = output_path.stat().st_size
    return {
        "schema_version": 1,
        "summary_type": "liquidation_data_only_staging",
        "execution_enabled": False,
        "trading_credentials_present": trading_credentials_present,
        "collector_commit": collector_commit,
        "source": {
            "id": "bybit-linear",
            "endpoint": endpoint,
            "symbols": sorted(symbol.upper() for symbol in symbols),
        },
        "clock_probe": clock_probe.as_json_dict(),
        "output": {
            "file_name": output_path.name,
            "initial_size_bytes": output_initial_size_bytes,
            "final_size_bytes": output_size,
            "sha256": sha256_file(output_path),
            "line_count": stats.events_written,
        },
        "stats": stats.as_json_dict(),
    }


def write_json_atomic(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary_path.replace(path)


@dataclass(frozen=True, slots=True)
class StagingThresholds:
    minimum_duration_seconds: float
    minimum_messages_received: int
    maximum_parse_failures: int
    minimum_availability_ratio: float
    maximum_disconnects_per_hour: float
    maximum_duplicate_ratio: float
    latency_threshold_ms: int
    maximum_latency_over_threshold_ratio: float
    minimum_latency_samples: int
    minimum_events_per_symbol: int
    require_clock_synchronized: bool
    require_new_output: bool
    require_collector_commit: bool

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> StagingThresholds:
        return cls(
            minimum_duration_seconds=_number(
                payload["minimum_duration_seconds"],
                field_name="minimum_duration_seconds",
            ),
            minimum_messages_received=integer_value(
                payload["minimum_messages_received"],
                field="minimum_messages_received",
            ),
            maximum_parse_failures=integer_value(
                payload["maximum_parse_failures"],
                field="maximum_parse_failures",
            ),
            minimum_availability_ratio=_number(
                payload["minimum_availability_ratio"],
                field_name="minimum_availability_ratio",
            ),
            maximum_disconnects_per_hour=_number(
                payload["maximum_disconnects_per_hour"],
                field_name="maximum_disconnects_per_hour",
            ),
            maximum_duplicate_ratio=_number(
                payload["maximum_duplicate_ratio"],
                field_name="maximum_duplicate_ratio",
            ),
            latency_threshold_ms=integer_value(
                payload["latency_threshold_ms"],
                field="latency_threshold_ms",
            ),
            maximum_latency_over_threshold_ratio=_number(
                payload["maximum_latency_over_threshold_ratio"],
                field_name="maximum_latency_over_threshold_ratio",
            ),
            minimum_latency_samples=integer_value(
                payload["minimum_latency_samples"],
                field="minimum_latency_samples",
            ),
            minimum_events_per_symbol=integer_value(
                payload["minimum_events_per_symbol"],
                field="minimum_events_per_symbol",
            ),
            require_clock_synchronized=_boolean(
                payload["require_clock_synchronized"],
                field_name="require_clock_synchronized",
            ),
            require_new_output=_boolean(
                payload["require_new_output"],
                field_name="require_new_output",
            ),
            require_collector_commit=_boolean(
                payload["require_collector_commit"],
                field_name="require_collector_commit",
            ),
        )


@dataclass(frozen=True, slots=True)
class StagingPolicy:
    policy_id: str
    endpoint: str
    symbols: tuple[str, ...]
    thresholds: StagingThresholds

    @classmethod
    def load(cls, path: Path, *, mode: str) -> StagingPolicy:
        with path.open(encoding="utf-8") as handle:
            payload = _require_mapping(json.load(handle), field_name="policy")
        if integer_value(payload["schema_version"], field="schema_version") != 1:
            raise ValueError("policy schema_version must be 1")
        modes = _require_mapping(payload["modes"], field_name="modes")
        thresholds = _require_mapping(modes[mode], field_name=f"modes.{mode}")
        symbols = tuple(
            str(symbol).upper()
            for symbol in _require_sequence(payload["symbols"], field_name="symbols")
        )
        return cls(
            policy_id=str(payload["policy_id"]),
            endpoint=str(payload["endpoint"]),
            symbols=symbols,
            thresholds=StagingThresholds.from_mapping(thresholds),
        )


@dataclass(frozen=True, slots=True)
class GateResult:
    gate: str
    passed: bool
    actual: object
    expected: object

    def as_json_dict(self) -> dict[str, object]:
        return {
            "gate": self.gate,
            "passed": self.passed,
            "actual": self.actual,
            "expected": self.expected,
        }


def _nested_mapping(
    payload: Mapping[str, object],
    key: str,
    *,
    parent: str,
) -> Mapping[str, Any]:
    return _require_mapping(payload[key], field_name=f"{parent}.{key}")


def evaluate_staging_summary(
    summary: Mapping[str, object],
    *,
    policy: StagingPolicy,
    mode: str,
) -> dict[str, Any]:
    source = _nested_mapping(summary, "source", parent="summary")
    clock_probe = _nested_mapping(summary, "clock_probe", parent="summary")
    output = _nested_mapping(summary, "output", parent="summary")
    stats = _nested_mapping(summary, "stats", parent="summary")
    latency = _nested_mapping(stats, "latency", parent="summary.stats")
    events_by_symbol = _nested_mapping(stats, "events_by_symbol", parent="summary.stats")

    duration_seconds = _number(stats["duration_ms"], field_name="stats.duration_ms") / 1_000
    messages_received = integer_value(
        stats["messages_received"],
        field="stats.messages_received",
    )
    parse_failures = integer_value(stats["parse_failures"], field="stats.parse_failures")
    availability_ratio = _number(
        stats["availability_ratio"],
        field_name="stats.availability_ratio",
    )
    disconnects_per_hour = _number(
        stats["disconnects_per_hour"],
        field_name="stats.disconnects_per_hour",
    )
    events_parsed = integer_value(stats["events_parsed"], field="stats.events_parsed")
    duplicates = integer_value(stats["duplicates"], field="stats.duplicates")
    duplicate_ratio = duplicates / events_parsed if events_parsed else 0.0
    latency_count = integer_value(latency["count"], field="stats.latency.count")

    buckets = _nested_mapping(latency, "buckets", parent="summary.stats.latency")
    latency_over_threshold = 0
    for label, raw_count in buckets.items():
        if label.startswith("gt_"):
            lower_bound = int(label.removeprefix("gt_").removesuffix("_ms"))
            if lower_bound >= policy.thresholds.latency_threshold_ms:
                latency_over_threshold += integer_value(
                    raw_count,
                    field=f"stats.latency.buckets.{label}",
                )
        elif label.startswith("le_"):
            upper_bound = int(label.removeprefix("le_").removesuffix("_ms"))
            if upper_bound > policy.thresholds.latency_threshold_ms:
                latency_over_threshold += integer_value(
                    raw_count,
                    field=f"stats.latency.buckets.{label}",
                )
    latency_over_ratio = latency_over_threshold / latency_count if latency_count else 0.0

    actual_symbols = tuple(
        sorted(
            str(symbol).upper()
            for symbol in _require_sequence(source["symbols"], field_name="source.symbols")
        )
    )
    expected_symbols = tuple(sorted(policy.symbols))
    output_hash = str(output["sha256"])
    output_hash_valid = len(output_hash) == 64 and all(
        character in "0123456789abcdef" for character in output_hash
    )
    initial_size = integer_value(
        output["initial_size_bytes"],
        field="output.initial_size_bytes",
    )
    events_written = integer_value(stats["events_written"], field="stats.events_written")
    line_count = integer_value(output["line_count"], field="output.line_count")
    synchronized = clock_probe.get("synchronized")

    collector_commit = str(summary.get("collector_commit", ""))
    collector_commit_valid = len(collector_commit) == 40 and all(
        character in "0123456789abcdef" for character in collector_commit
    )
    gates = [
        GateResult(
            "summary_schema_version",
            summary.get("schema_version") == 1,
            summary.get("schema_version"),
            1,
        ),
        GateResult(
            "summary_type",
            summary.get("summary_type") == "liquidation_data_only_staging",
            summary.get("summary_type"),
            "liquidation_data_only_staging",
        ),
        GateResult(
            "run_status",
            stats.get("run_status") == "completed_duration",
            stats.get("run_status"),
            "completed_duration",
        ),
        GateResult(
            "execution_disabled",
            summary.get("execution_enabled") is False,
            summary.get("execution_enabled"),
            False,
        ),
        GateResult(
            "trading_credentials_absent",
            summary.get("trading_credentials_present") is False,
            summary.get("trading_credentials_present"),
            False,
        ),
        GateResult(
            "source_id",
            source.get("id") == "bybit-linear",
            source.get("id"),
            "bybit-linear",
        ),
        GateResult(
            "endpoint",
            str(source["endpoint"]) == policy.endpoint,
            source["endpoint"],
            policy.endpoint,
        ),
        GateResult(
            "collector_commit",
            not policy.thresholds.require_collector_commit or collector_commit_valid,
            collector_commit,
            "40 lowercase hexadecimal characters",
        ),
        GateResult("symbols", actual_symbols == expected_symbols, actual_symbols, expected_symbols),
        GateResult(
            "minimum_duration_seconds",
            duration_seconds >= policy.thresholds.minimum_duration_seconds,
            duration_seconds,
            policy.thresholds.minimum_duration_seconds,
        ),
        GateResult(
            "minimum_messages_received",
            messages_received >= policy.thresholds.minimum_messages_received,
            messages_received,
            policy.thresholds.minimum_messages_received,
        ),
        GateResult(
            "maximum_parse_failures",
            parse_failures <= policy.thresholds.maximum_parse_failures,
            parse_failures,
            policy.thresholds.maximum_parse_failures,
        ),
        GateResult(
            "minimum_availability_ratio",
            availability_ratio >= policy.thresholds.minimum_availability_ratio,
            availability_ratio,
            policy.thresholds.minimum_availability_ratio,
        ),
        GateResult(
            "maximum_disconnects_per_hour",
            disconnects_per_hour <= policy.thresholds.maximum_disconnects_per_hour,
            disconnects_per_hour,
            policy.thresholds.maximum_disconnects_per_hour,
        ),
        GateResult(
            "maximum_duplicate_ratio",
            duplicate_ratio <= policy.thresholds.maximum_duplicate_ratio,
            duplicate_ratio,
            policy.thresholds.maximum_duplicate_ratio,
        ),
        GateResult(
            "minimum_latency_samples",
            latency_count >= policy.thresholds.minimum_latency_samples,
            latency_count,
            policy.thresholds.minimum_latency_samples,
        ),
        GateResult(
            "maximum_latency_over_threshold_ratio",
            latency_over_ratio <= policy.thresholds.maximum_latency_over_threshold_ratio,
            latency_over_ratio,
            policy.thresholds.maximum_latency_over_threshold_ratio,
        ),
        GateResult("output_sha256", output_hash_valid, output_hash, "64 lowercase hex characters"),
        GateResult("event_line_count", line_count == events_written, line_count, events_written),
        GateResult(
            "new_output",
            not policy.thresholds.require_new_output or initial_size == 0,
            initial_size,
            0,
        ),
        GateResult(
            "clock_synchronized",
            not policy.thresholds.require_clock_synchronized or synchronized is True,
            synchronized,
            True,
        ),
    ]

    for symbol in expected_symbols:
        event_count = integer_value(
            events_by_symbol.get(symbol, 0),
            field=f"stats.events_by_symbol.{symbol}",
        )
        gates.append(
            GateResult(
                f"minimum_events_{symbol}",
                event_count >= policy.thresholds.minimum_events_per_symbol,
                event_count,
                policy.thresholds.minimum_events_per_symbol,
            )
        )

    passed = all(gate.passed for gate in gates)
    return {
        "schema_version": 1,
        "report_type": "liquidation_data_only_staging_evaluation",
        "policy_id": policy.policy_id,
        "mode": mode,
        "passed": passed,
        "gates": [gate.as_json_dict() for gate in gates],
        "failed_gates": [gate.gate for gate in gates if not gate.passed],
    }
