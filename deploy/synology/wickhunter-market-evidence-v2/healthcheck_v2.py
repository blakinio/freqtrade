#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

from ai_platform.wickhunter.market_evidence_readiness import readiness_exit_code


def main() -> int:
    root = Path(os.environ.get("MARKET_EVIDENCE_V2_DURABLE_ROOT", ""))
    path = root / "collector-health.json"
    if not root.is_absolute():
        return 1
    try:
        maximum_age_seconds = int(
            os.environ.get("MARKET_EVIDENCE_V2_HEALTH_MAX_AGE_SECONDS", "600")
        )
    except ValueError:
        return 1
    return readiness_exit_code(
        path,
        expected_schema_version=2,
        maximum_age_seconds=maximum_age_seconds,
    )


if __name__ == "__main__":
    sys.exit(main())
