from __future__ import annotations

import argparse
import asyncio
import os
import time
from pathlib import Path

from ai_platform.research.liquidations.staging import (
    DEFAULT_BYBIT_TIME_URL,
    probe_bybit_clock,
    trading_credentials_present_in_environment,
    write_json_atomic,
)
from ai_platform.research.liquidations.symbol_universe import (
    DEFAULT_SYMBOL_PROFILE,
    DEFAULT_SYMBOL_UNIVERSE_PATH,
    SymbolProfile,
    load_symbol_profile,
)
from ai_platform.scripts.liquidation_binance_collector import (
    DEFAULT_BINANCE_ENDPOINT,
    DEFAULT_BINANCE_TIME_URL,
    collect_binance_liquidations,
    probe_binance_clock,
    trading_credentials_present as binance_credentials_present,
)
from ai_platform.scripts.liquidation_collector import (
    DEFAULT_BYBIT_ENDPOINT,
    collect_bybit_liquidations,
)


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def _validate_profile_scope(profile: SymbolProfile, *, allow_broad_universe: bool) -> None:
    if (
        len(profile.symbols) > profile.broad_universe_review_threshold
        and not allow_broad_universe
    ):
        raise ValueError(
            "profile exceeds broad_universe_review_threshold; "
            "pass --allow-broad-universe after a separate capacity review"
        )


def _target_paths(output_root: Path) -> dict[str, Path]:
    return {
        "bybit_output": output_root / "bybit-linear.ndjson",
        "bybit_summary": output_root / "bybit-linear-summary.json",
        "binance_output": output_root / "binance-usdm.ndjson",
        "binance_summary": output_root / "binance-usdm-summary.json",
        "manifest": output_root / "multi-source-manifest.json",
    }


def _require_unused_targets(paths: dict[str, Path]) -> None:
    occupied = [str(path) for path in paths.values() if path.exists()]
    if occupied:
        raise FileExistsError(f"multi-source output targets already exist: {occupied}")


async def run_multi_source_collection(
    *,
    profile: SymbolProfile,
    output_root: Path,
    duration_seconds: float | None,
    collector_commit: str,
    require_new_output: bool,
    clock_tolerance_ms: int,
    bybit_endpoint: str = DEFAULT_BYBIT_ENDPOINT,
    bybit_time_url: str = DEFAULT_BYBIT_TIME_URL,
    binance_endpoint: str = DEFAULT_BINANCE_ENDPOINT,
    binance_time_url: str = DEFAULT_BINANCE_TIME_URL,
) -> dict[str, object]:
    paths = _target_paths(output_root)
    if require_new_output:
        _require_unused_targets(paths)
    output_root.mkdir(parents=True, exist_ok=True)

    generic_credentials_present = trading_credentials_present_in_environment()
    any_binance_credentials_present = binance_credentials_present()
    if generic_credentials_present or any_binance_credentials_present:
        raise RuntimeError("trading credentials are present; data-only runner refuses to start")

    started_at_ms = time.time_ns() // 1_000_000
    bybit_clock, binance_clock = await asyncio.gather(
        asyncio.to_thread(
            probe_bybit_clock,
            server_time_url=bybit_time_url,
            tolerance_ms=clock_tolerance_ms,
        ),
        asyncio.to_thread(
            probe_binance_clock,
            server_time_url=binance_time_url,
            tolerance_ms=clock_tolerance_ms,
        ),
    )

    bybit_stats, binance_stats = await asyncio.gather(
        collect_bybit_liquidations(
            endpoint=bybit_endpoint,
            symbols=profile.symbols,
            output_path=paths["bybit_output"],
            duration_seconds=duration_seconds,
            summary_path=paths["bybit_summary"],
            collector_commit=collector_commit,
            require_new_output=require_new_output,
            clock_probe=bybit_clock,
            trading_credentials_present=False,
        ),
        collect_binance_liquidations(
            endpoint=binance_endpoint,
            symbols=profile.symbols,
            output_path=paths["binance_output"],
            duration_seconds=duration_seconds,
            summary_path=paths["binance_summary"],
            collector_commit=collector_commit,
            require_new_output=require_new_output,
            clock_probe=binance_clock,
            credentials_present=False,
        ),
    )
    ended_at_ms = time.time_ns() // 1_000_000

    manifest: dict[str, object] = {
        "schema_version": 1,
        "manifest_type": "liquidation_multi_source_collection",
        "execution_enabled": False,
        "trading_credentials_present": False,
        "collector_commit": collector_commit,
        "started_at_ms": started_at_ms,
        "ended_at_ms": ended_at_ms,
        "duration_ms": ended_at_ms - started_at_ms,
        "symbol_profile": {
            "name": profile.name,
            "frozen_at": profile.frozen_at,
            "selection_basis": profile.selection_basis,
            "symbol_count": len(profile.symbols),
            "symbols": list(profile.symbols),
        },
        "sources": {
            "bybit-linear": {
                "endpoint": bybit_endpoint,
                "clock_probe": bybit_clock.as_json_dict(),
                "output": paths["bybit_output"].name,
                "summary": paths["bybit_summary"].name,
                "stats": bybit_stats.as_json_dict(),
            },
            "binance-usdm": {
                "endpoint": binance_endpoint,
                "clock_probe": binance_clock.as_json_dict(),
                "output": paths["binance_output"].name,
                "summary": paths["binance_summary"].name,
                "stats": binance_stats.as_json_dict(),
            },
        },
        "cross_source_policy": {
            "deduplicate_between_exchanges": False,
            "sum_events_without_source_labels": False,
        },
    }
    await asyncio.to_thread(write_json_atomic, paths["manifest"], manifest)
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Bybit and Binance liquidation events for one frozen symbol profile.",
    )
    parser.add_argument("--profile", default=DEFAULT_SYMBOL_PROFILE)
    parser.add_argument(
        "--universe-file",
        type=Path,
        default=DEFAULT_SYMBOL_UNIVERSE_PATH,
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--duration-seconds", type=_positive_float)
    parser.add_argument(
        "--collector-commit",
        default=os.environ.get("GITHUB_SHA", "unknown"),
    )
    parser.add_argument("--require-new-output", action="store_true")
    parser.add_argument("--allow-broad-universe", action="store_true")
    parser.add_argument("--clock-tolerance-ms", type=_non_negative_int, default=2_000)
    parser.add_argument("--bybit-endpoint", default=DEFAULT_BYBIT_ENDPOINT)
    parser.add_argument("--bybit-time-url", default=DEFAULT_BYBIT_TIME_URL)
    parser.add_argument("--binance-endpoint", default=DEFAULT_BINANCE_ENDPOINT)
    parser.add_argument("--binance-time-url", default=DEFAULT_BINANCE_TIME_URL)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    profile = load_symbol_profile(args.profile, universe_path=args.universe_file)
    _validate_profile_scope(profile, allow_broad_universe=args.allow_broad_universe)
    asyncio.run(
        run_multi_source_collection(
            profile=profile,
            output_root=args.output_root,
            duration_seconds=args.duration_seconds,
            collector_commit=args.collector_commit,
            require_new_output=args.require_new_output,
            clock_tolerance_ms=args.clock_tolerance_ms,
            bybit_endpoint=args.bybit_endpoint,
            bybit_time_url=args.bybit_time_url,
            binance_endpoint=args.binance_endpoint,
            binance_time_url=args.binance_time_url,
        )
    )


if __name__ == "__main__":
    main()
