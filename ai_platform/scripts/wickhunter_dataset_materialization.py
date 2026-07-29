from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ai_platform.wickhunter.canonical import canonical_json
from ai_platform.wickhunter.materialization import (
    load_materialization_request,
    materialize_wickhunter_dataset_package,
    preflight_materialization_package,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preflight or materialize an immutable WickHunter WH-01 dataset package."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("preflight", "materialize"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--package-root", type=Path, required=True)
        subparser.add_argument("--request", type=Path, required=True)
        if command == "materialize":
            subparser.add_argument("--output-root", type=Path, required=True)
    return parser


def _error_payload(exc: Exception) -> dict[str, object]:
    return {
        "schema_version": "wickhunter-dataset-materialization-report-v1",
        "report_type": "error",
        "status": "error",
        "error_type": type(exc).__name__,
        "error": str(exc),
        "trading_authorized": False,
        "model_execution_authorized": False,
        "live_capital_authorized": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        request = load_materialization_request(args.request)
        if args.command == "preflight":
            report = preflight_materialization_package(
                package_root=args.package_root,
                request=request,
            )
            print(canonical_json(report.as_json_dict()))
            return 0 if report.status == "ready" else 2
        result = materialize_wickhunter_dataset_package(
            package_root=args.package_root,
            request=request,
            output_root=args.output_root,
        )
        print(canonical_json(result.as_json_dict()))
        return 0
    except Exception as exc:
        print(json.dumps(_error_payload(exc), separators=(",", ":"), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
