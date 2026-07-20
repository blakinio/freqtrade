#!/usr/bin/env python3
"""Validate and evaluate the predeclared Phase 6 model-selection policy."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ai_platform.scripts.model_comparison_contract import load_model_comparison_contract
from ai_platform.scripts.model_comparison_harness import build_materialization
from ai_platform.scripts.model_comparison_metric_semantics import (
    load_model_comparison_metric_semantics,
)
from ai_platform.scripts.oos_trade_boundary_contract import load_oos_trade_boundary_contract


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "ai_platform/model_comparison/selection-policy-v1.json"
CANONICAL_MATERIALIZATION_ROOT = "ai_platform/artifacts/model-comparison/materialized"
EXPECTED_POLICY_ID = "freqai-model-comparison-selection-v1"
EXPECTED_MODELS = ["LightGBMRegressor", "XGBoostRegressor"]
EXPECTED_AUTHORIZATION = {
    "final_holdout_used": False,
    "retuning_allowed": False,
    "promotion_allowed": False,
    "profitability_claim_allowed": False,
}
EXPECTED_SHARED_EVIDENCE = {
    "exact_models_required": True,
    "canonical_experiment_identity_required": True,
    "same_starting_balance_required": True,
    "same_scoring_window_required": True,
    "same_metric_semantics_required": True,
    "same_oos_trade_boundary_required": True,
}
EXPECTED_GATE_PROVENANCE = {
    "minimum_trades": "gates.minimum_holdout_trades",
    "minimum_profit": "gates.minimum_holdout_profit",
    "maximum_drawdown": "gates.maximum_holdout_drawdown",
    "minimum_stability": (
        "gates.minimum_profitable_folds / "
        "metric_semantics.metrics.stability.evaluated_folds"
    ),
}


class ModelComparisonSelectionPolicyError(RuntimeError):
    """Raised when selection inputs or policy semantics are unsafe or inconsistent."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelComparisonSelectionPolicyError(
            f"Unable to read {label} {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ModelComparisonSelectionPolicyError(f"{label} must contain a JSON object")
    return payload


def _resolve_repo_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ModelComparisonSelectionPolicyError(
            f"{label} must be a repository-relative path"
        )
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ModelComparisonSelectionPolicyError(f"{label} escapes repository root") from exc
    return candidate


def _expected_gate_values(
    baseline_plan: dict[str, Any],
    metric_semantics: dict[str, Any],
) -> dict[str, float | int]:
    gates = baseline_plan.get("gates")
    if not isinstance(gates, dict):
        raise ModelComparisonSelectionPolicyError(
            "Baseline validation plan gates must be an object"
        )
    stability = metric_semantics["metrics"]["stability"]
    evaluated_folds = stability["evaluated_folds"]
    if not isinstance(evaluated_folds, int) or evaluated_folds <= 0:
        raise ModelComparisonSelectionPolicyError(
            "Stability evaluated_folds must be positive"
        )
    return {
        "minimum_trades": gates["minimum_holdout_trades"],
        "minimum_profit": gates["minimum_holdout_profit"],
        "maximum_drawdown": gates["maximum_holdout_drawdown"],
        "minimum_stability": gates["minimum_profitable_folds"] / evaluated_folds,
    }


def _validate_policy_semantics(
    policy: dict[str, Any],
    comparison: dict[str, Any],
    metric_semantics: dict[str, Any],
    boundary: dict[str, Any],
    baseline_plan: dict[str, Any],
) -> None:
    if policy.get("models") != {
        "incumbent": "LightGBMRegressor",
        "challenger": "XGBoostRegressor",
    }:
        raise ModelComparisonSelectionPolicyError(
            "Unexpected incumbent/challenger model identity"
        )
    if comparison.get("models") != EXPECTED_MODELS:
        raise ModelComparisonSelectionPolicyError(
            "Comparison model set drifted from selection policy"
        )
    if baseline_plan.get("holdout", {}).get("timerange") != boundary["scoring_window"][
        "timerange"
    ]:
        raise ModelComparisonSelectionPolicyError(
            "Baseline holdout gates must refer to the same consumed historical OOS scoring window"
        )

    expected_eligibility = {
        **_expected_gate_values(baseline_plan, metric_semantics),
        "provenance": EXPECTED_GATE_PROVENANCE,
    }
    if policy.get("eligibility_gates") != expected_eligibility:
        raise ModelComparisonSelectionPolicyError(
            "Selection eligibility gates drifted from predeclared baseline validation evidence"
        )
    if policy.get("objectives") != {
        "profit": "maximize",
        "drawdown": "minimize",
        "stability": "maximize",
        "trades": "eligibility_only",
    }:
        raise ModelComparisonSelectionPolicyError("Unexpected model-selection objectives")
    if policy.get("decision_rule") != {
        "policy": "eligibility_then_strict_pareto",
        "strict_pareto_metrics": ["profit", "drawdown", "stability"],
        "one_eligible": "select_eligible",
        "both_ineligible": "select_null",
        "both_eligible_and_one_strictly_dominates": "select_dominant",
        "both_eligible_no_strict_dominance": "select_null",
        "exact_tie": "select_null",
    }:
        raise ModelComparisonSelectionPolicyError("Selection decision rule drifted")
    if policy.get("shared_evidence_requirements") != EXPECTED_SHARED_EVIDENCE:
        raise ModelComparisonSelectionPolicyError(
            "Selection shared-evidence requirements drifted"
        )
    if policy.get("authorization") != EXPECTED_AUTHORIZATION:
        raise ModelComparisonSelectionPolicyError(
            "Selection policy cannot authorize holdout use, retuning, promotion, or claims"
        )


