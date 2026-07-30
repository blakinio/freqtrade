#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def main() -> int:
    root = Path(os.environ.get("MARKET_EVIDENCE_DURABLE_ROOT", ""))
    path = root / "collector-health.json"
    try:
        if not root.is_absolute() or path.is_symlink() or not path.is_file():
            return 1
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("healthy") is not True:
            return 1
        observed_at_ms = payload.get("observed_at_ms")
        if not isinstance(observed_at_ms, int):
            return 1
        maximum_age_seconds = int(os.environ.get("MARKET_EVIDENCE_HEALTH_MAX_AGE_SECONDS", "600"))
        if maximum_age_seconds < 1:
            return 1
        age_ms = time.time_ns() // 1_000_000 - observed_at_ms
        return 0 if 0 <= age_ms <= maximum_age_seconds * 1000 else 1
    except (OSError, ValueError, json.JSONDecodeError):
        return 1


if __name__ == "__main__":
    sys.exit(main())
