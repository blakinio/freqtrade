from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import time
import urllib.parse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from ai_platform.market_data.binance_spot_instrument_smoke import (
    BINANCE_SPOT_REDUCED_PAYLOAD_URL,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    REDUCED_PAYLOAD_POLICY_VERSION,
    SmokeExecutionError,
    SmokePolicy,
    UrlOpener,
    _decode_object,
    _fetch_once,
)
from ai_platform.market_data.common import (
    canonical_json_bytes,
    canonical_sha256,
    refuse_trading_credentials,
    validate_commit,
)
from ai_platform.market_data.instrument_adapters import (
    InstrumentCatalogSnapshot,
    parse_binance_spot_catalog,
)


POLICY_PATH = Path(
    "ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json"
)
POLICY_ID = "binance-spot-instrument-shadow-acceptance-v1"
CLASSIFICATION = "shadow_source_operational_acceptance"
MANIFEST_VERSION = "binance-spot-instrument-acceptance-manifest-v1"
REPORT_VERSION = "binance-spot-instrument-acceptance-report-v1"
SUMMARY_VERSION = "binance-spot-instrument-acceptance-summary-v1"
SAMPLE_REPORT_VERSION = "binance-spot-instrument-acceptance-sample-report-v1"
MANIFEST_NAME = "binance-spot-instrument-acceptance-manifest.json"
REPORT_NAME = "binance-spot-instrument-acceptance-report.json"
SUMMARY_NAME = "binance-spot-instrument-acceptance-summary.json"
SHA256_NAME = "artifact-sha256.txt"
REQUEST_NAME = "run-request.json"
POLICY_NAME = "policy.json"
SAMPLES_DIR_NAME = "samples"
PROXY_ENV_NAMES = frozenset(
    {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"}
)
EXPECTED_OUTCOMES = frozenset({"accepted", "rejected", "inconclusive_incomplete_window"})


class Sleeper(Protocol):
    def __call__(self, seconds: float) -> None: ...


class MonotonicClock(Protocol):
    def __call__(self) -> float: ...


class WallClockNs(Protocol):
    def __call__(self) -> int: ...


@dataclass(frozen=True, slots=True)
class AcceptanceThresholds:
    minimum_duration_seconds: int
    minimum_attempted_samples: int
    minimum_successful_samples: int
    minimum_availability_ratio: float
    maximum_consecutive_failures: int
    maximum_transport_failures: int
    maximum_parse_failures: int
    maximum_integrity_failures: int
    maximum_response_duration_ms: float
    maximum_response_bytes: int
    minimum_instrument_count: int
    maximum_instrument_count: int
    minimum_active_instrument_count: int
    maximum_consecutive_catalog_count_change_ratio: float
    required_active_native_symbols: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BinanceSpotInstrumentAcceptancePolicy:
    policy_id: str
    source_id: str
    request_url: str
    minimum_duration_seconds: int
    sample_interval_seconds: int
    timeout_seconds: int
    max_response_bytes: int
    allow_redirects: bool
    retries_per_sample: int
    required_host_class: str
    github_hosted_runner_allowed: bool
    baseline_evidence: Mapping[str, object]
    thresholds: AcceptanceThresholds
    requirements: Mapping[str, object]
    durability: Mapping[str, object]
    outcomes: Mapping[str, object]
    boundary: str

    @classmethod
    def load(cls, path: Path = POLICY_PATH) -> BinanceSpotInstrumentAcceptancePolicy:  # noqa: C901
        payload = _load_object(path)
        if _integer(payload.get("schema_version"), field="schema_version") != 1:
            raise ValueError("policy schema_version must be 1")
        if payload.get("classification") != CLASSIFICATION:
            raise ValueError("unexpected policy classification")
        if payload.get("policy_id") != POLICY_ID:
            raise ValueError("unexpected policy_id")
        if payload.get("source_id") != "binance-spot":
            raise ValueError("policy source_id must be binance-spot")
        if payload.get("request_url") != BINANCE_SPOT_REDUCED_PAYLOAD_URL:
            raise ValueError("policy request_url must remain frozen")
        minimum_duration_seconds = _integer(
            payload.get("minimum_duration_seconds"), field="minimum_duration_seconds"
        )
        if minimum_duration_seconds < 86_400:
            raise ValueError("minimum_duration_seconds must be at least 86400")
        sample_interval_seconds = _integer(
            payload.get("sample_interval_seconds"), field="sample_interval_seconds"
        )
        if sample_interval_seconds != 900:
            raise ValueError("sample_interval_seconds must remain frozen at 900")
        if (
            _integer(payload.get("timeout_seconds"), field="timeout_seconds")
            != DEFAULT_TIMEOUT_SECONDS
        ):
            raise ValueError("timeout_seconds must remain frozen")
        if (
            _integer(payload.get("max_response_bytes"), field="max_response_bytes")
            != DEFAULT_MAX_RESPONSE_BYTES
        ):
            raise ValueError("max_response_bytes must remain frozen")
        if payload.get("allow_redirects") is not False:
            raise ValueError("redirects must remain forbidden")
        if (
            _integer(
                payload.get("retries_per_sample"),
                field="retries_per_sample",
                minimum=0,
            )
            != 0
        ):
            raise ValueError("retries_per_sample must remain zero")

        host = _mapping(payload.get("host"), field="host")
        if host.get("required_class") != "always_on_nonrestricted_linux_staging":
            raise ValueError("unexpected required host class")
        if host.get("exact_host_id_required") is not True:
            raise ValueError("policy must require exact host_id")
        if host.get("github_hosted_runner_allowed") is not False:
            raise ValueError("GitHub-hosted runners must remain forbidden")

        baseline = dict(_mapping(payload.get("baseline_evidence"), field="baseline_evidence"))
        if (
            _integer(baseline.get("artifact_id"), field="baseline_evidence.artifact_id")
            != 8686988992
        ):
            raise ValueError("baseline artifact_id does not match reviewed smoke evidence")
        if (
            _text(
                baseline.get("artifact_digest"),
                field="baseline_evidence.artifact_digest",
            )
            != "sha256:1862d17e8c117e31eec6688c8f34c32cce4a505ec125805cd095df6894cc4f6e"
        ):
            raise ValueError("baseline artifact digest does not match reviewed smoke evidence")

        threshold_map = _mapping(payload.get("thresholds"), field="thresholds")
        required_symbols = tuple(
            _text(item, field="thresholds.required_active_native_symbols[]").upper()
            for item in _sequence(
                threshold_map.get("required_active_native_symbols"),
                field="thresholds.required_active_native_symbols",
            )
        )
        if required_symbols != ("BTCUSDT", "ETHUSDT"):
            raise ValueError("required symbol anchors must remain BTCUSDT and ETHUSDT")
        thresholds = AcceptanceThresholds(
            minimum_duration_seconds=_integer(
                threshold_map.get("minimum_duration_seconds"),
                field="thresholds.minimum_duration_seconds",
            ),
            minimum_attempted_samples=_integer(
                threshold_map.get("minimum_attempted_samples"),
                field="thresholds.minimum_attempted_samples",
            ),
            minimum_successful_samples=_integer(
                threshold_map.get("minimum_successful_samples"),
                field="thresholds.minimum_successful_samples",
            ),
            minimum_availability_ratio=_ratio(
                threshold_map.get("minimum_availability_ratio"),
                field="thresholds.minimum_availability_ratio",
            ),
            maximum_consecutive_failures=_integer(
                threshold_map.get("maximum_consecutive_failures"),
                field="thresholds.maximum_consecutive_failures",
                minimum=0,
            ),
            maximum_transport_failures=_integer(
                threshold_map.get("maximum_transport_failures"),
                field="thresholds.maximum_transport_failures",
                minimum=0,
            ),
            maximum_parse_failures=_integer(
                threshold_map.get("maximum_parse_failures"),
                field="thresholds.maximum_parse_failures",
                minimum=0,
            ),
            maximum_integrity_failures=_integer(
                threshold_map.get("maximum_integrity_failures"),
                field="thresholds.maximum_integrity_failures",
                minimum=0,
            ),
            maximum_response_duration_ms=_positive_number(
                threshold_map.get("maximum_response_duration_ms"),
                field="thresholds.maximum_response_duration_ms",
            ),
            maximum_response_bytes=_integer(
                threshold_map.get("maximum_response_bytes"),
                field="thresholds.maximum_response_bytes",
            ),
            minimum_instrument_count=_integer(
                threshold_map.get("minimum_instrument_count"),
                field="thresholds.minimum_instrument_count",
            ),
            maximum_instrument_count=_integer(
                threshold_map.get("maximum_instrument_count"),
                field="thresholds.maximum_instrument_count",
            ),
            minimum_active_instrument_count=_integer(
                threshold_map.get("minimum_active_instrument_count"),
                field="thresholds.minimum_active_instrument_count",
            ),
            maximum_consecutive_catalog_count_change_ratio=_ratio(
                threshold_map.get("maximum_consecutive_catalog_count_change_ratio"),
                field="thresholds.maximum_consecutive_catalog_count_change_ratio",
            ),
            required_active_native_symbols=required_symbols,
        )
        if thresholds.minimum_duration_seconds != minimum_duration_seconds:
            raise ValueError("duration thresholds disagree")
        expected_samples = minimum_duration_seconds // sample_interval_seconds + 1
        if thresholds.minimum_attempted_samples != expected_samples:
            raise ValueError("minimum_attempted_samples must cover every scheduled slot")
        if thresholds.maximum_response_bytes != DEFAULT_MAX_RESPONSE_BYTES:
            raise ValueError("threshold response byte limit must match transport limit")
        if thresholds.minimum_successful_samples > thresholds.minimum_attempted_samples:
            raise ValueError("minimum successful samples cannot exceed attempted samples")
        if thresholds.maximum_instrument_count > 10_000:
            raise ValueError("maximum instrument count exceeds adapter bound")

        requirements = dict(_mapping(payload.get("requirements"), field="requirements"))
        for key, expected in (
            ("public_only", True),
            ("execution_enabled", False),
            ("trading_credentials_present", False),
            ("proxy_routing_present", False),
            ("performance_research_authorized", False),
            ("replay_authorized", False),
            ("model_training_authorized", False),
            ("strategy_research_authorized", False),
            ("orders_submitted", 0),
            ("production_source_enabled", False),
            ("raw_snapshots", True),
            ("normalized_snapshots", True),
            ("independent_evaluation", True),
        ):
            if requirements.get(key) != expected:
                raise ValueError(f"policy requirement {key} must equal {expected!r}")

        durability = dict(_mapping(payload.get("durability"), field="durability"))
        if durability.get("immutable_storage_uri_required") is not True:
            raise ValueError("immutable storage URI must be required")
        if durability.get("ephemeral_ci_artifact_alone_is_sufficient") is not False:
            raise ValueError("ephemeral CI artifact alone must remain insufficient")
        for key in (
            "raw_snapshots_required",
            "normalized_snapshots_required",
            "sample_reports_required",
            "summary_required",
            "manifest_required",
            "report_required",
            "checksum_index_required",
        ):
            if durability.get(key) is not True:
                raise ValueError(f"durability requirement {key} must be true")

        outcomes = dict(_mapping(payload.get("outcomes"), field="outcomes"))
        if set(outcomes) != EXPECTED_OUTCOMES:
            raise ValueError("policy outcomes do not match frozen outcome model")
        return cls(
            policy_id=POLICY_ID,
            source_id="binance-spot",
            request_url=BINANCE_SPOT_REDUCED_PAYLOAD_URL,
            minimum_duration_seconds=minimum_duration_seconds,
            sample_interval_seconds=sample_interval_seconds,
            timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
            max_response_bytes=DEFAULT_MAX_RESPONSE_BYTES,
            allow_redirects=False,
            retries_per_sample=0,
            required_host_class="always_on_nonrestricted_linux_staging",
            github_hosted_runner_allowed=False,
            baseline_evidence=baseline,
            thresholds=thresholds,
            requirements=requirements,
            durability=durability,
            outcomes=outcomes,
            boundary=_text(payload.get("boundary"), field="boundary"),
        )


@dataclass(frozen=True, slots=True)
class AcceptanceRequest:
    request_id: str
    run_id: str
    host_id: str
    host_class: str
    duration_seconds: int
    sample_interval_seconds: int
    durable_storage_uri: str
    baseline_artifact_id: int
    baseline_artifact_digest: str


@dataclass(frozen=True, slots=True)
class Gate:
    name: str
    passed: bool
    actual: object
    expected: object
    category: str

    def as_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "actual": self.actual,
            "expected": self.expected,
            "category": self.category,
        }