def load_model_comparison_selection_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    policy = _read_json(path.resolve(), "model comparison selection policy")
    if policy.get("schema_version") != 1:
        raise ModelComparisonSelectionPolicyError(
            "Only selection policy schema_version 1 is supported"
        )
    if policy.get("selection_policy_id") != EXPECTED_POLICY_ID:
        raise ModelComparisonSelectionPolicyError("Unexpected selection_policy_id")

    comparison = load_model_comparison_contract(
        _resolve_repo_path(policy.get("comparison_contract"), "comparison_contract")
    )
    metric_semantics = load_model_comparison_metric_semantics(
        _resolve_repo_path(policy.get("metric_semantics"), "metric_semantics")
    )
    boundary = load_oos_trade_boundary_contract(
        _resolve_repo_path(policy.get("oos_trade_boundary"), "oos_trade_boundary")
    )
    baseline_plan = _read_json(
        _resolve_repo_path(
            policy.get("baseline_validation_plan"),
            "baseline_validation_plan",
        ),
        "baseline validation plan",
    )
    _read_json(
        _resolve_repo_path(policy.get("extraction_schema"), "extraction_schema"),
        "OOS extraction schema",
    )
    _validate_policy_semantics(
        policy,
        comparison,
        metric_semantics,
        boundary,
        baseline_plan,
    )
    return policy


def _canonical_experiment_identities(policy: dict[str, Any]) -> dict[str, str]:
    contract_path = _resolve_repo_path(
        policy["comparison_contract"],
        "comparison_contract",
    )
    materialization = build_materialization(
        contract_path,
        output_root=CANONICAL_MATERIALIZATION_ROOT,
    )
    return {
        model["model_type"]: model["experiment_identity"]
        for model in materialization["models"]
    }


def _validate_extraction_consistency(extraction: dict[str, Any]) -> None:
    counts = extraction["counts"]
    metrics = extraction["metrics"]
    included_evidence = extraction["included_trade_evidence"]
    excluded_evidence = extraction["excluded_trade_evidence"]
    stability = extraction["stability_evidence"]

    if counts["input_trades"] != counts["included_trades"] + counts["excluded_trades"]:
        raise ModelComparisonSelectionPolicyError(
            "Extraction trade counts are internally inconsistent"
        )
    if metrics["trades"] != counts["included_trades"]:
        raise ModelComparisonSelectionPolicyError(
            "Extraction metric trade count does not match included-trade evidence"
        )
    if len(included_evidence) != counts["included_trades"]:
        raise ModelComparisonSelectionPolicyError(
            "Included-trade evidence length does not match extraction counts"
        )
    if len(excluded_evidence) != counts["excluded_trades"]:
        raise ModelComparisonSelectionPolicyError(
            "Excluded-trade evidence length does not match extraction counts"
        )
    if counts["included_force_exit_trades"] > counts["included_trades"]:
        raise ModelComparisonSelectionPolicyError(
            "Included force-exit count exceeds included trades"
        )
    if sum(stability["fold_trade_counts"].values()) != metrics["trades"]:
        raise ModelComparisonSelectionPolicyError(
            "Stability fold trade counts do not cover all included trades"
        )
    profitable_from_folds = sum(value > 0 for value in stability["fold_profits"].values())
    if profitable_from_folds != stability["profitable_folds"]:
        raise ModelComparisonSelectionPolicyError(
            "Profitable-fold count does not match fold-profit evidence"
        )
    expected_stability = stability["profitable_folds"] / stability["evaluated_folds"]
    if metrics["stability"] != expected_stability:
        raise ModelComparisonSelectionPolicyError(
            "Stability metric does not match profitable-fold evidence"
        )
    fold_profit = math.fsum(stability["fold_profits"].values())
    if not math.isclose(fold_profit, metrics["profit"], rel_tol=1e-12, abs_tol=1e-12):
        raise ModelComparisonSelectionPolicyError(
            "Fold profits do not reproduce the extraction profit metric"
        )


