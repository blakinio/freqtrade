from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_platform.research.liquidations.multi_source_acceptance import (
    DEFAULT_MULTI_SOURCE_ACCEPTANCE_POLICY_PATH,
    MultiSourceAcceptancePolicy,
    evaluate_multi_source_run,
)
from ai_platform.research.liquidations.staging import write_json_atomic


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate one immutable liquidation multi-source run package.",
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument(
        "--policy",
        type=Path,
        default=DEFAULT_MULTI_SOURCE_ACCEPTANCE_POLICY_PATH,
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    policy = MultiSourceAcceptancePolicy.load(args.policy)
    report = evaluate_multi_source_run(args.run_root, policy=policy)
    write_json_atomic(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
