#!/usr/bin/env python3
"""Validate the Phase 6 model-comparison contract without running market research."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
TIMERANGE_PATTERN = re.compile(r"^[0-9]{8}-[0-9]{8}$")
EXPECTED_MODELS = ["LightGBMRegressor", "XGBoostRegressor"]
EXPECTED_PRIMARY_METRICS = ["profit", "drawdown", "trades", "stability"]
EXPECTED_PROTECTED_USAGE = (
    "forbidden_for_training_tuning_feature_selection_model_selection_model_comparison"
)
BASELINE_MANIFEST = REPO_ROOT / "ai_platform/experiments/baseline-v1.json"
BASELINE_REGISTRY = REPO_ROOT / "ai_platform/registry/baseline-v1.json"
BASELINE_CONFIG = REPO_ROOT / "ai_platform/configs/freqai-baseline.example.json"


class ModelComparisonContractError(RuntimeError):
    """Raised when a model-comparison definition violates the frozen research contract."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelComparisonContractError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ModelComparisonContractError(f"{label} must contain a JSON object")
    return payload


def _resolve_repo_path(value: str) -> Path:
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ModelComparisonContractError(f"Path escapes repository root: {value}") from exc
    return candidate


def _parse_timerange(value: Any, label: str) -> tuple[datetime, datetime]:
    if not isinstance(value, str) or not TIMERANGE_PATTERN.fullmatch(value):
        raise ModelComparisonContractError(f"{label} must use YYYYMMDD-YYYYMMDD format")
    start_raw, end_raw = value.split("-", maxsplit=1)
    start = datetime.strptime(start_raw, "%Y%m%d")
    end = datetime.strptime(end_raw, "%Y%m%d")
    if start > end:
        raise ModelComparisonContractError(f"{label} starts after it ends")
    return start, end


def _timeranges_overlap(left: str, right: str) -> bool:
    left_start, left_end = _parse_timerange(left, "left timerange")
    right_start, right_end = _parse_timerange(right, "right timerange")
    return left_start <= right_end and right_start <= left_end


def _validate_selection_window(label: str, timerange: Any, protected_timerange: str) -> None:
    if not isinstance(timerange, str):
        raise ModelComparisonContractError(f"{label} must be a timerange string")
    _parse_timerange(timerange, label)
    if _timeranges_overlap(timerange, protected_timerange):
        raise ModelComparisonContractError(
            f"{label} overlaps protected final holdout {protected_timerange}; "
            "the final holdout cannot be used for model comparison or selection"
        )


