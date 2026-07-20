#!/usr/bin/env python3
"""Validate Phase 6 model-comparison metric semantics without scoring model output."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ai_platform.scripts.model_comparison_contract import load_model_comparison_contract
from ai_platform.scripts.oos_trade_boundary_contract import load_oos_trade_boundary_contract


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SEMANTICS_ID = "freqai-model-comparison-metrics-v1"
EXPECTED_METRICS = ["profit", "drawdown", "trades", "stability"]
EXPECTED_COMPARISON = "ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json"
EXPECTED_BOUNDARY = "ai_platform/model_comparison/oos-trade-boundary-v1.json"


class ModelComparisonMetricSemanticsError(RuntimeError):
    """Raised when model-comparison metric semantics are incomplete or inconsistent."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelComparisonMetricSemanticsError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ModelComparisonMetricSemanticsError(f"{label} must contain a JSON object")
    return payload


def _resolve_repo_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ModelComparisonMetricSemanticsError(f"{label} must be a repository-relative path")
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ModelComparisonMetricSemanticsError(f"{label} escapes repository root") from exc
    return candidate


def _parse_iso_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ModelComparisonMetricSemanticsError(f"{label} must be an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ModelComparisonMetricSemanticsError(f"{label} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo != UTC:
        raise ModelComparisonMetricSemanticsError(f"{label} must use UTC")
    return parsed


def _validate_metric_names(semantics: dict[str, Any], comparison: dict[str, Any]) -> None:
    metrics = semantics.get("metrics")
    if not isinstance(metrics, dict) or list(metrics) != EXPECTED_METRICS:
        raise ModelComparisonMetricSemanticsError(
            "metrics must define profit, drawdown, trades, and stability in canonical order"
        )
    if comparison.get("selection_policy", {}).get("primary_metrics") != EXPECTED_METRICS:
        raise ModelComparisonMetricSemanticsError(
            "Metric semantics must exactly match comparison primary_metrics"
        )


def _validate_starting_balance(semantics: dict[str, Any]) -> None:
    starting_balance = semantics.get("starting_balance")
    expected = {
        "source_field": "starting_balance",
        "requirement": "positive_finite_number",
    }
    if starting_balance != expected:
        raise ModelComparisonMetricSemanticsError(
            "starting_balance must come from a positive finite strategy-result field"
        )


def _validate_core_metrics(semantics: dict[str, Any]) -> None:
    metrics = semantics["metrics"]
    expected_profit = {
        "result_field": "profit",
        "freqtrade_equivalent": "profit_total",
        "formula": "sum(included_trades.profit_abs) / starting_balance",
        "empty_trade_value": 0.0,
    }
    if metrics.get("profit") != expected_profit:
        raise ModelComparisonMetricSemanticsError("profit semantics drifted from Freqtrade profit_total")

    expected_drawdown = {
        "result_field": "drawdown",
        "freqtrade_equivalent": "max_drawdown_account",
        "implementation": "freqtrade.data.metrics.calculate_max_drawdown",
        "date_col": "close_date",
        "value_col": "profit_abs",
        "starting_balance_source": "starting_balance",
        "result_attribute": "relative_account_drawdown",
        "relative_selection": False,
        "empty_trade_value": 0.0,
    }
    if metrics.get("drawdown") != expected_drawdown:
        raise ModelComparisonMetricSemanticsError(
            "drawdown semantics drifted from Freqtrade max_drawdown_account"
        )

    expected_trades = {
        "result_field": "trades",
        "formula": "count(included_trades)",
        "empty_trade_value": 0,
    }
    if metrics.get("trades") != expected_trades:
        raise ModelComparisonMetricSemanticsError("trades must count strict-OOS included trades only")


def _validate_stability_folds(
    semantics: dict[str, Any],
    boundary: dict[str, Any],
) -> None:
    stability = semantics["metrics"].get("stability")
    if not isinstance(stability, dict):
        raise ModelComparisonMetricSemanticsError("stability semantics must be an object")
    if stability.get("policy") != "calendar_month_profitable_fold_ratio":
        raise ModelComparisonMetricSemanticsError(
            "stability must normalize the profitable-fold concept over calendar months"
        )
    if stability.get("fold_assignment_field") != "close_date":
        raise ModelComparisonMetricSemanticsError("Stability folds must realize profit by close_date")
    if stability.get("fold_timezone") != "UTC":
        raise ModelComparisonMetricSemanticsError("Stability folds must use UTC")
    if stability.get("profitable_fold_condition") != "> 0":
        raise ModelComparisonMetricSemanticsError("A profitable stability fold must have profit > 0")
    if stability.get("formula") != "profitable_folds / evaluated_folds":
        raise ModelComparisonMetricSemanticsError("Unexpected stability formula")
    if stability.get("evaluated_folds") != 2:
        raise ModelComparisonMetricSemanticsError("Phase 6 stability must evaluate exactly two folds")
    if stability.get("minimum") != 0.0 or stability.get("maximum") != 1.0:
        raise ModelComparisonMetricSemanticsError("Stability must remain normalized to [0, 1]")

    scoring = boundary["scoring_window"]
    scoring_start = _parse_iso_utc(scoring["start_inclusive"], "scoring_window.start_inclusive")
    scoring_end = _parse_iso_utc(scoring["end_exclusive"], "scoring_window.end_exclusive")
    folds = stability.get("folds")
    if not isinstance(folds, list) or len(folds) != 2:
        raise ModelComparisonMetricSemanticsError("Stability must declare exactly two calendar folds")

    previous_end = scoring_start
    for index, fold in enumerate(folds):
        if not isinstance(fold, dict):
            raise ModelComparisonMetricSemanticsError("Stability folds must be objects")
        start = _parse_iso_utc(fold.get("start_inclusive"), f"stability.folds[{index}].start_inclusive")
        end = _parse_iso_utc(fold.get("end_exclusive"), f"stability.folds[{index}].end_exclusive")
        if start != previous_end:
            raise ModelComparisonMetricSemanticsError(
                "Stability folds must be contiguous and start at the OOS boundary"
            )
        if end <= start:
            raise ModelComparisonMetricSemanticsError("Stability fold end must be after start")
        previous_end = end
    if previous_end != scoring_end:
        raise ModelComparisonMetricSemanticsError(
            "Stability folds must exactly cover the complete strict OOS scoring window"
        )

    first_start = _parse_iso_utc(folds[0]["start_inclusive"], "first fold start")
    second_start = _parse_iso_utc(folds[1]["start_inclusive"], "second fold start")
    if second_start != first_start + timedelta(days=31):
        raise ModelComparisonMetricSemanticsError("Expected May and June 2026 calendar folds")


def _validate_empty_oos_policy(semantics: dict[str, Any]) -> None:
    expected = {
        "profit": 0.0,
        "drawdown": 0.0,
        "trades": 0,
        "stability": 0.0,
        "selection_evidence_sufficient": False,
    }
    if semantics.get("empty_oos_policy") != expected:
        raise ModelComparisonMetricSemanticsError(
            "Empty OOS must fail closed for selection evidence with zero-valued metrics"
        )


def _validate_selection_constraints(semantics: dict[str, Any]) -> None:
    expected = {
        "metric_scope": "strict_oos_included_trades_only",
        "same_starting_balance_required": True,
        "same_scoring_window_required": True,
        "same_stability_folds_required": True,
        "final_holdout_metrics_allowed": False,
        "promotion_allowed": False,
        "profitability_claim_allowed": False,
    }
    if semantics.get("selection_constraints") != expected:
        raise ModelComparisonMetricSemanticsError(
            "Metric selection constraints must preserve fair comparison and holdout isolation"
        )


def _validate_numeric_contract_examples(semantics: dict[str, Any]) -> None:
    stability = semantics["metrics"]["stability"]
    minimum = stability.get("minimum")
    maximum = stability.get("maximum")
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in (minimum, maximum)):
        raise ModelComparisonMetricSemanticsError("Stability bounds must be finite numbers")