def _validate_extractions(
    policy: dict[str, Any],
    extractions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if len(extractions) != 2:
        raise ModelComparisonSelectionPolicyError(
            "Exactly two OOS extraction artifacts are required"
        )
    schema = _read_json(
        _resolve_repo_path(policy["extraction_schema"], "extraction_schema"),
        "OOS extraction schema",
    )
    validator = Draft202012Validator(schema)
    for index, extraction in enumerate(extractions):
        try:
            validator.validate(extraction)
        except ValidationError as exc:
            raise ModelComparisonSelectionPolicyError(
                f"OOS extraction artifact {index} does not match the extraction schema: "
                f"{exc.message}"
            ) from exc
        _validate_extraction_consistency(extraction)

    by_model = {extraction["model_type"]: extraction for extraction in extractions}
    if set(by_model) != set(EXPECTED_MODELS) or len(by_model) != 2:
        raise ModelComparisonSelectionPolicyError(
            "Selection requires exactly one LightGBMRegressor and one XGBoostRegressor extraction"
        )

    expected_identities = _canonical_experiment_identities(policy)
    for model_type, extraction in by_model.items():
        if extraction["experiment_identity"] != expected_identities[model_type]:
            raise ModelComparisonSelectionPolicyError(
                f"Extraction experiment identity drifted for {model_type}"
            )

    first, second = (by_model[model] for model in EXPECTED_MODELS)
    if first["starting_balance"] != second["starting_balance"]:
        raise ModelComparisonSelectionPolicyError(
            "Model-selection evidence must use the same starting balance"
        )
    if first["scoring_window"] != second["scoring_window"]:
        raise ModelComparisonSelectionPolicyError(
            "Model-selection evidence must use the same scoring window"
        )
    if first["metric_semantics_id"] != second["metric_semantics_id"]:
        raise ModelComparisonSelectionPolicyError(
            "Model-selection evidence must use the same metric semantics"
        )
    if first["oos_trade_boundary_id"] != second["oos_trade_boundary_id"]:
        raise ModelComparisonSelectionPolicyError(
            "Model-selection evidence must use the same OOS trade boundary"
        )
    return by_model


def _eligibility_evidence(
    extraction: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, Any]:
    metrics = extraction["metrics"]
    checks = {
        "minimum_trades": {
            "actual": metrics["trades"],
            "threshold": gates["minimum_trades"],
            "passed": metrics["trades"] >= gates["minimum_trades"],
        },
        "minimum_profit": {
            "actual": metrics["profit"],
            "threshold": gates["minimum_profit"],
            "passed": metrics["profit"] >= gates["minimum_profit"],
        },
        "maximum_drawdown": {
            "actual": metrics["drawdown"],
            "threshold": gates["maximum_drawdown"],
            "passed": metrics["drawdown"] <= gates["maximum_drawdown"],
        },
        "minimum_stability": {
            "actual": metrics["stability"],
            "threshold": gates["minimum_stability"],
            "passed": metrics["stability"] >= gates["minimum_stability"],
        },
    }
    return {
        "eligible": all(check["passed"] for check in checks.values()),
        "gates": checks,
    }


def _strictly_dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_metrics = left["metrics"]
    right_metrics = right["metrics"]
    no_worse = (
        left_metrics["profit"] >= right_metrics["profit"]
        and left_metrics["drawdown"] <= right_metrics["drawdown"]
        and left_metrics["stability"] >= right_metrics["stability"]
    )
    strictly_better = (
        left_metrics["profit"] > right_metrics["profit"]
        or left_metrics["drawdown"] < right_metrics["drawdown"]
        or left_metrics["stability"] > right_metrics["stability"]
    )
    return no_worse and strictly_better


def evaluate_model_selection(
    extractions: list[dict[str, Any]],
    policy_path: Path = DEFAULT_POLICY,
) -> dict[str, Any]:
    """Evaluate strict-OOS extraction artifacts without retuning or model execution."""
    policy = load_model_comparison_selection_policy(policy_path)
    by_model = _validate_extractions(policy, extractions)
    gates = policy["eligibility_gates"]
    eligibility = {
        model: _eligibility_evidence(by_model[model], gates)
        for model in EXPECTED_MODELS
    }
    eligible_models = [model for model in EXPECTED_MODELS if eligibility[model]["eligible"]]

    incumbent, challenger = EXPECTED_MODELS
    incumbent_dominates = False
    challenger_dominates = False
    selected_model: str | None = None
    if len(eligible_models) == 1:
        selected_model = eligible_models[0]
        basis = "only_model_passing_predeclared_eligibility_gates"
    elif not eligible_models:
        basis = "no_model_passed_predeclared_eligibility_gates"
    else:
        incumbent_dominates = _strictly_dominates(
            by_model[incumbent],
            by_model[challenger],
        )
        challenger_dominates = _strictly_dominates(
            by_model[challenger],
            by_model[incumbent],
        )
        if incumbent_dominates:
            selected_model = incumbent
            basis = "strict_pareto_dominance_among_eligible_models"
        elif challenger_dominates:
            selected_model = challenger
            basis = "strict_pareto_dominance_among_eligible_models"
        else:
            basis = "eligible_models_inconclusive_no_strict_pareto_dominance"

    return {
        "schema_version": 1,
        "selection_policy_id": policy["selection_policy_id"],
        "model_eligibility": eligibility,
        "dominance": {
            "LightGBMRegressor_over_XGBoostRegressor": incumbent_dominates,
            "XGBoostRegressor_over_LightGBMRegressor": challenger_dominates,
        },
        "selection": {
            "selected_model": selected_model,
            "basis": basis,
            "final_holdout_used": False,
            "promotion_allowed": False,
            "profitability_claim_allowed": False,
        },
        "authorization": policy["authorization"],
    }
