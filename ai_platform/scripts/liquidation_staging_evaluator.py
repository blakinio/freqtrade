from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.staging import (
    StagingPolicy,
    evaluate_staging_summary,
    write_json_atomic,
)


def _load_summary(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError("summary must be a JSON object")
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a liquidation data-only collector summary against a frozen policy.",
    )
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--mode", choices=("smoke", "acceptance"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = _load_summary(args.summary)
    policy = StagingPolicy.load(args.policy, mode=args.mode)
    report = evaluate_staging_summary(
        summary,
        policy=policy,
        mode=args.mode,
    )
    write_json_atomic(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
