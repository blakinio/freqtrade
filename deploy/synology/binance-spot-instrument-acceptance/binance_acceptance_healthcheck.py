#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
from pathlib import Path


root = Path(
    os.environ.get(
        "BINANCE_ACCEPTANCE_DURABLE_ROOT",
        "/var/lib/freqtrade-staging-state/binance-spot-instrument-acceptance",
    )
)
health_path = root / "binance-v3-persistent-sampler-health.json"
max_age_seconds = int(os.environ.get("BINANCE_ACCEPTANCE_HEALTH_MAX_AGE_SECONDS", "120"))
payload = json.loads(health_path.read_text(encoding="utf-8"))
observed_at_ns = int(payload["observed_at_ns"])
if time.time_ns() - observed_at_ns > max_age_seconds * 1_000_000_000:
    raise SystemExit("persistent sampler health is stale")
if payload.get("healthy") is not True:
    raise SystemExit("persistent sampler is unhealthy")
if payload.get("execution_enabled") is not False:
    raise SystemExit("execution must remain disabled")
if payload.get("production_source_enabled") is not False:
    raise SystemExit("production source must remain disabled")
if payload.get("orders_submitted") != 0:
    raise SystemExit("orders_submitted must remain zero")
result = payload.get("result")
if not isinstance(result, dict) or result.get("status") not in {
    "sampled",
    "not_due",
    "finalized",
}:
    raise SystemExit("persistent sampler result is invalid")
