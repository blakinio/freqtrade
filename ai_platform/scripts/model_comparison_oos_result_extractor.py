#!/usr/bin/env python3
"""Extract strict Phase 6 OOS metrics from an existing Freqtrade backtest archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from zipfile import BadZipFile, ZipFile

from ai_platform.scripts.model_comparison_contract import load_model_comparison_contract
from ai_platform.scripts.model_comparison_harness import build_materialization
from ai_platform.scripts.model_comparison_metric_semantics import (
    load_model_comparison_metric_semantics,
)
from ai_platform.scripts.oos_trade_boundary_contract import load_oos_trade_boundary_contract
from ai_platform.scripts.run_experiment import load_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMPARISON_CONTRACT = REPO_ROOT / "ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json"
DEFAULT_BOUNDARY_CONTRACT = REPO_ROOT / "ai_platform/model_comparison/oos-trade-boundary-v1.json"
DEFAULT_METRIC_SEMANTICS = REPO_ROOT / "ai_platform/model_comparison/metric-semantics-v1.json"
EXTRACTOR_ID = "freqai-model-comparison-oos-extractor-v1"
CANONICAL_MATERIALIZATION_ROOT = "ai_platform/artifacts/model-comparison/materialized"
MAX_JSON_MEMBER_BYTES = 256 * 1024 * 1024


class ModelComparisonOosExtractorError(RuntimeError):
    """Raised when a backtest archive cannot be scored safely and reproducibly."""


@dataclass(frozen=True)
class ParsedTrade:
    source_index: int
    open_date_original: str
    close_date_original: str
    open_date: datetime
    close_date: datetime
    profit_abs: float
    exit_reason: str


DrawdownCalculator = Callable[[list[ParsedTrade], float], float]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ModelComparisonOosExtractorError(f"Unable to hash archive {path}: {exc}") from exc
    return digest.hexdigest()


def _parse_json_bytes(payload: bytes, label: str) -> dict[str, Any] | None:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    if "strategy" in value and "strategy_comparison" in value:
        return value
    return None


def _load_backtest_stats(archive_path: Path) -> tuple[dict[str, Any], str, str]:
    archive_path = archive_path.resolve()
    archive_sha256 = _sha256(archive_path)
    candidates: list[tuple[str, dict[str, Any]]] = []
    try:
        with ZipFile(archive_path) as archive:
            for member in archive.infolist():
                if member.is_dir() or not member.filename.endswith(".json"):
                    continue
                if member.file_size > MAX_JSON_MEMBER_BYTES:
                    continue
                parsed = _parse_json_bytes(archive.read(member), member.filename)
                if parsed is not None:
                    candidates.append((member.filename, parsed))
    except (OSError, BadZipFile) as exc:
        raise ModelComparisonOosExtractorError(
            f"Unable to read Freqtrade backtest archive {archive_path}: {exc}"
        ) from exc

    if len(candidates) != 1:
        raise ModelComparisonOosExtractorError(
            "Backtest archive must contain exactly one JSON stats member with strategy and "
            "strategy_comparison"
        )
    member_name, stats = candidates[0]
    return stats, member_name, archive_sha256


def _parse_utc_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ModelComparisonOosExtractorError(f"{label} must be a non-empty timestamp string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ModelComparisonOosExtractorError(f"{label} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ModelComparisonOosExtractorError(f"{label} must include an explicit timezone")
    return parsed.astimezone(UTC)


def _parse_trade(trade: Any, source_index: int, required_fields: list[str]) -> ParsedTrade:
    if not isinstance(trade, dict):
        raise ModelComparisonOosExtractorError(f"Trade {source_index} must be a JSON object")
    missing = [field for field in required_fields if field not in trade]
    if missing:
        raise ModelComparisonOosExtractorError(
            f"Trade {source_index} is missing required fields: {', '.join(missing)}"
        )

    open_original = trade["open_date"]
    close_original = trade["close_date"]
    open_date = _parse_utc_timestamp(open_original, f"trade[{source_index}].open_date")
    close_date = _parse_utc_timestamp(close_original, f"trade[{source_index}].close_date")
    if close_date < open_date:
        raise ModelComparisonOosExtractorError(
            f"Trade {source_index} closes before its open timestamp"
        )

    profit_abs = trade["profit_abs"]
    if (
        isinstance(profit_abs, bool)
        or not isinstance(profit_abs, (int, float))
        or not math.isfinite(profit_abs)
    ):
        raise ModelComparisonOosExtractorError(
            f"trade[{source_index}].profit_abs must be a finite number"
        )
    exit_reason = trade["exit_reason"]
    if not isinstance(exit_reason, str) or not exit_reason:
        raise ModelComparisonOosExtractorError(
            f"trade[{source_index}].exit_reason must be a non-empty string"
        )

    return ParsedTrade(
        source_index=source_index,
        open_date_original=open_original,
        close_date_original=close_original,
        open_date=open_date,
        close_date=close_date,
        profit_abs=float(profit_abs),
        exit_reason=exit_reason,
    )


def _canonical_expected_manifest(model_type: str) -> dict[str, Any]:
    materialization = build_materialization(
        DEFAULT_COMPARISON_CONTRACT,
        output_root=CANONICAL_MATERIALIZATION_ROOT,
    )
    for model in materialization["models"]:
        if model["model_type"] == model_type:
            return model["manifest"]
    raise ModelComparisonOosExtractorError(f"Unsupported comparison model: {model_type}")


def _validate_manifest_against_comparison(
    manifest_path: Path,
    comparison: dict[str, Any],
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    model_type = manifest["freqai_model"]
    if model_type not in comparison["models"]:
        raise ModelComparisonOosExtractorError(
            f"Manifest model {model_type} is not part of the pinned comparison"
        )
    expected = _canonical_expected_manifest(model_type)
    shared_fields = (
        "experiment_id",
        "strategy",
        "freqai_model",
        "timerange",
        "download_timerange",
        "pairs",
        "timeframes",
        "fee",
    )
    for field in shared_fields:
        if manifest[field] != expected[field]:
            raise ModelComparisonOosExtractorError(
                f"Manifest field {field} does not match the canonical materialized comparison input"
            )
    return manifest


def _strategy_stats_for_manifest(
    stats: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    strategies = stats.get("strategy")
    if not isinstance(strategies, dict) or set(strategies) != {manifest["strategy"]}:
        raise ModelComparisonOosExtractorError(
            "Backtest archive must contain exactly the manifest strategy result"
        )
    strategy_stats = strategies[manifest["strategy"]]
    if not isinstance(strategy_stats, dict):
        raise ModelComparisonOosExtractorError("Backtest strategy result must be a JSON object")

    expected_identity = {
        "strategy_name": manifest["strategy"],
        "freqaimodel": manifest["freqai_model"],
        "freqai_identifier": manifest["experiment_id"],
        "timerange": manifest["timerange"],
    }
    for field, expected in expected_identity.items():
        if strategy_stats.get(field) != expected:
            raise ModelComparisonOosExtractorError(
                f"Backtest strategy result field {field} does not match the manifest identity"
            )
    return strategy_stats


def _starting_balance(strategy_stats: dict[str, Any]) -> float:
    value = strategy_stats.get("starting_balance")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelComparisonOosExtractorError("starting_balance must be a positive finite number")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ModelComparisonOosExtractorError("starting_balance must be a positive finite number")
    return value


def _trade_evidence(trade: ParsedTrade, *, reasons: list[str] | None = None) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "source_index": trade.source_index,
        "open_date": trade.open_date_original,
        "close_date": trade.close_date_original,
        "profit_abs": trade.profit_abs,
        "exit_reason": trade.exit_reason,
    }
    if reasons:
        evidence["exclusion_reasons"] = reasons
    return evidence


def _partition_trades(
    trades: list[ParsedTrade],
    boundary: dict[str, Any],
) -> tuple[list[ParsedTrade], list[dict[str, Any]], dict[str, int]]:
    scoring = boundary["scoring_window"]
    start = _parse_utc_timestamp(scoring["start_inclusive"], "scoring_window.start_inclusive")
    end = _parse_utc_timestamp(scoring["end_exclusive"], "scoring_window.end_exclusive")
    included: list[ParsedTrade] = []
    excluded_evidence: list[dict[str, Any]] = []
    pre_window_count = 0
    post_window_count = 0

    for trade in trades:
        reasons: list[str] = []
        if trade.open_date < start:
            reasons.append("pre_window_open")
            pre_window_count += 1
        if trade.close_date >= end:
            reasons.append("post_window_close")
            post_window_count += 1
        if reasons:
            excluded_evidence.append(_trade_evidence(trade, reasons=reasons))
        else:
            included.append(trade)

    counts = {
        "input_trades": len(trades),
        "included_trades": len(included),
        "excluded_trades": len(excluded_evidence),
        "excluded_pre_window_open_trades": pre_window_count,
        "excluded_post_window_close_trades": post_window_count,
        "included_force_exit_trades": sum(
            trade.exit_reason == "force_exit" for trade in included
        ),
    }
    return included, excluded_evidence, counts


def _freqtrade_drawdown(trades: list[ParsedTrade], starting_balance: float) -> float:
    if not trades:
        return 0.0
    try:
        import pandas as pd

        from freqtrade.data.metrics import calculate_max_drawdown
    except ImportError as exc:
        raise ModelComparisonOosExtractorError(
            "Non-empty OOS drawdown extraction requires the full Freqtrade runtime dependencies"
        ) from exc

    frame = pd.DataFrame(
        {
            "close_date": [trade.close_date for trade in trades],
            "profit_abs": [trade.profit_abs for trade in trades],
        }
    )
    result = calculate_max_drawdown(
        frame,
        date_col="close_date",
        value_col="profit_abs",
        starting_balance=starting_balance,
        relative=False,
    )
    return float(result.relative_account_drawdown)


def _stability_metrics(
    trades: list[ParsedTrade],
    starting_balance: float,
    semantics: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    folds = semantics["metrics"]["stability"]["folds"]
    fold_trade_counts: dict[str, int] = {}
    fold_profits: dict[str, float] = {}
    profitable_folds = 0

    for fold in folds:
        start = _parse_utc_timestamp(fold["start_inclusive"], f"fold {fold['name']} start")
        end = _parse_utc_timestamp(fold["end_exclusive"], f"fold {fold['name']} end")
        fold_trades = [trade for trade in trades if start <= trade.close_date < end]
        fold_profit = math.fsum(trade.profit_abs for trade in fold_trades) / starting_balance
        fold_trade_counts[fold["name"]] = len(fold_trades)
        fold_profits[fold["name"]] = fold_profit
        if fold_profit > 0:
            profitable_folds += 1

    evaluated_folds = len(folds)
    stability = profitable_folds / evaluated_folds
    evidence = {
        "evaluated_folds": evaluated_folds,
        "profitable_folds": profitable_folds,
        "fold_trade_counts": fold_trade_counts,
        "fold_profits": fold_profits,
    }
    return stability, evidence


def extract_oos_result(
    archive_path: Path,
    manifest_path: Path,
    *,
    drawdown_calculator: DrawdownCalculator | None = None,
) -> dict[str, Any]:
    """Extract strict-OOS metrics and audit evidence without executing a model or backtest."""
    comparison = load_model_comparison_contract(DEFAULT_COMPARISON_CONTRACT)
    boundary = load_oos_trade_boundary_contract(DEFAULT_BOUNDARY_CONTRACT)
    semantics = load_model_comparison_metric_semantics(DEFAULT_METRIC_SEMANTICS)
    manifest = _validate_manifest_against_comparison(manifest_path.resolve(), comparison)
    stats, stats_member, archive_sha256 = _load_backtest_stats(archive_path)
    strategy_stats = _strategy_stats_for_manifest(stats, manifest)
    starting_balance = _starting_balance(strategy_stats)

    raw_trades = strategy_stats.get("trades")
    if not isinstance(raw_trades, list):
        raise ModelComparisonOosExtractorError("Backtest strategy result trades must be a list")
    required_fields = semantics["required_trade_fields"]
    trades = [
        _parse_trade(trade, source_index, required_fields)
        for source_index, trade in enumerate(raw_trades)
    ]
    included, excluded_evidence, counts = _partition_trades(trades, boundary)

    profit = math.fsum(trade.profit_abs for trade in included) / starting_balance
    calculator = drawdown_calculator or _freqtrade_drawdown
    drawdown = float(calculator(included, starting_balance))
    if not math.isfinite(drawdown) or drawdown < 0:
        raise ModelComparisonOosExtractorError(
            "Drawdown calculator must return a finite non-negative ratio"
        )
    stability, stability_evidence = _stability_metrics(included, starting_balance, semantics)

    return {
        "schema_version": 1,
        "extractor_id": EXTRACTOR_ID,
        "metric_semantics_id": semantics["metric_semantics_id"],
        "oos_trade_boundary_id": boundary["boundary_id"],
        "model_type": manifest["freqai_model"],
        "experiment_identity": manifest["experiment_id"],
        "strategy": manifest["strategy"],
        "source": {
            "archive_sha256": archive_sha256,
            "stats_member": stats_member,
        },
        "scoring_window": boundary["scoring_window"],
        "starting_balance": starting_balance,
        "counts": counts,
        "metrics": {
            "profit": profit,
            "drawdown": drawdown,
            "trades": len(included),
            "stability": stability,
        },
        "stability_evidence": stability_evidence,
        "included_trade_evidence": [_trade_evidence(trade) for trade in included],
        "excluded_trade_evidence": excluded_evidence,
        "authorization": {
            "final_holdout_used": False,
            "retuning_allowed": False,
            "promotion_allowed": False,
            "profitability_claim_allowed": False,
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ModelComparisonOosExtractorError(f"Unable to write extraction output: {exc}") from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Existing Freqtrade backtest result ZIP")
    parser.add_argument("manifest", type=Path, help="Canonical materialized experiment manifest")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON evidence path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = extract_oos_result(args.archive, args.manifest)
        _write_json(args.output, result)
    except (ModelComparisonOosExtractorError, RuntimeError) as exc:
        print(f"OOS result extraction failed: {exc}", file=sys.stderr)
        return 1
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