def _validate_header(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != 1:
        raise ModelComparisonContractError("Only model comparison schema_version 1 is supported")
    comparison_id = plan.get("comparison_id")
    if not isinstance(comparison_id, str) or not ID_PATTERN.fullmatch(comparison_id):
        raise ModelComparisonContractError("comparison_id contains unsupported characters")
    if plan.get("status") != "contract_only":
        raise ModelComparisonContractError("The first Phase 6 slice must remain contract_only")
    if plan.get("models") != EXPECTED_MODELS:
        raise ModelComparisonContractError(
            "The first model comparison must be LightGBMRegressor vs XGBoostRegressor"
        )
    if plan.get("variable_under_test") != "freqai_model":
        raise ModelComparisonContractError(
            "freqai_model must be the only primary variable under test"
        )


def _load_shared_experiment(plan: dict[str, Any]) -> dict[str, Any]:
    shared = plan.get("shared_experiment")
    if not isinstance(shared, dict):
        raise ModelComparisonContractError("shared_experiment must be an object")
    return shared


def _validate_shared_baseline(shared: dict[str, Any]) -> dict[str, Any]:
    baseline_manifest = _read_json(BASELINE_MANIFEST, "baseline experiment manifest")
    baseline_registry = _read_json(BASELINE_REGISTRY, "baseline registry definition")
    baseline_config = _read_json(BASELINE_CONFIG, "baseline research config")
    expected_shared = {
        "config": baseline_manifest["config"],
        "feature_set_id": baseline_registry["feature_set_id"],
        "target_id": baseline_registry["target_id"],
        "pairs": baseline_manifest["pairs"],
        "timeframes": baseline_manifest["timeframes"],
        "fee": baseline_manifest["fee"],
    }
    drifted = [
        field for field, expected in expected_shared.items() if shared.get(field) != expected
    ]
    if drifted:
        raise ModelComparisonContractError(
            f"shared_experiment.{drifted[0]} drifted from the current baseline contract"
        )
    return baseline_config


def _validate_risk_baseline(
    shared: dict[str, Any], baseline_config: dict[str, Any]
) -> dict[str, Any]:
    risk = shared.get("risk_assumptions")
    if not isinstance(risk, dict):
        raise ModelComparisonContractError("shared_experiment.risk_assumptions must be an object")
    if risk.get("dry_run") is not True or baseline_config.get("dry_run") is not True:
        raise ModelComparisonContractError("Model comparison must remain research-only dry-run")
    if risk.get("trading_mode") != baseline_config.get("trading_mode"):
        raise ModelComparisonContractError("Model comparison trading mode drifted from baseline")
    if risk.get("max_open_trades") != baseline_config.get("max_open_trades"):
        raise ModelComparisonContractError("Model comparison max_open_trades drifted from baseline")
    if risk.get("can_short") is not False:
        raise ModelComparisonContractError("The comparison must remain long-only")
    return risk


def _validate_protected_holdout(plan: dict[str, Any], risk: dict[str, Any]) -> str:
    protected = plan.get("protected_final_holdout")
    if not isinstance(protected, dict):
        raise ModelComparisonContractError("protected_final_holdout must be an object")
    if protected.get("usage") != EXPECTED_PROTECTED_USAGE:
        raise ModelComparisonContractError(
            "Protected final holdout usage policy is not strict enough"
        )

    declaration_path_value = protected.get("declaration")
    if not isinstance(declaration_path_value, str):
        raise ModelComparisonContractError("protected_final_holdout.declaration must be a path")
    declaration = _read_json(
        _resolve_repo_path(declaration_path_value),
        "prospective final holdout declaration",
    )
    protected_timerange = protected.get("timerange")
    if protected_timerange != declaration.get("final_holdout", {}).get("timerange"):
        raise ModelComparisonContractError(
            "Protected final holdout must exactly match the prospective declaration"
        )
    if declaration.get("final_holdout", {}).get("used") is not False:
        raise ModelComparisonContractError("Prospective final holdout is no longer marked unused")
    if declaration.get("authorization", {}).get("retuning_allowed") is not False:
        raise ModelComparisonContractError("Prospective final holdout declaration permits retuning")

    frozen = declaration.get("frozen_parameters", {})
    drifted = [
        parameter
        for parameter in ("entry_prediction_threshold", "exit_prediction_threshold")
        if risk.get(parameter) != frozen.get(parameter)
    ]
    if drifted:
        raise ModelComparisonContractError(
            f"shared_experiment.risk_assumptions.{drifted[0]} drifted from the frozen candidate"
        )
    if not isinstance(protected_timerange, str):
        raise ModelComparisonContractError("protected_final_holdout.timerange must be a string")
    _parse_timerange(protected_timerange, "protected_final_holdout.timerange")
    return protected_timerange


def _validate_selection_windows(shared: dict[str, Any], protected_timerange: str) -> None:
    for field in ("training_window", "tuning_window"):
        _validate_selection_window(
            f"shared_experiment.{field}",
            shared.get(field),
            protected_timerange,
        )

    historical_windows = shared.get("historical_oos_windows")
    if not isinstance(historical_windows, list) or not historical_windows:
        raise ModelComparisonContractError("At least one historical OOS window is required")
    for index, window in enumerate(historical_windows):
        if not isinstance(window, dict):
            raise ModelComparisonContractError("Historical OOS windows must be objects")
        if window.get("unseen_status") != "consumed_historical_oos":
            raise ModelComparisonContractError(
                "Historical OOS inputs must be explicitly marked consumed_historical_oos"
            )
        _validate_selection_window(
            f"shared_experiment.historical_oos_windows[{index}].timerange",
            window.get("timerange"),
            protected_timerange,
        )


def _validate_policies(plan: dict[str, Any]) -> None:
    expected_parameter_policy = {
        "policy": "fixed_before_execution_model_specific_identity",
        "joint_tuning_allowed": False,
        "feature_changes_allowed": False,
    }
    if plan.get("model_parameter_policy") != expected_parameter_policy:
        raise ModelComparisonContractError(
            "Model parameters must be fixed before execution and feature changes are forbidden"
        )

    selection = plan.get("selection_policy")
    if not isinstance(selection, dict):
        raise ModelComparisonContractError("selection_policy must be an object")
    if selection.get("primary_metrics") != EXPECTED_PRIMARY_METRICS:
        raise ModelComparisonContractError("Primary model-selection metrics drifted")
    forbidden_true_fields = (
        "final_holdout_metrics_allowed",
        "promotion_allowed",
        "profitability_claim_allowed",
    )
    if any(selection.get(field) is not False for field in forbidden_true_fields):
        raise ModelComparisonContractError(
            "Final holdout metrics, promotion, and profitability claims must remain forbidden"
        )

    result_schema = plan.get("result_schema")
    if not isinstance(result_schema, str) or not _resolve_repo_path(result_schema).is_file():
        raise ModelComparisonContractError(
            "result_schema must reference an existing repository file"
        )


def load_model_comparison_contract(path: Path) -> dict[str, Any]:
    plan = _read_json(path.resolve(), "model comparison contract")
    _validate_header(plan)
    shared = _load_shared_experiment(plan)
    baseline_config = _validate_shared_baseline(shared)
    risk = _validate_risk_baseline(shared, baseline_config)
    protected_timerange = _validate_protected_holdout(plan, risk)
    _validate_selection_windows(shared, protected_timerange)
    _validate_policies(plan)
    return plan


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to model comparison contract JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plan = load_model_comparison_contract(args.contract)
    except ModelComparisonContractError as exc:
        print(f"Model comparison contract invalid: {exc}", file=sys.stderr)
        return 1
    print(plan["comparison_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
