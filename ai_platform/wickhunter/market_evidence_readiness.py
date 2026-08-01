from __future__ import annotations

import argparse
import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any


CAPTURE_REQUEST_UNAVAILABLE = "CAPTURE_REQUEST_UNAVAILABLE"
SIMPLE_READY_STATUSES = frozenset(
    {
        "idle",
        "initialized",
        "not_due",
        "waiting",
        "waiting_for_interval_end",
    }
)
COMPLETED_READY_STATUSES = frozenset({"published", "supplement_completed"})
AUTHORITY_FALSE_FIELDS = (
    "execution_enabled",
    "trading_credentials_present",
    "model_execution_authorized",
    "replay_authorized",
    "performance_research_authorized",
    "live_capital_authorized",
)


def result_is_ready(result: Mapping[str, object]) -> bool:
    status = result.get("status")
    if not isinstance(status, str) or not status:
        return False
    if result.get("reason_code") == CAPTURE_REQUEST_UNAVAILABLE:
        return False
    if status in SIMPLE_READY_STATUSES:
        return True
    if status == "sampled":
        sample_status = result.get("sample_status")
        return sample_status is None or sample_status == "pass"
    if status in COMPLETED_READY_STATUSES:
        return result.get("outcome") == "accepted"
    return False


def collector_health_payload(
    *,
    schema_version: int,
    observed_at_ms: int,
    result: Mapping[str, object],
    authority: Mapping[str, object],
) -> dict[str, Any]:
    ready = result_is_ready(result)
    return {
        "schema_version": schema_version,
        "observed_at_ms": observed_at_ms,
        "live": True,
        "ready": ready,
        "healthy": ready,
        "result": dict(result),
        **authority,
    }


def health_payload_is_ready(
    payload: object,
    *,
    expected_schema_version: int,
    maximum_age_seconds: int,
    now_ms: int | None = None,
) -> bool:
    if not isinstance(payload, dict) or "result" not in payload:
        return False
    schema_version = payload.get("schema_version")
    if isinstance(schema_version, bool) or schema_version != expected_schema_version:
        return False
    if payload.get("live") is not True:
        return False
    if payload.get("ready") is not True or payload.get("healthy") is not True:
        return False
    result = payload.get("result")
    if not isinstance(result, dict) or not result_is_ready(result):
        return False
    observed_at_ms = payload.get("observed_at_ms")
    if isinstance(observed_at_ms, bool) or not isinstance(observed_at_ms, int):
        return False
    if (
        isinstance(maximum_age_seconds, bool)
        or not isinstance(maximum_age_seconds, int)
        or maximum_age_seconds < 1
    ):
        return False
    current_ms = time.time_ns() // 1_000_000 if now_ms is None else now_ms
    age_ms = current_ms - observed_at_ms
    if age_ms < 0 or age_ms > maximum_age_seconds * 1_000:
        return False
    orders_submitted = payload.get("orders_submitted")
    if isinstance(orders_submitted, bool) or orders_submitted != 0:
        return False
    return all(payload.get(field) is False for field in AUTHORITY_FALSE_FIELDS)


def load_health_file(path: Path) -> object:
    if path.is_symlink() or not path.is_file():
        raise ValueError("collector health file is unavailable")
    return json.loads(path.read_text(encoding="utf-8"))


def readiness_exit_code(
    path: Path,
    *,
    expected_schema_version: int,
    maximum_age_seconds: int,
) -> int:
    try:
        payload = load_health_file(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return 1
    return (
        0
        if health_payload_is_ready(
            payload,
            expected_schema_version=expected_schema_version,
            maximum_age_seconds=maximum_age_seconds,
        )
        else 1
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--health-file", type=Path, required=True)
    parser.add_argument("--schema-version", type=int, choices=(1, 2), required=True)
    parser.add_argument("--max-age-seconds", type=int, required=True)
    arguments = parser.parse_args()
    return readiness_exit_code(
        arguments.health_file,
        expected_schema_version=arguments.schema_version,
        maximum_age_seconds=arguments.max_age_seconds,
    )


if __name__ == "__main__":
    raise SystemExit(main())