def _load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be an object")
    return value


def _sequence(value: object, *, field: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be an array")
    return value


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _integer(value: object, *, field: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def _positive_number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{field} must be numeric")
    parsed = float(value)
    if parsed <= 0:
        raise ValueError(f"{field} must be > 0")
    return parsed


def _ratio(value: object, *, field: str) -> float:
    parsed = _positive_number(value, field=field)
    if parsed > 1:
        raise ValueError(f"{field} must be <= 1")
    return parsed


def _identity(value: object, *, field: str) -> str:
    text = _text(value, field=field)
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,100}", text):
        raise ValueError(f"{field} contains unsupported characters")
    return text


def _validated_durable_uri(value: object) -> str:
    uri = _text(value, field="request.durable_storage_uri")
    parsed = urllib.parse.urlsplit(uri)
    if parsed.scheme != "file" or not parsed.path.startswith("/"):
        raise ValueError("durable_storage_uri must be an absolute file URI")
    if parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(
            "durable_storage_uri must not contain authority, credentials, query or fragment"
        )
    return uri


def validate_request(  # noqa: C901
    payload: Mapping[str, object],
    *,
    policy: BinanceSpotInstrumentAcceptancePolicy,
) -> AcceptanceRequest:
    if _integer(payload.get("schema_version"), field="request.schema_version") != 1:
        raise ValueError("request schema_version must be 1")
    if payload.get("policy_id") != policy.policy_id:
        raise ValueError("request policy_id does not match policy")
    if payload.get("source_id") != policy.source_id:
        raise ValueError("request source_id does not match policy")
    if payload.get("request_url") != policy.request_url:
        raise ValueError("request_url does not match frozen policy")
    if payload.get("host_class") != policy.required_host_class:
        raise ValueError("request host_class does not match policy")
    if payload.get("github_hosted_runner") is not False:
        raise ValueError("GitHub-hosted runner must remain forbidden")
    duration = _integer(payload.get("duration_seconds"), field="request.duration_seconds")
    if duration < policy.minimum_duration_seconds:
        raise ValueError("request duration is shorter than policy minimum")
    interval = _integer(
        payload.get("sample_interval_seconds"), field="request.sample_interval_seconds"
    )
    if interval != policy.sample_interval_seconds:
        raise ValueError("request sample interval does not match policy")
    for key, expected in (
        ("public_only", True),
        ("execution_enabled", False),
        ("trading_credentials_present", False),
        ("proxy_routing_present", False),
        ("performance_research_authorized", False),
        ("replay_authorized", False),
        ("model_training_authorized", False),
        ("strategy_research_authorized", False),
        ("orders_submitted", 0),
        ("production_source_enabled", False),
    ):
        if payload.get(key) != expected:
            raise ValueError(f"request {key} must equal {expected!r}")
    baseline_id = _integer(
        payload.get("baseline_artifact_id"), field="request.baseline_artifact_id"
    )
    baseline_digest = _text(
        payload.get("baseline_artifact_digest"), field="request.baseline_artifact_digest"
    )
    if baseline_id != policy.baseline_evidence["artifact_id"]:
        raise ValueError("request baseline artifact id mismatch")
    if baseline_digest != policy.baseline_evidence["artifact_digest"]:
        raise ValueError("request baseline artifact digest mismatch")
    return AcceptanceRequest(
        request_id=_identity(payload.get("request_id"), field="request.request_id"),
        run_id=_identity(payload.get("run_id"), field="request.run_id"),
        host_id=_identity(payload.get("host_id"), field="request.host_id"),
        host_class=policy.required_host_class,
        duration_seconds=duration,
        sample_interval_seconds=interval,
        durable_storage_uri=_validated_durable_uri(payload.get("durable_storage_uri")),
        baseline_artifact_id=baseline_id,
        baseline_artifact_digest=baseline_digest,
    )


def refuse_proxy_environment(environment: Mapping[str, str]) -> None:
    present = sorted(name for name in PROXY_ENV_NAMES if environment.get(name, "").strip())
    if present:
        raise RuntimeError("acceptance refuses proxy environment variables: " + ", ".join(present))


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_atomic(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    with temporary.open("xb") as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _write_json_atomic(path: Path, value: object) -> None:
    _write_atomic(path, canonical_json_bytes(value) + b"\n")


def _sample_paths(root: Path, index: int) -> tuple[Path, Path, Path]:
    sample_root = root / SAMPLES_DIR_NAME / f"{index:04d}"
    return (
        sample_root / "raw-response.json",
        sample_root / "instrument-catalog-snapshot.json",
        sample_root / "sample-report.json",
    )


def _active_symbols(snapshot: InstrumentCatalogSnapshot) -> frozenset[str]:
    return frozenset(item.native_symbol for item in snapshot.instruments if item.active)


def _sample_success_report(
    *,
    index: int,
    scheduled_offset_seconds: int,
    raw_payload: bytes,
    snapshot: InstrumentCatalogSnapshot,
    status: int,
    content_type: str,
    final_url: str,
    started_ns: int,
    ended_ns: int,
    required_symbols: Sequence[str],
) -> dict[str, object]:
    active_count = sum(1 for item in snapshot.instruments if item.active)
    active_symbols = _active_symbols(snapshot)
    seed: dict[str, object] = {
        "sample_report_version": SAMPLE_REPORT_VERSION,
        "sample_index": index,
        "scheduled_offset_seconds": scheduled_offset_seconds,
        "status": "pass",
        "request_url": BINANCE_SPOT_REDUCED_PAYLOAD_URL,
        "final_url": final_url,
        "http_status": status,
        "content_type": content_type,
        "request_started_ns": started_ns,
        "response_completed_ns": ended_ns,
        "duration_ms": (ended_ns - started_ns) / 1_000_000,
        "response_bytes": len(raw_payload),
        "raw_response_sha256": _sha256_bytes(raw_payload),
        "instrument_count": len(snapshot.instruments),
        "active_instrument_count": active_count,
        "inactive_instrument_count": len(snapshot.instruments) - active_count,
        "required_active_symbols_present": {
            symbol: symbol in active_symbols for symbol in required_symbols
        },
        "source_snapshot_id": snapshot.source_snapshot_id,
        "source_snapshot_sha256": snapshot.source_snapshot_sha256,
        "catalog_snapshot_sha256": snapshot.snapshot_sha256,
        "attempt_count": 1,
        "redirect_count": 0,
        "source_acceptance": False,
        "production_source_enabled": False,
        "orders_submitted": 0,
    }
    return {**seed, "sample_report_sha256": canonical_sha256(seed)}


def _sample_failure_report(
    *,
    index: int,
    scheduled_offset_seconds: int,
    error: Exception,
    stage: str,
) -> dict[str, object]:
    details = error.details if isinstance(error, SmokeExecutionError) else None
    seed: dict[str, object] = {
        "sample_report_version": SAMPLE_REPORT_VERSION,
        "sample_index": index,
        "scheduled_offset_seconds": scheduled_offset_seconds,
        "status": "fail",
        "request_url": BINANCE_SPOT_REDUCED_PAYLOAD_URL,
        "failure_stage": details.stage if details else stage,
        "error_type": details.error_type if details else error.__class__.__name__,
        "error_message": str(error)[:500],
        "request_started_ns": details.request_started_ns if details else None,
        "response_completed_ns": details.response_completed_ns if details else None,
        "http_status": details.http_status if details else None,
        "content_type": details.content_type if details else None,
        "final_url": details.final_url if details else None,
        "declared_response_bytes": details.declared_response_bytes if details else None,
        "observed_response_bytes": details.observed_response_bytes if details else None,
        "attempt_count": 1,
        "raw_payload_persisted": False,
        "source_acceptance": False,
        "production_source_enabled": False,
        "orders_submitted": 0,
    }
    return {**seed, "sample_report_sha256": canonical_sha256(seed)}


def _catalog_count_change_ratio(previous: int, current: int) -> float:
    if previous <= 0:
        return 0.0
    return abs(current - previous) / previous


def _maximum_consecutive_failures(reports: Sequence[Mapping[str, object]]) -> int:
    maximum = 0
    current = 0
    for report in reports:
        if report.get("status") == "fail":
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0
    return maximum


def _summarize(
    *,
    request: AcceptanceRequest,
    started_ns: int,
    ended_ns: int,
    observed_duration_seconds: float,
    reports: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    successes = [report for report in reports if report.get("status") == "pass"]
    failures = [report for report in reports if report.get("status") == "fail"]
    durations = [float(report["duration_ms"]) for report in successes]
    response_bytes = [int(report["response_bytes"]) for report in successes]
    instrument_counts = [int(report["instrument_count"]) for report in successes]
    active_counts = [int(report["active_instrument_count"]) for report in successes]
    transport_failures = sum(
        1
        for report in failures
        if report.get("failure_stage") in {"transport", "response_headers", "response_body"}
    )
    parse_failures = sum(
        1 for report in failures if report.get("failure_stage") in {"decode", "parse_and_normalize"}
    )
    count_change_ratios = [
        _catalog_count_change_ratio(previous, current)
        for previous, current in itertools.pairwise(instrument_counts)
    ]
    anchor_failures = sum(
        1
        for report in successes
        if not all(
            bool(value)
            for value in _mapping(
                report.get("required_active_symbols_present"),
                field="sample.required_active_symbols_present",
            ).values()
        )
    )
    seed: dict[str, object] = {
        "summary_version": SUMMARY_VERSION,
        "source_id": "binance-spot",
        "request_url": BINANCE_SPOT_REDUCED_PAYLOAD_URL,
        "request_id": request.request_id,
        "run_id": request.run_id,
        "host_id": request.host_id,
        "started_ns": started_ns,
        "ended_ns": ended_ns,
        "observed_duration_seconds": observed_duration_seconds,
        "configured_duration_seconds": request.duration_seconds,
        "sample_interval_seconds": request.sample_interval_seconds,
        "scheduled_sample_count": request.duration_seconds // request.sample_interval_seconds + 1,
        "attempted_sample_count": len(reports),
        "successful_sample_count": len(successes),
        "failed_sample_count": len(failures),
        "availability_ratio": len(successes) / len(reports) if reports else 0.0,
        "maximum_consecutive_failures": _maximum_consecutive_failures(reports),
        "transport_failure_count": transport_failures,
        "parse_failure_count": parse_failures,
        "integrity_failure_count": 0,
        "anchor_symbol_failure_count": anchor_failures,
        "response_duration_ms_min": min(durations) if durations else None,
        "response_duration_ms_max": max(durations) if durations else None,
        "response_duration_ms_mean": sum(durations) / len(durations) if durations else None,
        "response_bytes_min": min(response_bytes) if response_bytes else None,
        "response_bytes_max": max(response_bytes) if response_bytes else None,
        "response_bytes_mean": sum(response_bytes) / len(response_bytes)
        if response_bytes
        else None,
        "instrument_count_min": min(instrument_counts) if instrument_counts else None,
        "instrument_count_max": max(instrument_counts) if instrument_counts else None,
        "active_instrument_count_min": min(active_counts) if active_counts else None,
        "active_instrument_count_max": max(active_counts) if active_counts else None,
        "maximum_consecutive_catalog_count_change_ratio": max(count_change_ratios)
        if count_change_ratios
        else 0.0,
        "distinct_source_snapshot_count": len(
            {str(report["source_snapshot_sha256"]) for report in successes}
        ),
        "baseline_artifact_id": request.baseline_artifact_id,
        "baseline_artifact_digest": request.baseline_artifact_digest,
        "source_acceptance": False,
        "production_source_enabled": False,
        "orders_submitted": 0,
    }
    return {**seed, "summary_sha256": canonical_sha256(seed)}


def _gates(
    summary: Mapping[str, object],
    *,
    policy: BinanceSpotInstrumentAcceptancePolicy,
) -> tuple[Gate, ...]:
    thresholds = policy.thresholds
    return (
        Gate(
            "minimum_duration_seconds",
            float(summary["observed_duration_seconds"]) >= thresholds.minimum_duration_seconds,
            summary["observed_duration_seconds"],
            thresholds.minimum_duration_seconds,
            "window",
        ),
        Gate(
            "minimum_attempted_samples",
            int(summary["attempted_sample_count"]) >= thresholds.minimum_attempted_samples,
            summary["attempted_sample_count"],
            thresholds.minimum_attempted_samples,
            "window",
        ),
        Gate(
            "minimum_successful_samples",
            int(summary["successful_sample_count"]) >= thresholds.minimum_successful_samples,
            summary["successful_sample_count"],
            thresholds.minimum_successful_samples,
            "availability",
        ),
        Gate(
            "minimum_availability_ratio",
            float(summary["availability_ratio"]) >= thresholds.minimum_availability_ratio,
            summary["availability_ratio"],
            thresholds.minimum_availability_ratio,
            "availability",
        ),
        Gate(
            "maximum_consecutive_failures",
            int(summary["maximum_consecutive_failures"]) <= thresholds.maximum_consecutive_failures,
            summary["maximum_consecutive_failures"],
            thresholds.maximum_consecutive_failures,
            "availability",
        ),
        Gate(
            "maximum_transport_failures",
            int(summary["transport_failure_count"]) <= thresholds.maximum_transport_failures,
            summary["transport_failure_count"],
            thresholds.maximum_transport_failures,
            "transport",
        ),
        Gate(
            "maximum_parse_failures",
            int(summary["parse_failure_count"]) <= thresholds.maximum_parse_failures,
            summary["parse_failure_count"],
            thresholds.maximum_parse_failures,
            "parsing",
        ),
        Gate(
            "maximum_integrity_failures",
            int(summary["integrity_failure_count"]) <= thresholds.maximum_integrity_failures,
            summary["integrity_failure_count"],
            thresholds.maximum_integrity_failures,
            "integrity",
        ),
        Gate(
            "maximum_response_duration_ms",
            summary["response_duration_ms_max"] is not None
            and float(summary["response_duration_ms_max"])
            <= thresholds.maximum_response_duration_ms,
            summary["response_duration_ms_max"],
            thresholds.maximum_response_duration_ms,
            "latency",
        ),
        Gate(
            "maximum_response_bytes",
            summary["response_bytes_max"] is not None
            and int(summary["response_bytes_max"]) <= thresholds.maximum_response_bytes,
            summary["response_bytes_max"],
            thresholds.maximum_response_bytes,
            "transport",
        ),
        Gate(
            "minimum_instrument_count",
            summary["instrument_count_min"] is not None
            and int(summary["instrument_count_min"]) >= thresholds.minimum_instrument_count,
            summary["instrument_count_min"],
            thresholds.minimum_instrument_count,
            "catalog",
        ),
        Gate(
            "maximum_instrument_count",
            summary["instrument_count_max"] is not None
            and int(summary["instrument_count_max"]) <= thresholds.maximum_instrument_count,
            summary["instrument_count_max"],
            thresholds.maximum_instrument_count,
            "catalog",
        ),
        Gate(
            "minimum_active_instrument_count",
            summary["active_instrument_count_min"] is not None
            and int(summary["active_instrument_count_min"])
            >= thresholds.minimum_active_instrument_count,
            summary["active_instrument_count_min"],
            thresholds.minimum_active_instrument_count,
            "catalog",
        ),
        Gate(
            "required_active_native_symbols",
            int(summary["anchor_symbol_failure_count"]) == 0,
            summary["anchor_symbol_failure_count"],
            0,
            "catalog",
        ),
        Gate(
            "maximum_consecutive_catalog_count_change_ratio",
            float(summary["maximum_consecutive_catalog_count_change_ratio"])
            <= thresholds.maximum_consecutive_catalog_count_change_ratio,
            summary["maximum_consecutive_catalog_count_change_ratio"],
            thresholds.maximum_consecutive_catalog_count_change_ratio,
            "catalog",
        ),
        Gate(
            "production_source_enabled",
            summary.get("production_source_enabled") is False,
            summary.get("production_source_enabled"),
            False,
            "safety",
        ),
        Gate(
            "orders_submitted",
            summary.get("orders_submitted") == 0,
            summary.get("orders_submitted"),
            0,
            "safety",
        ),
    )


def _outcome(gates: Sequence[Gate]) -> str:
    failed = [gate for gate in gates if not gate.passed]
    if not failed:
        return "accepted"
    if all(gate.category == "window" for gate in failed):
        return "inconclusive_incomplete_window"
    return "rejected"


def _artifact_entries(root: Path, paths: Sequence[Path]) -> list[dict[str, object]]:
    entries = []
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    return entries


def _seal_package(
    *,
    root: Path,
    request_mapping: Mapping[str, object],
    policy_mapping: Mapping[str, object],
    summary: Mapping[str, object],
    collector_commit: str,
    policy: BinanceSpotInstrumentAcceptancePolicy,
) -> dict[str, object]:
    _write_json_atomic(root / REQUEST_NAME, request_mapping)
    _write_json_atomic(root / POLICY_NAME, policy_mapping)
    _write_json_atomic(root / SUMMARY_NAME, summary)
    data_paths = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.name not in {MANIFEST_NAME, REPORT_NAME, SHA256_NAME}
    ]
    entries = _artifact_entries(root, data_paths)
    manifest_seed: dict[str, object] = {
        "manifest_version": MANIFEST_VERSION,
        "policy_id": policy.policy_id,
        "source_id": policy.source_id,
        "collector_commit": collector_commit,
        "artifacts": entries,
        "source_acceptance": False,
        "production_source_enabled": False,
        "orders_submitted": 0,
    }
    manifest = {**manifest_seed, "manifest_sha256": canonical_sha256(manifest_seed)}
    _write_json_atomic(root / MANIFEST_NAME, manifest)

    gates = _gates(summary, policy=policy)
    outcome = _outcome(gates)
    report_seed: dict[str, object] = {
        "report_version": REPORT_VERSION,
        "policy_id": policy.policy_id,
        "source_id": policy.source_id,
        "outcome": outcome,
        "gates": [gate.as_json() for gate in gates],
        "summary_sha256": summary["summary_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "collector_commit": collector_commit,
        "baseline_evidence": dict(policy.baseline_evidence),
        "source_acceptance": False,
        "production_source_enabled": False,
        "orders_submitted": 0,
        "boundary": policy.boundary,
    }
    report = {**report_seed, "report_sha256": canonical_sha256(report_seed)}
    _write_json_atomic(root / REPORT_NAME, report)

    checksum_paths = [
        path for path in root.rglob("*") if path.is_file() and path.name != SHA256_NAME
    ]
    checksum_lines = "".join(
        f"{_sha256_file(path)}  {path.relative_to(root).as_posix()}\n"
        for path in sorted(checksum_paths, key=lambda item: item.relative_to(root).as_posix())
    )
    _write_atomic(root / SHA256_NAME, checksum_lines.encode("utf-8"))
    return report


def run_acceptance(
    *,
    request_path: Path,
    policy_path: Path,
    output_root: Path,
    collector_commit: str,
    environment: Mapping[str, str] | None = None,
    opener: UrlOpener | None = None,
    sleeper: Sleeper = time.sleep,
    monotonic: MonotonicClock = time.monotonic,
    wall_clock_ns: WallClockNs = time.time_ns,
) -> dict[str, object]:
    commit = validate_commit(collector_commit, field="collector_commit")
    env = environment if environment is not None else os.environ
    refuse_trading_credentials(env)
    refuse_proxy_environment(env)
    policy_mapping = _load_object(policy_path)
    policy = BinanceSpotInstrumentAcceptancePolicy.load(policy_path)
    request_mapping = _load_object(request_path)
    request = validate_request(request_mapping, policy=policy)
    if output_root.exists():
        raise FileExistsError(f"output root already exists: {output_root}")
    output_root.mkdir(parents=True, exist_ok=False)
    (output_root / SAMPLES_DIR_NAME).mkdir()
    started_ns = wall_clock_ns()
    started_monotonic = monotonic()
    reports: list[dict[str, object]] = []
    expected_samples = request.duration_seconds // request.sample_interval_seconds + 1
    smoke_policy = SmokePolicy(
        version=REDUCED_PAYLOAD_POLICY_VERSION,
        source_id=policy.source_id,
        request_url=policy.request_url,
        timeout_seconds=policy.timeout_seconds,
        max_response_bytes=policy.max_response_bytes,
        allow_redirects=policy.allow_redirects,
        retries=policy.retries_per_sample,
        source_acceptance=False,
    )
    smoke_policy.validate()

    for index in range(expected_samples):
        offset = index * request.sample_interval_seconds
        delay = started_monotonic + offset - monotonic()
        if delay > 0:
            sleeper(delay)
        stage = "transport"
        raw_path, snapshot_path, report_path = _sample_paths(output_root, index)
        try:
            if opener is None:
                raw, status, content_type, final_url, sample_started, sample_ended = _fetch_once(
                    smoke_policy
                )
            else:
                raw, status, content_type, final_url, sample_started, sample_ended = _fetch_once(
                    smoke_policy, opener=opener
                )
            stage = "decode"
            payload = _decode_object(raw)
            stage = "parse_and_normalize"
            snapshot = parse_binance_spot_catalog(
                payload,
                captured_at_ms=sample_ended // 1_000_000,
                request_url=policy.request_url,
            )
            report = _sample_success_report(
                index=index,
                scheduled_offset_seconds=offset,
                raw_payload=raw,
                snapshot=snapshot,
                status=status,
                content_type=content_type,
                final_url=final_url,
                started_ns=sample_started,
                ended_ns=sample_ended,
                required_symbols=policy.thresholds.required_active_native_symbols,
            )
        except Exception as exc:
            report = _sample_failure_report(
                index=index,
                scheduled_offset_seconds=offset,
                error=exc,
                stage=stage,
            )
            _write_json_atomic(report_path, report)
        else:
            _write_atomic(raw_path, raw)
            _write_json_atomic(snapshot_path, snapshot.as_json_dict())
            _write_json_atomic(report_path, report)
        reports.append(report)

    ended_monotonic = monotonic()
    ended_ns = wall_clock_ns()
    summary = _summarize(
        request=request,
        started_ns=started_ns,
        ended_ns=ended_ns,
        observed_duration_seconds=max(0.0, ended_monotonic - started_monotonic),
        reports=reports,
    )
    return _seal_package(
        root=output_root,
        request_mapping=request_mapping,
        policy_mapping=policy_mapping,
        summary=summary,
        collector_commit=commit,
        policy=policy,
    )


def _verify_self_hash(value: Mapping[str, object], *, field: str, hash_field: str) -> None:
    claimed = _text(value.get(hash_field), field=f"{field}.{hash_field}")
    seed = dict(value)
    seed.pop(hash_field, None)
    if canonical_sha256(seed) != claimed:
        raise ValueError(f"{field} self hash mismatch")


def evaluate_package(*, run_root: Path, policy_path: Path) -> dict[str, object]:  # noqa: C901
    policy = BinanceSpotInstrumentAcceptancePolicy.load(policy_path)
    request_mapping = _load_object(run_root / REQUEST_NAME)
    request = validate_request(request_mapping, policy=policy)
    package_policy = _load_object(run_root / POLICY_NAME)
    external_policy = _load_object(policy_path)
    if canonical_json_bytes(package_policy) != canonical_json_bytes(external_policy):
        raise ValueError("packaged policy differs from evaluator policy")
    summary = _load_object(run_root / SUMMARY_NAME)
    manifest = _load_object(run_root / MANIFEST_NAME)
    report = _load_object(run_root / REPORT_NAME)
    _verify_self_hash(summary, field="summary", hash_field="summary_sha256")
    _verify_self_hash(manifest, field="manifest", hash_field="manifest_sha256")
    _verify_self_hash(report, field="report", hash_field="report_sha256")

    entries = _sequence(manifest.get("artifacts"), field="manifest.artifacts")
    seen: set[str] = set()
    for raw_entry in entries:
        entry = _mapping(raw_entry, field="manifest.artifact")
        relative = _text(entry.get("path"), field="manifest.artifact.path")
        if relative in seen:
            raise ValueError("manifest contains duplicate artifact path")
        seen.add(relative)
        path = run_root / relative
        if not path.is_file():
            raise ValueError(f"manifest artifact is missing: {relative}")
        if path.stat().st_size != _integer(
            entry.get("bytes"), field="manifest.artifact.bytes", minimum=0
        ):
            raise ValueError(f"manifest artifact size mismatch: {relative}")
        if _sha256_file(path) != _text(entry.get("sha256"), field="manifest.artifact.sha256"):
            raise ValueError(f"manifest artifact hash mismatch: {relative}")
    actual_data_paths = {
        path.relative_to(run_root).as_posix()
        for path in run_root.rglob("*")
        if path.is_file() and path.name not in {MANIFEST_NAME, REPORT_NAME, SHA256_NAME}
    }
    if seen != actual_data_paths:
        raise ValueError("manifest artifact set differs from package data files")

    report_paths = sorted((run_root / SAMPLES_DIR_NAME).glob("*/sample-report.json"))
    reports: list[dict[str, object]] = []
    for path in report_paths:
        sample = _load_object(path)
        _verify_self_hash(sample, field=path.as_posix(), hash_field="sample_report_sha256")
        if sample.get("status") == "pass":
            if not (path.parent / "raw-response.json").is_file():
                raise ValueError("successful sample raw response is missing")
            if not (path.parent / "instrument-catalog-snapshot.json").is_file():
                raise ValueError("successful sample normalized snapshot is missing")
        reports.append(sample)
    if len(reports) != int(summary["attempted_sample_count"]):
        raise ValueError("sample report count does not match summary")
    recomputed_summary = _summarize(
        request=request,
        started_ns=int(summary["started_ns"]),
        ended_ns=int(summary["ended_ns"]),
        observed_duration_seconds=float(summary["observed_duration_seconds"]),
        reports=reports,
    )
    if recomputed_summary != summary:
        raise ValueError("summary differs from independent sample recomputation")

    checksum_lines = (run_root / SHA256_NAME).read_text(encoding="utf-8").splitlines()
    indexed: dict[str, str] = {}
    for line in checksum_lines:
        digest, relative = line.split("  ", 1)
        if relative in indexed:
            raise ValueError("checksum index contains duplicate path")
        indexed[relative] = digest
        if _sha256_file(run_root / relative) != digest:
            raise ValueError(f"checksum index mismatch: {relative}")
    expected_indexed = {
        path.relative_to(run_root).as_posix()
        for path in run_root.rglob("*")
        if path.is_file() and path.name != SHA256_NAME
    }
    if set(indexed) != expected_indexed:
        raise ValueError("checksum index file set differs from package")

    recomputed_gates = _gates(summary, policy=policy)
    recomputed_outcome = _outcome(recomputed_gates)
    if report.get("outcome") != recomputed_outcome:
        raise ValueError("report outcome differs from independent evaluation")
    if report.get("gates") != [gate.as_json() for gate in recomputed_gates]:
        raise ValueError("report gates differ from independent evaluation")
    if report.get("summary_sha256") != summary.get("summary_sha256"):
        raise ValueError("report summary hash mismatch")
    if report.get("manifest_sha256") != manifest.get("manifest_sha256"):
        raise ValueError("report manifest hash mismatch")
    if report.get("source_acceptance") is not False:
        raise ValueError("source_acceptance must remain false")
    if report.get("production_source_enabled") is not False:
        raise ValueError("production_source_enabled must remain false")
    return report


def outcome_exit_code(outcome: object) -> int:
    if outcome == "accepted":
        return 0
    if outcome == "inconclusive_incomplete_window":
        return 2
    return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run or independently evaluate Binance Spot instrument shadow acceptance"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--request", type=Path, required=True)
    run_parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    run_parser.add_argument("--output-root", type=Path, required=True)
    run_parser.add_argument("--collector-commit", required=True)
    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--run-root", type=Path, required=True)
    evaluate_parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "run":
        report = run_acceptance(
            request_path=args.request,
            policy_path=args.policy,
            output_root=args.output_root,
            collector_commit=args.collector_commit,
        )
    else:
        report = evaluate_package(run_root=args.run_root, policy_path=args.policy)
    print(canonical_json_bytes(report).decode("utf-8"))
    return outcome_exit_code(report.get("outcome"))


if __name__ == "__main__":
    raise SystemExit(main())
