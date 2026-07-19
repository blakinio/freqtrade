import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ai_platform.scripts.run_experiment import load_manifest, validate_research_config
from ai_platform.scripts.run_optimization import (
    OptimizationError,
    build_hyperopt_command,
    evaluate_parameter_stability,
    generate_local_perturbations,
    load_optimization_plan,
    select_best_epoch,
    selection_identity,
    validate_plan_against_repository,
)
from ai_platform.scripts.run_validation import load_validation_plan


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "ai_platform" / "optimization" / "baseline-signal-thresholds-v1.json"
SCHEMA_PATH = ROOT / "ai_platform" / "optimization" / "schema-v1.json"
MANIFEST_PATH = ROOT / "ai_platform" / "experiments" / "baseline-v1.json"
VALIDATION_PATH = ROOT / "ai_platform" / "validation" / "baseline-validation-v1.json"
CONFIG_PATH = ROOT / "ai_platform" / "configs" / "freqai-baseline.example.json"
STRATEGY_PATH = ROOT / "ai_platform" / "strategies"


def test_baseline_optimization_plan_matches_schema() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(plan)


def test_phase5_plan_preserves_frozen_holdout_and_research_config() -> None:
    plan = load_optimization_plan(PLAN_PATH)
    manifest = load_manifest(MANIFEST_PATH)
    validation = load_validation_plan(VALIDATION_PATH)
    config = validate_research_config(CONFIG_PATH)

    validate_plan_against_repository(plan, manifest, validation, config)

    assert plan["training"]["timerange"] == "20251201-20260228"
    assert plan["tuning"]["timerange"] == "20260301-20260430"
    assert plan["final_holdout"] == validation["holdout"]
    assert plan["final_holdout"]["timerange"] == "20260501-20260630"
    assert config["dry_run"] is True
    assert config["exchange"]["key"] == ""
    assert config["exchange"]["secret"] == ""


def test_hyperopt_command_uses_tuning_window_and_buy_space_only(tmp_path: Path) -> None:
    plan = load_optimization_plan(PLAN_PATH)
    manifest = load_manifest(MANIFEST_PATH)

    command = build_hyperopt_command(
        manifest,
        plan,
        freqtrade_bin="freqtrade",
        config_path=CONFIG_PATH,
        strategy_path=STRATEGY_PATH,
        user_dir=tmp_path,
    )

    assert command[:2] == ["freqtrade", "hyperopt"]
    assert plan["tuning"]["timerange"] in command
    assert plan["final_holdout"]["timerange"] not in command
    assert command[command.index("--spaces") + 1] == "buy"
    assert "sell" not in command
    assert "roi" not in command
    assert "stoploss" not in command
    assert "protection" not in command
    assert "--disable-param-export" in command
    assert plan["hyperopt"]["loss"] in command


def test_plan_rejects_final_holdout_drift(tmp_path: Path) -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    plan["final_holdout"] = {
        "name": "holdout-incorrect",
        "timerange": "20260401-20260531",
    }
    plan_path = tmp_path / "optimization.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    loaded = load_optimization_plan(plan_path)
    manifest = load_manifest(MANIFEST_PATH)
    validation = load_validation_plan(VALIDATION_PATH)
    config = validate_research_config(CONFIG_PATH)

    with pytest.raises(OptimizationError, match="Final holdout must exactly match"):
        validate_plan_against_repository(loaded, manifest, validation, config)


def test_plan_rejects_tuning_overlap_with_final_holdout(tmp_path: Path) -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    plan["tuning"]["timerange"] = "20260301-20260515"
    plan_path = tmp_path / "optimization.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(OptimizationError, match="Tuning and final holdout windows must not overlap"):
        load_optimization_plan(plan_path)


def test_selection_identity_is_deterministic_and_parameter_sensitive() -> None:
    plan = load_optimization_plan(PLAN_PATH)
    git_commit = "a" * 40

    first = selection_identity(
        plan,
        git_commit=git_commit,
        parameter="entry_prediction_threshold",
        value=0.005,
    )
    second = selection_identity(
        plan,
        git_commit=git_commit,
        parameter="entry_prediction_threshold",
        value=0.005,
    )
    changed = selection_identity(
        plan,
        git_commit=git_commit,
        parameter="entry_prediction_threshold",
        value=0.006,
    )

    assert first == second
    assert first.startswith("opt-")
    assert first != changed


def test_local_perturbations_are_symmetric_inside_declared_bounds() -> None:
    stability = load_optimization_plan(PLAN_PATH)["parameter_stability"]

    assert generate_local_perturbations(0.005, stability) == [0.004, 0.006]


def test_parameter_stability_requires_all_local_neighbors_to_pass() -> None:
    stability = load_optimization_plan(PLAN_PATH)["parameter_stability"]
    baseline = {"trades": 40, "profit": 0.08, "drawdown": 0.10}
    stable_neighbors = [
        {
            "parameter": "entry_prediction_threshold",
            "value": 0.004,
            "metrics": {"trades": 35, "profit": 0.05, "drawdown": 0.12},
        },
        {
            "parameter": "entry_prediction_threshold",
            "value": 0.006,
            "metrics": {"trades": 30, "profit": 0.04, "drawdown": 0.15},
        },
    ]
    unstable_neighbors = [
        *stable_neighbors[:1],
        {
            "parameter": "entry_prediction_threshold",
            "value": 0.006,
            "metrics": {"trades": 5, "profit": -0.20, "drawdown": 0.40},
        },
    ]

    assert evaluate_parameter_stability(baseline, stable_neighbors, stability)["passed"] is True
    assert evaluate_parameter_stability(baseline, unstable_neighbors, stability)["passed"] is False


def test_best_epoch_selection_uses_loss_and_minimum_trade_gate(tmp_path: Path) -> None:
    result_path = tmp_path / "result.fthypt"
    epochs = [
        {
            "loss": -100.0,
            "params_dict": {"entry_prediction_threshold": 0.003},
            "results_metrics": {
                "total_trades": 5,
                "profit_total": 0.50,
                "max_drawdown_account": 0.01,
            },
        },
        {
            "loss": -2.0,
            "params_dict": {"entry_prediction_threshold": 0.005},
            "results_metrics": {
                "total_trades": 30,
                "profit_total": 0.08,
                "max_drawdown_account": 0.10,
            },
        },
        {
            "loss": -3.0,
            "params_dict": {"entry_prediction_threshold": 0.006},
            "results_metrics": {
                "total_trades": 25,
                "profit_total": 0.07,
                "max_drawdown_account": 0.11,
            },
        },
    ]
    result_path.write_text(
        "".join(json.dumps(epoch) + "\n" for epoch in epochs),
        encoding="utf-8",
    )

    selected = select_best_epoch(
        result_path,
        parameter="entry_prediction_threshold",
        min_trades=20,
    )

    assert selected["params_dict"]["entry_prediction_threshold"] == 0.006
    assert selected["loss"] == -3.0
