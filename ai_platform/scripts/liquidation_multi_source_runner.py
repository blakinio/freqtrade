from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.staging import (
    DEFAULT_BYBIT_TIME_URL,
    CollectorRunStats,
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
)
from ai_platform.scripts.liquidation_binance_collector import (
    trading_credentials_present as binance_credentials_present,
)
from ai_platform.scripts.liquidation_collector import (
    DEFAULT_BYBIT_ENDPOINT,
    collect_bybit_liquidations,
)


SOURCE_SEMANTICS: dict[str, dict[str, object]] = {
    "bybit-linear": {
        "stream": "allLiquidation",
        "coverage": "all liquidation events published by the exchange",
        "documented_push_frequency_ms": 500,
    },
    "binance-usdm": {
        "stream": "forceOrder",
        "coverage": "latest liquidation order per symbol within each 1000 ms window",
        "documented_push_frequency_ms": 1000,
    },
}


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
    if len(profile.symbols) > profile.broad_universe_review_threshold and not allow_broad_universe:
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


def _require_unused_targets(paths: Mapping[str, Path]) -> None:
    occupied = [str(path) for path in paths.values() if path.exists()]
    if occupied:
        raise FileExistsError(f"multi-source output targets already exist: {occupied}")


def _prepare_output_root(
    output_root: Path,
    paths: Mapping[str, Path],
    *,
    require_new_output: bool,
) -> None:
    if require_new_output:
        _require_unused_targets(paths)
    output_root.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"JSON payload must be an object: {path}")
    return payload


def _normalize_summary(
    summary_path: Path,
    *,
    source_id: str,
    endpoint: str,
    symbols: Sequence[str],
) -> None:
    summary = _load_json(summary_path)
    summary["source"] = {
        "id": source_id,
        "endpoint": endpoint,
        "symbols": list(symbols),
    }
    summary["source_semantics"] = SOURCE_SEMANTICS[source_id]
    write_json_atomic(summary_path, summary)


def _exception_text(error: BaseException) -> str:
    message = f"{type(error).__name__}: {error}"
    return message[:500]


def _source_manifest(
    *,
    endpoint: str,
    output_path: Path,
    summary_path: Path,
    start_clock: Mapping[str, object],
    end_clock: Mapping[str, object],
    result: CollectorRunStats | BaseException,
    normalization_result: None | BaseException,
    source_id: str,
) -> dict[str, object]:
    errors = [
        error
        for error in (result if isinstance(result, BaseException) else None, normalization_result)
        if isinstance(error, BaseException)
    ]
    stats: Mapping[str, object] | None = None
    if isinstance(result, CollectorRunStats):
        stats = result.as_json_dict()
    elif summary_path.exists():
        summary = _load_json(summary_path)
        raw_stats = summary.get("stats")
        if isinstance(raw_stats, dict):
            stats = raw_stats
    return {
        "endpoint": endpoint,
        "source_semantics": SOURCE_SEMANTICS[source_id],
        "output": output_path.name,
        "summary": summary_path.name,
        "collector_status": "failed" if errors else "completed",
        "collector_error": "; ".join(_exception_text(error) for error in errors) or None,
        "clock_probes": {
            "start": dict(start_clock),
            "end": dict(end_clock),
        },
        "stats": stats,
    }


