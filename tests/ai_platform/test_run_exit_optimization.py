import json
from pathlib import Path

import pytest
from ai_platform.scripts.run_exit_optimization import (
    CONSUMED_HOLDOUT,
    EXPECTED_TRAINING,
    EXPECTED_TUNING,
    FROZEN_ENTRY,
    ExitOptimizationError,
    exit_selection_identity,
    load_exit_plan,
    validate_exit_repository,
    write_sell_parameter_file,
)
from ai_platform.scripts.run_experiment import load_manifest, validate_research_config
from ai_platform.scripts.run_optimization import build_hyperopt_command
from ai_platform.scripts.run_validation import load_validation_plan
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "ai_platform/optimization/phase5-exit-thresholds-v1.json"
SCHEMA_PATH = ROOT / "ai_platform/optimization/exit-schema-v1.json"
MANIFEST_PATH = ROOT / "ai_platform/experiments/phase5-exit-v1.json"
VALIDATION_PATH = ROOT / "ai_platform/validation/baseline-validation-v1.json"
CONFIG_PATH = ROOT / "ai_platform/configs/freqai-baseline.example.json"
STRATEGY_PATH = ROOT / "ai_platform/strategies"
STRATEGY_FILE = STRATEGY_PATH / "AiPhase52ExitStrategy.py"


def test_exit_optimization_plan_matches_schema() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(plan)


def test_phase52_contract_freezes_entry_and_blocks_final_validation() -> None:
    plan = load_exit_plan(PLAN_PATH)

    assert plan["training"]["timerange"] == EXPECTED_TRAINING
    assert plan["tuning"]["timerange"] == EXPECTED_TUNING
    assert plan["consumed_holdout_reference"]["timerange"] == CONSUMED_HOLDOUT
    assert plan["fixed_parameters"] == {"entry_prediction_threshold": FROZEN_ENTRY}
    assert plan["future_final_holdout"] == {
        "status": "pending_new_unseen_window",
        "final_validation_authorized": False,
    }


def test_exit_hyperopt_uses_sell_space_and_never_consumed_holdout(tmp_path: Path) -> None:
    plan = load_exit_plan(PLAN_PATH)
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
    assert EXPECTED_TUNING in command
    assert CONSUMED_HOLDOUT not in command
    assert command[command.index("--spaces") + 1] == "sell"
    assert "buy" not in command
    assert "roi" not in command
    assert "stoploss" not in command
    assert "protection" not in command


def test_phase52_repository_contract_matches_phase51_evidence() -> None:
    plan = load_exit_plan(PLAN_PATH)
    manifest = load_manifest(MANIFEST_PATH)
    validation = load_validation_plan(VALIDATION_PATH)
    config = validate_research_config(CONFIG_PATH)

    validate_exit_repository(plan, manifest, validation, config)


def test_exit_plan_rejects_entry_threshold_drift(tmp_path: Path) -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    plan["fixed_parameters"]["entry_prediction_threshold"] = 0.007
    path = tmp_path / "exit-plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(ExitOptimizationError, match=r"frozen at 0\.006"):
        load_exit_plan(path)


def test_exit_plan_rejects_future_holdout_authorization(tmp_path: Path) -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    plan["future_final_holdout"]["final_validation_authorized"] = True
    path = tmp_path / "exit-plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(ExitOptimizationError, match="not yet authorized"):
        load_exit_plan(path)


def test_sell_parameter_file_uses_only_sell_group(tmp_path: Path) -> None:
    strategy_dir = tmp_path / "strategy"
    write_sell_parameter_file(
        strategy_dir,
        STRATEGY_FILE,
        "AiPhase52ExitStrategy",
        "exit_prediction_threshold",
        -0.003,
    )
    payload = json.loads((strategy_dir / "AiPhase52ExitStrategy.json").read_text(encoding="utf-8"))

    assert payload["params"] == {"sell": {"exit_prediction_threshold": -0.003}}
    assert "buy" not in payload["params"]


def test_exit_selection_identity_is_deterministic_and_parameter_sensitive() -> None:
    plan = load_exit_plan(PLAN_PATH)
    first = exit_selection_identity(
        plan,
        git_commit="a" * 40,
        parameter="exit_prediction_threshold",
        value=-0.003,
    )
    second = exit_selection_identity(
        plan,
        git_commit="a" * 40,
        parameter="exit_prediction_threshold",
        value=-0.003,
    )
    changed = exit_selection_identity(
        plan,
        git_commit="a" * 40,
        parameter="exit_prediction_threshold",
        value=-0.002,
    )

    assert first == second
    assert first.startswith("opt-")
    assert first != changed
