from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from ai_platform.wickhunter.canonical import canonical_sha256


HEALTH_SCHEMA_VERSION = "wickhunter-paper-runtime-operator-health-v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DRIFT_STATES = {"healthy", "drifted", "unknown"}
RUNTIME_HEALTH_STATES = {"healthy", "degraded", "fail_closed"}
ZERO_AUTHORITY = {
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"{field} must be an integer")
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{field} must be positive")
    return parsed


def _load(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("health file must be a regular file")
    if path.stat().st_size <= 0 or path.stat().st_size > 64 * 1024:
        raise ValueError("health file size is invalid")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("health file must contain an object")
    return payload


def main() -> int:  # noqa: C901
    try:
        path = Path(os.environ.get("HEALTH_PATH", "/runtime/operator/health.json"))
        if not path.is_absolute():
            return _fail("health path must be absolute")
        payload = _load(path)
        claimed_hash = payload.pop("health_sha256", None)
        if not isinstance(claimed_hash, str) or not SHA256_RE.fullmatch(claimed_hash):
            return _fail("health hash is invalid")
        if canonical_sha256(payload) != claimed_hash:
            return _fail("health self-hash mismatch")
        if payload.get("schema_version") != HEALTH_SCHEMA_VERSION:
            return _fail("health schema mismatch")
        if payload.get("status") != "healthy":
            return _fail("operator is fail-closed")
        expected_commit = os.environ.get("OPERATOR_COMMIT", "")
        if not GIT_SHA_RE.fullmatch(expected_commit):
            return _fail("expected operator commit is invalid")
        if payload.get("operator_commit") != expected_commit:
            return _fail("operator commit mismatch")
        if any(payload.get(name) != expected for name, expected in ZERO_AUTHORITY.items()):
            return _fail("health claims forbidden authority")
        runtime_health = payload.get("runtime_health")
        if runtime_health not in RUNTIME_HEALTH_STATES:
            return _fail("runtime health is invalid")
        if runtime_health != "healthy":
            return _fail("runtime health is not healthy")
        if payload.get("model_drift") not in DRIFT_STATES:
            return _fail("model drift state is invalid")
        if payload.get("data_drift") not in DRIFT_STATES:
            return _fail("data drift state is invalid")
        breaker_reasons = payload.get("circuit_breaker_reasons")
        if not isinstance(breaker_reasons, list):
            return _fail("circuit breaker reasons are invalid")
        if breaker_reasons != sorted(set(str(item) for item in breaker_reasons)):
            return _fail("circuit breaker reasons are not canonical")
        if payload.get("circuit_breaker_active") is not bool(breaker_reasons):
            return _fail("circuit breaker state is inconsistent")
        snapshot_id = payload.get("liquid20_snapshot_id")
        if not isinstance(snapshot_id, str) or not SHA256_RE.fullmatch(snapshot_id):
            return _fail("Liquid20 snapshot identity is invalid")
        checked_at_ms = _integer(payload.get("checked_at_ms"), field="checked_at_ms")
        last_success_at_ms = _integer(payload.get("last_success_at_ms"), field="last_success_at_ms")
        last_observed_at_ms = _integer(
            payload.get("last_observed_at_ms"), field="last_observed_at_ms"
        )
        now_ms = time.time_ns() // 1_000_000
        maximum_age_ms = (
            _integer(
                os.environ.get("HEALTH_MAX_AGE_SECONDS", "1200"),
                field="HEALTH_MAX_AGE_SECONDS",
            )
            * 1000
        )
        if maximum_age_ms < 60_000:
            return _fail("health maximum age is too small")
        if any(
            value > now_ms for value in (checked_at_ms, last_success_at_ms, last_observed_at_ms)
        ):
            return _fail("health timestamp is from the future")
        if last_success_at_ms != last_observed_at_ms:
            return _fail("last success and journal observation differ")
        if now_ms - checked_at_ms > maximum_age_ms:
            return _fail("health observation is stale")
        if now_ms - last_success_at_ms > maximum_age_ms:
            return _fail("last successful generation is stale")
        window_start_ms = _integer(payload.get("window_start_ms"), field="window_start_ms")
        window_end_ms = _integer(payload.get("window_end_ms"), field="window_end_ms")
        if not window_start_ms <= checked_at_ms < window_end_ms:
            return _fail("health observation is outside the activation window")
        generation = payload.get("generation")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
            return _fail("journal generation is not positive")
        if not SHA256_RE.fullmatch(str(payload.get("binding_id", ""))):
            return _fail("runtime binding identity is invalid")
        if not SHA256_RE.fullmatch(str(payload.get("run_id", ""))):
            return _fail("activation run identity is invalid")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return _fail(f"healthcheck failed: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