async def run_multi_source_collection(
    *,
    profile: SymbolProfile,
    output_root: Path,
    duration_seconds: float | None,
    collector_commit: str,
    require_new_output: bool,
    clock_tolerance_ms: int,
    run_id: str = "unspecified",
    host_id: str = "unspecified",
    bybit_endpoint: str = DEFAULT_BYBIT_ENDPOINT,
    bybit_time_url: str = DEFAULT_BYBIT_TIME_URL,
    binance_endpoint: str = DEFAULT_BINANCE_ENDPOINT,
    binance_time_url: str = DEFAULT_BINANCE_TIME_URL,
) -> dict[str, object]:
    paths = _target_paths(output_root)
    await asyncio.to_thread(
        _prepare_output_root,
        output_root,
        paths,
        require_new_output=require_new_output,
    )

    generic_credentials_present = trading_credentials_present_in_environment()
    any_binance_credentials_present = binance_credentials_present()
    if generic_credentials_present or any_binance_credentials_present:
        raise RuntimeError("trading credentials are present; data-only runner refuses to start")

    started_at_ms = time.time_ns() // 1_000_000
    bybit_clock_start, binance_clock_start = await asyncio.gather(
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

    bybit_result, binance_result = await asyncio.gather(
        collect_bybit_liquidations(
            endpoint=bybit_endpoint,
            symbols=profile.symbols,
            output_path=paths["bybit_output"],
            duration_seconds=duration_seconds,
            summary_path=paths["bybit_summary"],
            collector_commit=collector_commit,
            require_new_output=require_new_output,
            clock_probe=bybit_clock_start,
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
            clock_probe=binance_clock_start,
            credentials_present=False,
        ),
        return_exceptions=True,
    )

    bybit_normalization, binance_normalization = await asyncio.gather(
        asyncio.to_thread(
            _normalize_summary,
            paths["bybit_summary"],
            source_id="bybit-linear",
            endpoint=bybit_endpoint,
            symbols=profile.symbols,
        ),
        asyncio.to_thread(
            _normalize_summary,
            paths["binance_summary"],
            source_id="binance-usdm",
            endpoint=binance_endpoint,
            symbols=profile.symbols,
        ),
        return_exceptions=True,
    )

    bybit_clock_end, binance_clock_end = await asyncio.gather(
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
    ended_at_ms = time.time_ns() // 1_000_000

    bybit_source = _source_manifest(
        endpoint=bybit_endpoint,
        output_path=paths["bybit_output"],
        summary_path=paths["bybit_summary"],
        start_clock=bybit_clock_start.as_json_dict(),
        end_clock=bybit_clock_end.as_json_dict(),
        result=bybit_result,
        normalization_result=bybit_normalization,
        source_id="bybit-linear",
    )
    binance_source = _source_manifest(
        endpoint=binance_endpoint,
        output_path=paths["binance_output"],
        summary_path=paths["binance_summary"],
        start_clock=binance_clock_start.as_json_dict(),
        end_clock=binance_clock_end.as_json_dict(),
        result=binance_result,
        normalization_result=binance_normalization,
        source_id="binance-usdm",
    )
    failed_sources = [
        source_id
        for source_id, source in (
            ("bybit-linear", bybit_source),
            ("binance-usdm", binance_source),
        )
        if source["collector_status"] != "completed"
    ]
    manifest: dict[str, object] = {
        "schema_version": 1,
        "manifest_type": "liquidation_multi_source_collection",
        "run_status": "failed" if failed_sources else "completed",
        "run_id": run_id,
        "host_id": host_id,
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
            "bybit-linear": bybit_source,
            "binance-usdm": binance_source,
        },
        "cross_source_policy": {
            "deduplicate_between_exchanges": False,
            "sum_events_without_source_labels": False,
        },
    }
    await asyncio.to_thread(write_json_atomic, paths["manifest"], manifest)
    if failed_sources:
        raise RuntimeError(f"multi-source collection failed: {', '.join(failed_sources)}")
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
    parser.add_argument("--run-id")
    parser.add_argument(
        "--host-id",
        default=os.environ.get("LIQUIDATION_STAGING_HOST_ID", "unspecified"),
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
            run_id=args.run_id or args.output_root.name,
            host_id=args.host_id,
            bybit_endpoint=args.bybit_endpoint,
            bybit_time_url=args.bybit_time_url,
            binance_endpoint=args.binance_endpoint,
            binance_time_url=args.binance_time_url,
        )
    )


if __name__ == "__main__":
    main()
