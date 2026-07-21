#!/usr/bin/env python3
"""Validate bounded historical-execution prerequisites for experimental PyTorch and RL tracks."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ai_platform.scripts.experimental_model_research_contract import (
    validate_experimental_model_research_foundation,
)
from ai_platform.scripts.run_experiment import (
    build_backtest_command,
    build_download_command,
    load_manifest,
    validate_research_config,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TRACKS = {"pytorch-research-v1", "rl-research-v1"}
SEMANTIC_DOWNLOAD_WINDOW = "20250801-20260630"
SEMANTIC_PREDICTION_WINDOW = "20260301-20260630"
EXECUTION_DOWNLOAD_TIMERANGE = "20250801-20260701"
EXECUTION_PREDICTION_TIMERANGE = "20260301-20260701"
EXPECTED_HISTORICAL_OOS = "20260501-20260630"
EXPECTED_FINAL_HOLDOUT = "20260801-20260930"
EXPECTED_EXCHANGE = "kraken"
EXPECTED_PAIRS = ["BTC/USDT", "ETH/USDT"]
EXPECTED_TIMEFRAMES = ["15m", "1h", "4h"]
EXPECTED_FEE = 0.002
TIMEFRAME_SECONDS = {"15m": 15 * 60, "1h": 60 * 60, "4h": 4 * 60 * 60}


class ExperimentalHistoricalPreflightError(RuntimeError):
    """Raised when experimental historical-execution prerequisites drift or are incomplete."""


def _resolve_repo_path(value: str) -> Path:
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ExperimentalHistoricalPreflightError(
            f"Repository-relative path escapes root: {value}"
        ) from exc
    return path


def _date_token(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d").replace(tzinfo=UTC)


def _split_timerange(value: str) -> tuple[str, str]:
    try:
        start, stop = value.split("-", maxsplit=1)
    except ValueError as exc:
        raise ExperimentalHistoricalPreflightError(
            f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}"
        ) from exc
    if len(start) != 8 or len(stop) != 8:
        raise ExperimentalHistoricalPreflightError(
            f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}"
        )
    return start, stop


def _validate_exclusive_execution_boundary(
    semantic_window: str,
    execution_timerange: str,
    *,
    label: str,
) -> None:
    semantic_start, semantic_end_inclusive = _split_timerange(semantic_window)
    execution_start, execution_end_exclusive = _split_timerange(execution_timerange)
    if execution_start != semantic_start:
        raise ExperimentalHistoricalPreflightError(f"{label} execution start drifted")
    expected_stop = (_date_token(semantic_end_inclusive) + timedelta(days=1)).strftime("%Y%m%d")
    if execution_end_exclusive != expected_stop:
        raise ExperimentalHistoricalPreflightError(
            f"{label} must encode the inclusive semantic end as exclusive stop {expected_stop}"
        )


def _canonical_inputs() -> tuple[dict[str, Any], list[dict[str, Any]]]:  # noqa: C901
    foundation = validate_experimental_model_research_foundation()
    if foundation["protected_final_holdout"] != {
        "declaration": "ai_platform/validation/final-holdout-v2-declaration.json",
        "timerange": EXPECTED_FINAL_HOLDOUT,
        "used": False,
        "usage": "forbidden",
    }:
        raise ExperimentalHistoricalPreflightError("Protected final holdout contract drifted")

    geometry = foundation["shared_temporal_geometry"]
    expected_geometry = {
        "historical_oos_window": EXPECTED_HISTORICAL_OOS,
        "prediction_window": SEMANTIC_PREDICTION_WINDOW,
        "download_timerange": SEMANTIC_DOWNLOAD_WINDOW,
        "freqtrade_prediction_timerange": EXECUTION_PREDICTION_TIMERANGE,
        "freqtrade_download_timerange": EXECUTION_DOWNLOAD_TIMERANGE,
    }
    for field, expected_value in expected_geometry.items():
        if geometry.get(field) != expected_value:
            raise ExperimentalHistoricalPreflightError(
                f"Experimental temporal geometry drifted for {field}: expected {expected_value}"
            )

    _validate_exclusive_execution_boundary(
        SEMANTIC_PREDICTION_WINDOW,
        EXECUTION_PREDICTION_TIMERANGE,
        label="Prediction window",
    )
    _validate_exclusive_execution_boundary(
        SEMANTIC_DOWNLOAD_WINDOW,
        EXECUTION_DOWNLOAD_TIMERANGE,
        label="Download window",
    )
    prediction_start, prediction_stop = _split_timerange(EXECUTION_PREDICTION_TIMERANGE)
    prediction_days = (_date_token(prediction_stop) - _date_token(prediction_start)).days
    if prediction_days != 122:
        raise ExperimentalHistoricalPreflightError(
            f"Execution prediction timerange must span 122 days, got {prediction_days}"
        )

    tracks: list[dict[str, Any]] = []
    for track in foundation["tracks"]:
        track_id = track["track_id"]
        if track_id not in EXPECTED_TRACKS:
            raise ExperimentalHistoricalPreflightError(f"Unexpected track identity: {track_id}")
        manifest_path = _resolve_repo_path(track["manifest"])
        manifest = load_manifest(manifest_path)
        config_path = _resolve_repo_path(track["config"])
        config = validate_research_config(config_path)
        exchange = str(config.get("exchange", {}).get("name", "")).lower()
        freqai = config.get("freqai", {})

        expected_manifest = {
            "download_timerange": EXECUTION_DOWNLOAD_TIMERANGE,
            "timerange": EXECUTION_PREDICTION_TIMERANGE,
            "pairs": EXPECTED_PAIRS,
            "timeframes": EXPECTED_TIMEFRAMES,
            "fee": EXPECTED_FEE,
        }
        for field, value in expected_manifest.items():
            if manifest.get(field) != value:
                raise ExperimentalHistoricalPreflightError(
                    f"{track_id} manifest drifted for {field}: expected {value!r}"
                )
        if exchange != EXPECTED_EXCHANGE:
            raise ExperimentalHistoricalPreflightError(
                f"{track_id} exchange drifted: expected {EXPECTED_EXCHANGE}"
            )
        if freqai.get("train_period_days") != 90 or freqai.get("backtest_period_days") != 122:
            raise ExperimentalHistoricalPreflightError(
                f"{track_id} single-training-window geometry drifted"
            )
        if freqai.get("continual_learning", False) is not False:
            raise ExperimentalHistoricalPreflightError(
                f"{track_id} continual learning must remain disabled"
            )

        strategy_path = _resolve_repo_path(manifest["strategy_path"])
        strategy_file = strategy_path / f"{manifest['strategy']}.py"
        model_file = REPO_ROOT / "ai_platform/freqaimodels" / f"{manifest['freqai_model']}.py"
        if not strategy_file.is_file():
            raise ExperimentalHistoricalPreflightError(
                f"Canonical strategy file is missing: {strategy_file}"
            )
        if not model_file.is_file():
            raise ExperimentalHistoricalPreflightError(
                f"Canonical FreqAI model file is missing: {model_file}"
            )

        tracks.append(
            {
                "track_id": track_id,
                "manifest_path": manifest_path,
                "manifest": manifest,
                "config_path": config_path,
                "config": config,
                "strategy_path": strategy_path,
            }
        )

    if {item["track_id"] for item in tracks} != EXPECTED_TRACKS:
        raise ExperimentalHistoricalPreflightError("Canonical experimental track set drifted")
    return foundation, tracks


def build_preflight_report(*, freqtrade_bin: str = "freqtrade") -> dict[str, Any]:
    """Validate contracts and materialize the exact download/backtest command paths only."""
    foundation, tracks = _canonical_inputs()
    first = sorted(tracks, key=lambda item: item["track_id"])[0]
    download_command = build_download_command(
        first["manifest"],
        freqtrade_bin=freqtrade_bin,
        config_path=first["config_path"],
    )
    download_command.extend(["--dl-trades", "--convert"])

    backtest_commands: dict[str, list[str]] = {}
    for item in tracks:
        backtest_commands[item["track_id"]] = build_backtest_command(
            item["manifest"],
            freqtrade_bin=freqtrade_bin,
            config_path=item["config_path"],
            strategy_path=item["strategy_path"],
            run_dir=Path("<runtime-output-dir>") / item["track_id"],
        )

    serialized_commands = json.dumps(
        {"download": download_command, "backtests": backtest_commands}, sort_keys=True
    )
    if EXPECTED_FINAL_HOLDOUT in serialized_commands:
        raise ExperimentalHistoricalPreflightError(
            "Protected final holdout leaked into an execution command"
        )

    return {
        "schema_version": 1,
        "preflight_id": "experimental-model-historical-execution-preflight-v2",
        "status": "contract_ready_data_unverified",
        "exchange": EXPECTED_EXCHANGE,
        "semantic_download_window": SEMANTIC_DOWNLOAD_WINDOW,
        "semantic_prediction_window": SEMANTIC_PREDICTION_WINDOW,
        "execution_download_timerange": EXECUTION_DOWNLOAD_TIMERANGE,
        "execution_prediction_timerange": EXECUTION_PREDICTION_TIMERANGE,
        "freqtrade_stop_semantics": "end_exclusive",
        "historical_oos_window": EXPECTED_HISTORICAL_OOS,
        "protected_final_holdout": EXPECTED_FINAL_HOLDOUT,
        "protected_final_holdout_used": False,
        "phase6_member": False,
        "retuning_allowed": False,
        "promotion_allowed": False,
        "profitability_claim_allowed": False,
        "pairs": EXPECTED_PAIRS,
        "timeframes": EXPECTED_TIMEFRAMES,
        "runtime_dependency_profiles": ["freqai", "freqai_rl"],
        "runner": "ubuntu-24.04",
        "python": "3.12",
        "download_command": download_command,
        "backtest_commands": backtest_commands,
        "canonical_runner": "ai_platform.scripts.run_experiment",
        "strict_oos_extractor": "ai_platform.scripts.experimental_model_oos_result_extractor",
        "foundation_id": foundation["foundation_id"],
    }


def verify_downloaded_data(datadir: Path, *, pairs: list[str] | None = None) -> dict[str, Any]:
    """Verify exact pair/timeframe coverage after the runtime-only Kraken download step."""
    from freqtrade.configuration import TimeRange
    from freqtrade.data.history.history_utils import load_pair_history

    selected_pairs = pairs or EXPECTED_PAIRS
    if not selected_pairs or any(pair not in EXPECTED_PAIRS for pair in selected_pairs):
        raise ExperimentalHistoricalPreflightError("Data verification requested an unknown pair")

    report = build_preflight_report()
    timerange = TimeRange.parse_timerange(EXECUTION_DOWNLOAD_TIMERANGE)
    startdt = timerange.startdt
    stopdt = timerange.stopdt
    if startdt is None or stopdt is None:
        raise ExperimentalHistoricalPreflightError("Expected a bounded download timerange")

    expected_stop = _date_token("20260701")
    if stopdt != expected_stop:
        raise ExperimentalHistoricalPreflightError(
            "Freqtrade parser did not preserve the required exclusive 2026-07-01 stop boundary"
        )

    coverage: dict[str, dict[str, str | int]] = {}
    for pair in selected_pairs:
        for timeframe in EXPECTED_TIMEFRAMES:
            frame = load_pair_history(
                pair=pair,
                timeframe=timeframe,
                datadir=datadir,
                timerange=timerange,
                fill_up_missing=False,
                drop_incomplete=False,
            )
            if frame.empty:
                raise ExperimentalHistoricalPreflightError(
                    f"No downloaded data for {pair} {timeframe}"
                )
            first_date = frame["date"].min().to_pydatetime()
            last_date = frame["date"].max().to_pydatetime()
            if first_date > startdt:
                raise ExperimentalHistoricalPreflightError(
                    "Downloaded data starts too late for "
                    f"{pair} {timeframe}: {first_date.isoformat()}"
                )
            minimum_last_ts = timerange.stopts - TIMEFRAME_SECONDS[timeframe]
            if int(last_date.timestamp()) < minimum_last_ts:
                raise ExperimentalHistoricalPreflightError(
                    "Downloaded data ends too early for "
                    f"{pair} {timeframe}: {last_date.isoformat()}"
                )
            coverage[f"{pair}:{timeframe}"] = {
                "rows": len(frame),
                "first": first_date.isoformat(),
                "last": last_date.isoformat(),
            }

    report["status"] = "ready"
    report["market_data_available"] = True
    report["market_data_directory"] = str(datadir)
    report["verified_pairs"] = selected_pairs
    report["coverage"] = coverage
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("contract", "verify-data"),
        nargs="?",
        default="contract",
    )
    parser.add_argument(
        "--datadir",
        type=Path,
        default=Path("user_data/data/kraken"),
    )
    parser.add_argument(
        "--pair",
        action="append",
        choices=EXPECTED_PAIRS,
        dest="pairs",
        help="Limit data verification to one canonical pair; repeat to verify multiple pairs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.mode == "verify-data":
            result = verify_downloaded_data(args.datadir.resolve(), pairs=args.pairs)
        else:
            result = build_preflight_report(freqtrade_bin=shutil.which("freqtrade") or "freqtrade")
    except (ExperimentalHistoricalPreflightError, RuntimeError) as exc:
        print(f"Experimental historical execution preflight failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
