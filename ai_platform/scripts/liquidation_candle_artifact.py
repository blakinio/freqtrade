from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai_platform.research.liquidations.datasets.candle_artifact import (
    CandleArtifactError,
    build_artifact,
    load_request,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    REPO_ROOT
    / "ai_platform/research/liquidations/datasets/liquid20-candle-artifact-contract-v1.json"
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build immutable Liquid20 candle evidence")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--code-commit")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.validate_only:
            request = load_request(
                args.contract.resolve(),
                args.request.resolve(),
                repo_root=REPO_ROOT,
            )
            print(
                json.dumps(
                    {
                        "request_id": request.request_id,
                        "sources": [source.source for source in request.sources],
                        "symbols": [symbol for symbol, _ in request.pair_mapping],
                        "start_ms": request.start_ms,
                        "end_ms": request.end_ms,
                        "performance_research_authorized": (
                            request.performance_research_authorized
                        ),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.output_root is None or args.code_commit is None:
            raise CandleArtifactError(
                "--output-root and --code-commit are required unless --validate-only is used"
            )
        manifest = build_artifact(
            contract_path=args.contract.resolve(),
            request_path=args.request.resolve(),
            output_root=args.output_root.resolve(),
            repo_root=REPO_ROOT,
            code_commit=args.code_commit,
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    except CandleArtifactError as exc:
        print(f"Liquid20 candle artifact failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