def load_model_comparison_metric_semantics(path: Path) -> dict[str, Any]:
    semantics = _read_json(path.resolve(), "model comparison metric semantics")
    if semantics.get("schema_version") != 1:
        raise ModelComparisonMetricSemanticsError("Only metric semantics schema_version 1 is supported")
    if semantics.get("metric_semantics_id") != EXPECTED_SEMANTICS_ID:
        raise ModelComparisonMetricSemanticsError("Unexpected metric_semantics_id")
    if semantics.get("comparison_contract") != EXPECTED_COMPARISON:
        raise ModelComparisonMetricSemanticsError("Unexpected comparison contract path")
    if semantics.get("oos_trade_boundary") != EXPECTED_BOUNDARY:
        raise ModelComparisonMetricSemanticsError("Unexpected OOS trade-boundary path")

    comparison = load_model_comparison_contract(
        _resolve_repo_path(semantics["comparison_contract"], "comparison_contract")
    )
    boundary = load_oos_trade_boundary_contract(
        _resolve_repo_path(semantics["oos_trade_boundary"], "oos_trade_boundary")
    )
    _validate_metric_names(semantics, comparison)
    _validate_starting_balance(semantics)
    _validate_core_metrics(semantics)
    _validate_stability_folds(semantics, boundary)
    _validate_empty_oos_policy(semantics)
    _validate_selection_constraints(semantics)
    _validate_numeric_contract_examples(semantics)
    return semantics


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to metric semantics JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        semantics = load_model_comparison_metric_semantics(args.contract)
    except ModelComparisonMetricSemanticsError as exc:
        print(f"Model comparison metric semantics invalid: {exc}", file=sys.stderr)
        return 1
    print(semantics["metric_semantics_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
