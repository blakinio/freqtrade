from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from ai_platform.wickhunter.canonical import canonical_sha256


HEALTH_SCHEMA_VERSION = "wickhunter-production-research-runtime-health-v1"
TELEMETRY_SCHEMA_VERSION = "wickhunter-production-research-telemetry-v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
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


def _load(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{field} must be a regular file")
    if path.stat().st_size <= 0 or path.stat().st_size > 512 * 1024:
        raise ValueError(f"{field} size is invalid")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{field} must contain an object")
    return payload


def _verify_hash(payload: dict[str, Any], *, field: str, hash_field: str) -> str:
    claimed = payload.get(hash_field)
    if not isinstance(claimed, str) or SHA256_RE.fullmatch(claimed) is None:
        raise ValueError(f"{field} self-hash is invalid")
    seed = dict(payload)
    seed.pop(hash_field, None)
    if canonical_sha256(seed) != claimed:
        raise ValueError(f"{field} self-hash mismatch")
    return claimed


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"{field} must be an integer")
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{field} must be positive")
    return parsed


def main() -> int:  # noqa: C901
    try:
        health_path = Path(os.environ.get("HEALTH_PATH", "/runtime/operator/health.json"))
        telemetry_path = Path(os.environ.get("TELEMETRY_PATH", "/runtime/journal/telemetry.json"))
        health = _load(health_path, field="health")
        _verify_hash(health, field="health", hash_field="health_sha256")
        if health.get("schema_version") != HEALTH_SCHEMA_VERSION:
            return _fail("health schema mismatch")
        if health.get("status") != "healthy":
            return _fail("research operator is fail-closed")
        if health.get("mode") != "shadow":
            return _fail("research operator mode is not SHADOW")
        if health.get("no_trade_confidence") != "0.60":
            return _fail("no-trade confidence is not frozen at 0.60")
        if health.get("outcome_horizon_ms") != 900_000:
            return _fail("research outcome horizon is not 900 seconds")
        if any(health.get(name) != expected for name, expected in ZERO_AUTHORITY.items()):
            return _fail("health claims forbidden authority")

        expected_commit = os.environ.get("OPERATOR_COMMIT", "")
        if GIT_SHA_RE.fullmatch(expected_commit) is None:
            return _fail("expected operator commit is invalid")
        if health.get("operator_commit") != expected_commit:
            return _fail("operator commit mismatch")
        for env_name, field_name in (
            ("EXPECTED_MODEL_HASH", "model_hash"),
            ("EXPECTED_MODEL_ARTIFACT_SHA256", "model_artifact_sha256"),
            ("EXPECTED_PARAMETER_HASH", "parameter_hash"),
        ):
            expected = os.environ.get(env_name, "")
            if SHA256_RE.fullmatch(expected) is None:
                return _fail(f"{env_name} is invalid")
            if health.get(field_name) != expected:
                return _fail(f"{field_name} mismatch")

        snapshot_id = health.get("liquid20_snapshot_id")
        if not isinstance(snapshot_id, str) or SHA256_RE.fullmatch(snapshot_id) is None:
            return _fail("Liquid20 snapshot identity is invalid")
        if not SHA256_RE.fullmatch(str(health.get("binding_id", ""))):
            return _fail("research binding identity is invalid")
        if not SHA256_RE.fullmatch(str(health.get("run_id", ""))):
            return _fail("research run identity is invalid")

        checked_at_ms = _positive_int(health.get("checked_at_ms"), field="checked_at_ms")
        last_success_at_ms = _positive_int(
            health.get("last_success_at_ms"), field="last_success_at_ms"
        )
        last_observed_at_ms = _positive_int(
            health.get("last_observed_at_ms"), field="last_observed_at_ms"
        )
        if last_success_at_ms != last_observed_at_ms:
            return _fail("last success and runtime observation differ")
        now_ms = time.time_ns() // 1_000_000
        maximum_age_ms = (
            _positive_int(
                os.environ.get("HEALTH_MAX_AGE_SECONDS", "600"),
                field="HEALTH_MAX_AGE_SECONDS",
            )
            * 1000
        )
        if maximum_age_ms < 120_000:
            return _fail("health maximum age is too small")
        if any(
            value > now_ms for value in (checked_at_ms, last_success_at_ms, last_observed_at_ms)
        ):
            return _fail("health timestamp is from the future")
        if now_ms - checked_at_ms > maximum_age_ms:
            return _fail("health observation is stale")
        if now_ms - last_success_at_ms > maximum_age_ms:
            return _fail("last successful generation is stale")
        generation = health.get("generation")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
            return _fail("runtime generation is not positive")

        telemetry = _load(telemetry_path, field="telemetry")
        telemetry_hash = _verify_hash(
            telemetry,
            field="telemetry",
            hash_field="telemetry_sha256",
        )
        if telemetry.get("schema_version") != TELEMETRY_SCHEMA_VERSION:
            return _fail("telemetry schema mismatch")
        if telemetry_hash != health.get("telemetry_sha256"):
            return _fail("health does not bind the current telemetry snapshot")
        if telemetry.get("operator_commit") != expected_commit:
            return _fail("telemetry operator commit mismatch")
        if telemetry.get("run_id") != health.get("run_id"):
            return _fail("telemetry run identity mismatch")
        if telemetry.get("mode") != "shadow":
            return _fail("telemetry mode is not SHADOW")
        if telemetry.get("no_trade_confidence") != "0.60":
            return _fail("telemetry no-trade confidence mismatch")
        if telemetry.get("outcome_horizon_ms") != 900_000:
            return _fail("telemetry outcome horizon mismatch")
        if any(telemetry.get(name) != expected for name, expected in ZERO_AUTHORITY.items()):
            return _fail("telemetry claims forbidden authority")
        telemetry_checked_at_ms = _positive_int(
            telemetry.get("checked_at_ms"), field="telemetry checked_at_ms"
        )
        if telemetry_checked_at_ms != checked_at_ms:
            return _fail("health and telemetry timestamps differ")
        if now_ms - telemetry_checked_at_ms > maximum_age_ms:
            return _fail("telemetry is stale")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return _fail(f"healthcheck failed: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
