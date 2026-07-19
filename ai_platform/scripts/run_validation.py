#!/usr/bin/env python3
"""Run walk-forward, holdout, lookahead, and recursive validation for an experiment."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

from ai_platform.scripts.run_experiment import (
    REPO_ROOT,
    ExperimentError,
    build_backtest_command,
    extract_backtest_metrics,
    find_backtest_archive,
    load_manifest,
    run_logged,
    validate_research_config,
    write_json,
)


TIMERANGE_PATTERN = re.compile(r"^[0-9]{8}-[0-9]{8}$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
PERCENT_PATTERN = re.compile(r"^([+-]?\d+(?:\.\d+)?)%$")
REQUIRED_PLAN_FIELDS = {
    "schema_version",
    "validation_id",
    "experiment_manifest",
    "walk_forward_folds",
    "holdout",
    "gates",
    "lookahead",
    "recursive",
    "output_root",
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso_utc(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _resolve_repo_path(value: str) -> Path:
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ExperimentError(f"Path escapes repository root: {value}") from exc
    return candidate


def load_validation_plan(path: Path) -> dict[str, Any]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"Unable to read validation plan {path}: {exc}") from exc

    missing = sorted(REQUIRED_PLAN_FIELDS - plan.keys())
    if missing:
        raise ExperimentError(f"Validation plan is missing fields: {', '.join(missing)}")
    if plan["schema_version"] != 1:
        raise ExperimentError("Only validation schema_version 1 is supported")
    if not isinstance(plan["validation_id"], str) or not ID_PATTERN.fullmatch(
        plan["validation_id"]
    ):
        raise ExperimentError("validation_id contains unsupported characters")
    if len(plan["walk_forward_folds"]) < 2:
        raise ExperimentError("At least two walk-forward folds are required")

    names: set[str] = set()
    for window in [*plan["walk_forward_folds"], plan["holdout"]]:
        if not isinstance(window, dict):
            raise ExperimentError("Validation windows must be objects")
        name = window.get("name")
        timerange = window.get("timerange")
        if not isinstance(name, str) or not ID_PATTERN.fullmatch(name):
            raise ExperimentError("Validation window name contains unsupported characters")
        if name in names:
            raise ExperimentError(f"Duplicate validation window name: {name}")
        names.add(name)
        if not isinstance(timerange, str) or not TIMERANGE_PATTERN.fullmatch(timerange):
            raise ExperimentError(f"Invalid timerange for validation window {name}")

    return plan


def _derived_config(
    base_config: dict[str, Any],
    *,
    validation_id: str,
    window_name: str,
    run_token: str,
) -> dict[str, Any]:
    config = json.loads(json.dumps(base_config))
    freqai = config.setdefault("freqai", {})
    original_identifier = str(freqai.get("identifier", "ai-platform"))
    suffix = f"{validation_id}-{window_name}-{run_token}"
    freqai["identifier"] = f"{original_identifier}-{suffix}"[:240]
    return config


def _metric_number(metrics: dict[str, Any], key: str) -> float:
    value = metrics.get(key)
    if not isinstance(value, (int, float)):
        raise ExperimentError(f"Backtest metric {key!r} is missing or non-numeric")
    return float(value)


def summarize_backtest_metrics(metrics: dict[str, Any]) -> dict[str, float | int]:
    trades = metrics.get("total_trades", metrics.get("trade_count"))
    if not isinstance(trades, int):
        raise ExperimentError("Backtest result does not contain an integer trade count")
    return {
        "trades": trades,
        "profit": _metric_number(metrics, "profit_total"),
        "drawdown": _metric_number(metrics, "max_drawdown_account"),
    }


def build_lookahead_command(
    manifest: dict[str, Any],
    plan: dict[str, Any],
    *,
    freqtrade_bin: str,
    config_path: Path,
    strategy_path: Path,
    csv_path: Path,
) -> list[str]:
    options = plan["lookahead"]
    return [
        freqtrade_bin,
        "lookahead-analysis",
        "--config",
        str(config_path),
        "--strategy",
        manifest["strategy"],
        "--strategy-path",
        str(strategy_path),
        "--freqaimodel",
        manifest["freqai_model"],
        "--timerange",
        manifest["timerange"],
        "--fee",
        str(manifest["fee"]),
        "--pairs",
        *manifest["pairs"],
        "--minimum-trade-amount",
        str(options["minimum_trade_amount"]),
        "--targeted-trade-amount",
        str(options["targeted_trade_amount"]),
        "--lookahead-analysis-exportfilename",
        str(csv_path),
        "--no-color",
    ]


def parse_lookahead_csv(path: Path, strategy: str) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise ExperimentError(f"Unable to read lookahead CSV {path}: {exc}") from exc

    row = next((item for item in rows if item.get("strategy") == strategy), None)
    if row is None:
        raise ExperimentError(f"Lookahead result for {strategy} was not exported")

    indicators = [
        value.strip() for value in (row.get("biased_indicators") or "").split(",") if value.strip()
    ]
    effective_indicators = [value for value in indicators if not value.startswith("&")]
    biased_entries = int(row.get("biased_entry_signals") or 0)
    biased_exits = int(row.get("biased_exit_signals") or 0)
    passed = biased_entries == 0 and biased_exits == 0 and not effective_indicators

    return {
        "passed": passed,
        "reported_has_bias": (row.get("has_bias") or "").lower() in {"true", "yes", "1"},
        "total_signals": int(row.get("total_signals") or 0),
        "biased_entry_signals": biased_entries,
        "biased_exit_signals": biased_exits,
        "biased_indicators": indicators,
        "effective_biased_indicators": effective_indicators,
        "ignored_freqai_targets": [value for value in indicators if value.startswith("&")],
    }


def build_recursive_command(
    manifest: dict[str, Any],
    plan: dict[str, Any],
    config: dict[str, Any],
    *,
    freqtrade_bin: str,
    config_path: Path,
    strategy_path: Path,
) -> list[str]:
    options = plan["recursive"]
    timeframe = str(config.get("timeframe") or manifest["timeframes"][0])
    return [
        freqtrade_bin,
        "recursive-analysis",
        "--config",
        str(config_path),
        "--strategy",
        manifest["strategy"],
        "--strategy-path",
        str(strategy_path),
        "--freqaimodel",
        manifest["freqai_model"],
        "--timeframe",
        timeframe,
        "--timerange",
        options["timerange"],
        "--pairs",
        options["pair"],
        "--startup-candle",
        *[str(value) for value in options["startup_candles"]],
        "--no-color",
    ]


def parse_recursive_max_abs_variance(log_text: str) -> float:
    values: list[float] = []
    for line in log_text.splitlines():
        separator = "│" if "│" in line else "|" if "|" in line else None
        if separator is None:
            continue
        cells = [cell.strip() for cell in line.split(separator) if cell.strip()]
        if len(cells) < 2:
            continue
        indicator = cells[0]
        if indicator.lower().startswith("indicator") or indicator.startswith("&"):
            continue
        for cell in cells[1:]:
            match = PERCENT_PATTERN.fullmatch(cell)
            if match:
                values.append(abs(float(match.group(1))) / 100.0)

    if not values:
        raise ExperimentError("No numeric recursive-analysis variance values found in output")
    return max(values)


def _evaluate_gate(name: str, actual: Any, expected: str, passed: bool) -> dict[str, Any]:
    return {
        "name": name,
        "actual": actual,
        "expected": expected,
        "passed": passed,
    }


def evaluate_performance_gates(
    fold_summaries: list[dict[str, Any]],
    holdout_summary: dict[str, Any],
    gates: dict[str, Any],
) -> list[dict[str, Any]]:
    total_trades = sum(int(item["trades"]) for item in fold_summaries)
    profitable_folds = sum(float(item["profit"]) > 0 for item in fold_summaries)
    mean_fold_profit = mean(float(item["profit"]) for item in fold_summaries)
    max_fold_drawdown = max(float(item["drawdown"]) for item in fold_summaries)

    return [
        _evaluate_gate(
            "minimum_total_walk_forward_trades",
            total_trades,
            f">= {gates['minimum_total_trades']}",
            total_trades >= gates["minimum_total_trades"],
        ),
        _evaluate_gate(
            "minimum_profitable_folds",
            profitable_folds,
            f">= {gates['minimum_profitable_folds']}",
            profitable_folds >= gates["minimum_profitable_folds"],
        ),
        _evaluate_gate(
            "maximum_fold_drawdown",
            max_fold_drawdown,
            f"<= {gates['maximum_fold_drawdown']}",
            max_fold_drawdown <= gates["maximum_fold_drawdown"],
        ),
        _evaluate_gate(
            "minimum_mean_fold_profit",
            mean_fold_profit,
            f">= {gates['minimum_mean_fold_profit']}",
            mean_fold_profit >= gates["minimum_mean_fold_profit"],
        ),
        _evaluate_gate(
            "minimum_holdout_trades",
            holdout_summary["trades"],
            f">= {gates['minimum_holdout_trades']}",
            holdout_summary["trades"] >= gates["minimum_holdout_trades"],
        ),
        _evaluate_gate(
            "minimum_holdout_profit",
            holdout_summary["profit"],
            f">= {gates['minimum_holdout_profit']}",
            holdout_summary["profit"] >= gates["minimum_holdout_profit"],
        ),
        _evaluate_gate(
            "maximum_holdout_drawdown",
            holdout_summary["drawdown"],
            f"<= {gates['maximum_holdout_drawdown']}",
            holdout_summary["drawdown"] <= gates["maximum_holdout_drawdown"],
        ),
    ]


def _run_backtest_window(
    manifest: dict[str, Any],
    base_config: dict[str, Any],
    *,
    plan: dict[str, Any],
    window: dict[str, str],
    run_dir: Path,
    freqtrade_bin: str,
    strategy_path: Path,
    run_token: str,
) -> dict[str, Any]:
    window_dir = run_dir / "windows" / window["name"]
    window_dir.mkdir(parents=True, exist_ok=False)
    config = _derived_config(
        base_config,
        validation_id=plan["validation_id"],
        window_name=window["name"],
        run_token=run_token,
    )
    config_path = window_dir / "config.json"
    write_json(config_path, config)

    window_manifest = dict(manifest)
    window_manifest["timerange"] = window["timerange"]
    command = build_backtest_command(
        window_manifest,
        freqtrade_bin=freqtrade_bin,
        config_path=config_path,
        strategy_path=strategy_path,
        run_dir=window_dir,
    )
    run_logged(command, log_path=window_dir / "backtest.log")
    archive = find_backtest_archive(window_dir)
    metrics = extract_backtest_metrics(archive, manifest["strategy"])
    summary = {
        "name": window["name"],
        "timerange": window["timerange"],
        **summarize_backtest_metrics(metrics),
        "archive": archive.name,
    }
    write_json(window_dir / "window-summary.json", summary)
    return summary


def run_validation(
    plan_path: Path,
    *,
    freqtrade_bin: str,
) -> tuple[Path, bool]:
    plan_path = plan_path.resolve()
    plan = load_validation_plan(plan_path)
    manifest_path = _resolve_repo_path(plan["experiment_manifest"])
    manifest = load_manifest(manifest_path)
    config_path = _resolve_repo_path(manifest["config"])
    strategy_path = _resolve_repo_path(manifest["strategy_path"])
    base_config = validate_research_config(config_path)

    output_root = _resolve_repo_path(plan["output_root"])
    run_token = f"{_utc_now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    run_dir = output_root / plan["validation_id"] / run_token
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(plan_path, run_dir / "validation-plan.json")
    shutil.copy2(manifest_path, run_dir / "experiment-manifest.json")

    started_at = _utc_now()
    fold_summaries = [
        _run_backtest_window(
            manifest,
            base_config,
            plan=plan,
            window=window,
            run_dir=run_dir,
            freqtrade_bin=freqtrade_bin,
            strategy_path=strategy_path,
            run_token=run_token[-8:],
        )
        for window in plan["walk_forward_folds"]
    ]
    holdout_summary = _run_backtest_window(
        manifest,
        base_config,
        plan=plan,
        window=plan["holdout"],
        run_dir=run_dir,
        freqtrade_bin=freqtrade_bin,
        strategy_path=strategy_path,
        run_token=run_token[-8:],
    )

    gates = evaluate_performance_gates(fold_summaries, holdout_summary, plan["gates"])

    lookahead_result: dict[str, Any] | None = None
    if plan["lookahead"]["enabled"]:
        lookahead_csv = run_dir / "lookahead.csv"
        command = build_lookahead_command(
            manifest,
            plan,
            freqtrade_bin=freqtrade_bin,
            config_path=config_path,
            strategy_path=strategy_path,
            csv_path=lookahead_csv,
        )
        run_logged(command, log_path=run_dir / "lookahead.log")
        lookahead_result = parse_lookahead_csv(lookahead_csv, manifest["strategy"])
        gates.append(
            _evaluate_gate(
                "lookahead_bias",
                lookahead_result,
                "no effective biased entries, exits, or non-target indicators",
                bool(lookahead_result["passed"]),
            )
        )

    recursive_result: dict[str, Any] | None = None
    if plan["recursive"]["enabled"]:
        recursive_log = run_dir / "recursive.log"
        command = build_recursive_command(
            manifest,
            plan,
            base_config,
            freqtrade_bin=freqtrade_bin,
            config_path=config_path,
            strategy_path=strategy_path,
        )
        run_logged(command, log_path=recursive_log)
        max_variance = parse_recursive_max_abs_variance(recursive_log.read_text(encoding="utf-8"))
        threshold = float(plan["recursive"]["maximum_abs_variance_ratio"])
        recursive_result = {
            "maximum_abs_variance_ratio": max_variance,
            "threshold": threshold,
            "passed": max_variance <= threshold,
        }
        gates.append(
            _evaluate_gate(
                "recursive_variance",
                max_variance,
                f"<= {threshold}",
                max_variance <= threshold,
            )
        )

    passed = all(bool(gate["passed"]) for gate in gates)
    finished_at = _utc_now()
    report = {
        "schema_version": 1,
        "validation_id": plan["validation_id"],
        "experiment_id": manifest["experiment_id"],
        "run_id": run_token,
        "status": "passed" if passed else "failed_gates",
        "promotion_allowed": passed,
        "started_at": _iso_utc(started_at),
        "finished_at": _iso_utc(finished_at),
        "walk_forward": fold_summaries,
        "holdout": holdout_summary,
        "lookahead": lookahead_result,
        "recursive": recursive_result,
        "gates": gates,
    }
    write_json(run_dir / "validation-report.json", report)
    return run_dir, passed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="Path to validation plan JSON")
    parser.add_argument(
        "--freqtrade-bin",
        default="freqtrade",
        help="Freqtrade executable name or path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_dir, passed = run_validation(args.plan, freqtrade_bin=args.freqtrade_bin)
    except ExperimentError as exc:
        print(f"Validation failed to execute: {exc}", file=sys.stderr)
        return 1

    print(run_dir)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
