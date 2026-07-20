import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ai_platform.scripts.model_comparison_harness import build_materialization
from ai_platform.scripts.model_comparison_selection_policy import (
    CANONICAL_MATERIALIZATION_ROOT,
    DEFAULT_POLICY,
    ModelComparisonSelectionPolicyError,
    evaluate_model_selection,
    load_model_comparison_selection_policy,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY_SCHEMA = ROOT / "ai_platform/model_comparison/selection-policy-schema-v1.json"
DECISION_SCHEMA = ROOT / "ai_platform/model_comparison/selection-decision-schema-v1.json"
COMPARISON_CONTRACT = ROOT / "ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json"


def _canonical_identities() -> dict[str, str]:
    materialization = build_materialization(
        COMPARISON_CONTRACT,
        output_root=CANONICAL_MATERIALIZATION_ROOT,
    )
    return {
        model["model_type"]: model["experiment_identity"]
        for model in materialization["models"]
    }


def _fold_evidence(profit: float, stability: float, trades: int) -> tuple[dict, dict]:
    if stability == 1.0:
        if profit <= 0:
            raise AssertionError("Two profitable folds require positive total profit")
        fold_profits = {"2026-05": profit / 2, "2026-06": profit / 2}
        profitable_folds = 2
    elif stability == 0.5:
        if profit > 0:
            fold_profits = {"2026-05": profit, "2026-06": 0.0}
        else:
            fold_profits = {"2026-05": 0.01, "2026-06": profit - 0.01}
        profitable_folds = 1
    elif stability == 0.0:
        if profit > 0:
            raise AssertionError("Zero profitable folds cannot have positive total profit")
        fold_profits = {"2026-05": profit, "2026-06": 0.0}
        profitable_folds = 0
    else:
        raise AssertionError("Synthetic stability must be 0.0, 0.5, or 1.0")

    may_trades = trades // 2
    fold_trade_counts = {
        "2026-05": may_trades,
        "2026-06": trades - may_trades,
    }
    stability_evidence = {
        "evaluated_folds": 2,
        "profitable_folds": profitable_folds,
        "fold_trade_counts": fold_trade_counts,
        "fold_profits": fold_profits,
    }
    return fold_trade_counts, stability_evidence


def _extraction(
    model_type: str,
    *,
    profit: float = 0.10,
    drawdown: float = 0.10,
    trades: int = 20,
    stability: float = 0.5,
    starting_balance: float = 1000.0,
) -> dict:
    identities = _canonical_identities()
    _, stability_evidence = _fold_evidence(profit, stability, trades)
    included_evidence = [
        {
            "source_index": index,
            "open_date": "2026-05-01T00:00:00Z",
            "close_date": "2026-05-02T00:00:00Z",
            "profit_abs": 0.0,
            "exit_reason": "roi",
        }
        for index in range(trades)
    ]
    return {
        "schema_version": 1,
        "extractor_id": "freqai-model-comparison-oos-extractor-v1",
        "metric_semantics_id": "freqai-model-comparison-metrics-v1",
        "oos_trade_boundary_id": "freqai-model-comparison-oos-trade-boundary-v1",
        "model_type": model_type,
        "experiment_identity": identities[model_type],
        "strategy": "AiPhase52ExitStrategy",
        "source": {
            "archive_sha256": ("a" if model_type == "LightGBMRegressor" else "b") * 64,
            "stats_member": f"{model_type}.json",
        },
        "scoring_window": {
            "timerange": "20260501-20260630",
            "start_inclusive": "2026-05-01T00:00:00Z",
            "end_exclusive": "2026-07-01T00:00:00Z",
            "timezone": "UTC",
            "source_status": "consumed_historical_oos",
        },
        "starting_balance": starting_balance,
        "counts": {
            "input_trades": trades,
            "included_trades": trades,
            "excluded_trades": 0,
            "excluded_pre_window_open_trades": 0,
            "excluded_post_window_close_trades": 0,
            "included_force_exit_trades": 0,
        },
        "metrics": {
            "profit": profit,
            "drawdown": drawdown,
            "trades": trades,
            "stability": stability,
        },
        "stability_evidence": stability_evidence,
        "included_trade_evidence": included_evidence,
        "excluded_trade_evidence": [],
        "authorization": {
            "final_holdout_used": False,
            "retuning_allowed": False,
            "promotion_allowed": False,
            "profitability_claim_allowed": False,
        },
    }


def test_selection_policy_matches_schema_and_predeclared_validation_gates() -> None:
    policy = load_model_comparison_selection_policy(DEFAULT_POLICY)
    schema = json.loads(POLICY_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(policy)

    assert policy["eligibility_gates"]["minimum_trades"] == 10
    assert policy["eligibility_gates"]["minimum_profit"] == 0.0
    assert policy["eligibility_gates"]["maximum_drawdown"] == 0.25
    assert policy["eligibility_gates"]["minimum_stability"] == 0.5
    assert policy["objectives"]["trades"] == "eligibility_only"


def test_challenger_selected_only_when_strictly_pareto_dominant() -> None:
    lightgbm = _extraction(
        "LightGBMRegressor",
        profit=0.08,
        drawdown=0.12,
        stability=0.5,
    )
    xgboost = _extraction(
        "XGBoostRegressor",
        profit=0.10,
        drawdown=0.10,
        stability=1.0,
    )

    decision = evaluate_model_selection([lightgbm, xgboost])

    assert decision["selection"]["selected_model"] == "XGBoostRegressor"
    assert decision["dominance"]["XGBoostRegressor_over_LightGBMRegressor"] is True
    assert decision["selection"]["basis"] == "strict_pareto_dominance_among_eligible_models"
    schema = json.loads(DECISION_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(decision)


def test_incumbent_selected_when_it_strictly_pareto_dominates() -> None:
    lightgbm = _extraction(
        "LightGBMRegressor",
        profit=0.12,
        drawdown=0.08,
        stability=1.0,
    )
    xgboost = _extraction(
        "XGBoostRegressor",
        profit=0.10,
        drawdown=0.10,
        stability=0.5,
    )

    decision = evaluate_model_selection([lightgbm, xgboost])

    assert decision["selection"]["selected_model"] == "LightGBMRegressor"
    assert decision["dominance"]["LightGBMRegressor_over_XGBoostRegressor"] is True


def test_only_eligible_model_is_selected() -> None:
    lightgbm = _extraction("LightGBMRegressor", trades=9)
    xgboost = _extraction("XGBoostRegressor", trades=10)

    decision = evaluate_model_selection([lightgbm, xgboost])

    assert decision["model_eligibility"]["LightGBMRegressor"]["eligible"] is False
    assert decision["model_eligibility"]["XGBoostRegressor"]["eligible"] is True
    assert decision["selection"]["selected_model"] == "XGBoostRegressor"
    assert decision["selection"]["basis"] == "only_model_passing_predeclared_eligibility_gates"


def test_conflicting_eligible_metrics_are_inconclusive() -> None:
    lightgbm = _extraction(
        "LightGBMRegressor",
        profit=0.12,
        drawdown=0.15,
        stability=1.0,
    )
    xgboost = _extraction(
        "XGBoostRegressor",
        profit=0.10,
        drawdown=0.08,
        stability=1.0,
    )

    decision = evaluate_model_selection([lightgbm, xgboost])

    assert decision["selection"]["selected_model"] is None
    assert decision["dominance"] == {
        "LightGBMRegressor_over_XGBoostRegressor": False,
        "XGBoostRegressor_over_LightGBMRegressor": False,
    }
    assert decision["selection"]["basis"] == (
        "eligible_models_inconclusive_no_strict_pareto_dominance"
    )


def test_exact_metric_tie_is_inconclusive() -> None:
    lightgbm = _extraction("LightGBMRegressor")
    xgboost = _extraction("XGBoostRegressor")

    decision = evaluate_model_selection([lightgbm, xgboost])

    assert decision["selection"]["selected_model"] is None
    assert decision["dominance"] == {
        "LightGBMRegressor_over_XGBoostRegressor": False,
        "XGBoostRegressor_over_LightGBMRegressor": False,
    }


def test_both_ineligible_models_produce_null_selection() -> None:
    lightgbm = _extraction("LightGBMRegressor", trades=9)
    xgboost = _extraction("XGBoostRegressor", drawdown=0.30)

    decision = evaluate_model_selection([lightgbm, xgboost])

    assert decision["selection"]["selected_model"] is None
    assert decision["selection"]["basis"] == "no_model_passed_predeclared_eligibility_gates"


def test_more_trades_are_not_a_directional_selection_objective() -> None:
    lightgbm = _extraction("LightGBMRegressor", trades=100)
    xgboost = _extraction("XGBoostRegressor", trades=10)

    decision = evaluate_model_selection([lightgbm, xgboost])

    assert decision["selection"]["selected_model"] is None
    assert decision["dominance"] == {
        "LightGBMRegressor_over_XGBoostRegressor": False,
        "XGBoostRegressor_over_LightGBMRegressor": False,
    }


def test_selection_rejects_mismatched_starting_balance() -> None:
    lightgbm = _extraction("LightGBMRegressor", starting_balance=1000.0)
    xgboost = _extraction("XGBoostRegressor", starting_balance=2000.0)

    with pytest.raises(ModelComparisonSelectionPolicyError, match="same starting balance"):
        evaluate_model_selection([lightgbm, xgboost])


def test_selection_rejects_noncanonical_experiment_identity() -> None:
    lightgbm = _extraction("LightGBMRegressor")
    xgboost = _extraction("XGBoostRegressor")
    xgboost["experiment_identity"] = "drifted-xgboost-identity"

    with pytest.raises(ModelComparisonSelectionPolicyError, match="identity drifted"):
        evaluate_model_selection([lightgbm, xgboost])


def test_selection_rejects_internally_inconsistent_trade_counts() -> None:
    lightgbm = _extraction("LightGBMRegressor")
    xgboost = _extraction("XGBoostRegressor")
    xgboost["counts"]["input_trades"] += 1

    with pytest.raises(ModelComparisonSelectionPolicyError, match="internally inconsistent"):
        evaluate_model_selection([lightgbm, xgboost])


def test_selection_policy_rejects_gate_drift(tmp_path: Path) -> None:
    policy = json.loads(DEFAULT_POLICY.read_text(encoding="utf-8"))
    policy["eligibility_gates"]["minimum_trades"] = 9
    path = tmp_path / "selection-policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")

    with pytest.raises(ModelComparisonSelectionPolicyError, match="eligibility gates drifted"):
        load_model_comparison_selection_policy(path)


def test_selection_decision_never_authorizes_final_holdout_or_promotion() -> None:
    decision = evaluate_model_selection(
        [_extraction("LightGBMRegressor"), _extraction("XGBoostRegressor")]
    )

    assert decision["selection"]["final_holdout_used"] is False
    assert decision["selection"]["promotion_allowed"] is False
    assert decision["selection"]["profitability_claim_allowed"] is False
    assert decision["authorization"]["retuning_allowed"] is False
