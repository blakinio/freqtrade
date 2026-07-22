import ast
import json
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_synthetic_reference import (
    DesiredPosition,
    PositionState,
    Transition,
    desired_position_transition,
    reference_reward,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DESCRIPTOR = (
    REPO_ROOT
    / "ai_platform"
    / "experimental_model_research"
    / "rl-v2-runtime-integration-v1.json"
)
SYNTHETIC_DESCRIPTOR = (
    REPO_ROOT
    / "ai_platform"
    / "experimental_model_research"
    / "rl-v2-synthetic-implementation-v1.json"
)
MODEL_SOURCE = REPO_ROOT / "ai_platform" / "freqaimodels" / "DesiredPositionReinforcementLearner.py"
STRATEGY_SOURCE = REPO_ROOT / "ai_platform" / "strategies" / "AiDesiredPositionRLResearchStrategy.py"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _class_node(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"Missing class {name}")


def _method_node(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Missing method {class_node.name}.{name}")


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        if isinstance(child.func, ast.Name):
            names.add(child.func.id)
        elif isinstance(child.func, ast.Attribute):
            names.add(child.func.attr)
    return names


def test_runtime_descriptor_is_bound_to_frozen_synthetic_reference() -> None:
    runtime = _read_json(RUNTIME_DESCRIPTOR)
    synthetic = _read_json(SYNTHETIC_DESCRIPTOR)

    assert runtime["integration_id"] == "rl-v2-runtime-integration-v1"
    assert runtime["status"] == "runtime_integration_only"
    assert runtime["synthetic_reference"]["implementation_id"] == synthetic["implementation_id"]
    assert runtime["action_semantics"]["actions"] == synthetic["action_semantics"]["actions"]
    assert runtime["action_semantics"]["action_space_size"] == 2
    assert runtime["action_semantics"]["short_actions_present"] is False
    assert runtime["action_semantics"]["policy_requires_hidden_current_position"] is False
    assert runtime["reward_binding"]["redefines_reward_constants"] is False
    assert runtime["reward_binding"]["future_market_information_used"] is False


def test_runtime_descriptor_freezes_backend_and_authorizes_no_execution() -> None:
    runtime = _read_json(RUNTIME_DESCRIPTOR)

    assert runtime["runtime_binding"]["backend_family"] == (
        "stable_baselines3_via_freqai_reinforcement_learner"
    )
    assert runtime["runtime_binding"]["algorithm_family"] == "PPO"
    assert runtime["runtime_binding"]["policy_family"] == "MlpPolicy"

    scope = runtime["scope"]
    assert scope["runtime_adapter_implementation_allowed"] is True
    assert scope["static_binding_tests_allowed"] is True
    assert scope["synthetic_binding_tests_allowed"] is True
    for forbidden in (
        "training_config_allowed",
        "experiment_manifest_allowed",
        "run_request_allowed",
        "training_allowed",
        "model_fitting_allowed",
        "backtest_allowed",
        "historical_evaluation_allowed",
        "market_data_download_allowed",
        "hyperopt_allowed",
        "reward_parameter_search_allowed",
        "feature_search_allowed",
        "hyperparameter_search_allowed",
        "strict_oos_execution_allowed",
        "performance_evaluation_allowed",
        "future_evaluation_window_selection_allowed",
        "promotion_allowed",
        "live_trading_allowed",
    ):
        assert scope[forbidden] is False


def test_runtime_descriptor_preserves_evaluation_and_phase_isolation() -> None:
    isolation = _read_json(RUNTIME_DESCRIPTOR)["isolation"]

    assert isolation["consumed_historical_oos"] == {
        "timerange": "20260501-20260630",
        "usage": "forbidden",
    }
    assert isolation["protected_final_holdout"] == {
        "timerange": "20260801-20260930",
        "usage": "forbidden",
    }
    assert isolation["future_evaluation_window_selected"] is False
    assert isolation["frozen_entry_prediction_threshold"] == 0.006
    assert isolation["frozen_exit_prediction_threshold"] == -0.009
    assert isolation["phase6_authoritative_selected_model"] is None
    assert isolation["phase6_member"] is False


def test_model_adapter_statically_reuses_canonical_transition_and_reward() -> None:
    source = _read_source(MODEL_SOURCE)
    tree = ast.parse(source)
    environment = _class_node(tree, "DesiredPositionEnvironment")

    imported_reference_names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == (
            "ai_platform.scripts.rl_v2_synthetic_reference"
        ):
            imported_reference_names.update(alias.name for alias in node.names)

    assert {
        "DesiredPosition",
        "PositionState",
        "Transition",
        "desired_position_label",
        "desired_position_transition",
        "reference_reward",
    }.issubset(imported_reference_names)

    set_action_space = _method_node(environment, "set_action_space")
    transition = _method_node(environment, "_transition")
    calculate_reward = _method_node(environment, "calculate_reward")
    is_valid = _method_node(environment, "_is_valid")

    assert "Discrete" in _called_names(set_action_space)
    assert "desired_position_transition" in _called_names(transition)
    assert "reference_reward" in _called_names(calculate_reward)
    assert "desired_position_label" in _called_names(is_valid)
    assert "self._position" not in ast.unparse(is_valid)
    assert "Positions.Short" not in source
    assert "Long_enter" not in source
    assert "Long_exit" not in source


def test_model_adapter_two_actions_have_position_independent_meaning() -> None:
    source = _read_source(MODEL_SOURCE)

    assert "Target_flat = DesiredPosition.TARGET_FLAT.value" in source
    assert "Target_long = DesiredPosition.TARGET_LONG.value" in source
    assert "spaces.Discrete(len(DesiredPositionActions))" in source

    for position in (PositionState.FLAT, PositionState.LONG):
        assert desired_position_transition(position, DesiredPosition.TARGET_FLAT) in (
            Transition.HOLD_FLAT,
            Transition.EXIT_LONG,
        )
        assert desired_position_transition(position, DesiredPosition.TARGET_LONG) in (
            Transition.ENTER_LONG,
            Transition.HOLD_LONG,
        )


def test_runtime_reward_binding_matches_frozen_reference_cases() -> None:
    assert reference_reward(
        PositionState.FLAT,
        DesiredPosition.TARGET_FLAT,
        unrealized_profit=0.0,
        duration_steps=0,
    ) == pytest.approx(-0.01)
    assert reference_reward(
        PositionState.FLAT,
        DesiredPosition.TARGET_LONG,
        unrealized_profit=0.0,
        duration_steps=0,
    ) == pytest.approx(0.0)
    assert reference_reward(
        PositionState.LONG,
        DesiredPosition.TARGET_LONG,
        unrealized_profit=10.0,
        duration_steps=1_000_000,
    ) == pytest.approx(0.01)
    assert reference_reward(
        PositionState.LONG,
        DesiredPosition.TARGET_FLAT,
        unrealized_profit=10.0,
        duration_steps=1,
    ) == pytest.approx(0.05)
    assert reference_reward(
        PositionState.FLAT,
        99,
        unrealized_profit=0.0,
        duration_steps=0,
    ) == pytest.approx(-1.0)


def test_strategy_statically_maps_target_long_to_entry_and_target_flat_to_exit() -> None:
    source = _read_source(STRATEGY_SOURCE)
    tree = ast.parse(source)
    strategy = _class_node(tree, "AiDesiredPositionRLResearchStrategy")

    entry = ast.unparse(_method_node(strategy, "populate_entry_trend"))
    exit_ = ast.unparse(_method_node(strategy, "populate_exit_trend"))

    assert 'dataframe["do_predict"] == 1' in entry
    assert "DesiredPosition.TARGET_LONG.value" in entry
    assert 'dataframe["do_predict"] == 1' in exit_
    assert "DesiredPosition.TARGET_FLAT.value" in exit_
    assert "TARGET_FLAT.value" not in entry
    assert "TARGET_LONG.value" not in exit_
    assert "short" not in entry.lower()
    assert "short" not in exit_.lower()


def test_strategy_observability_binding_reuses_canonical_counter_vocabulary() -> None:
    source = _read_source(STRATEGY_SOURCE)
    tree = ast.parse(source)
    strategy = _class_node(tree, "AiDesiredPositionRLResearchStrategy")
    observe = _method_node(strategy, "record_prediction_observability")
    called = _called_names(observe)

    assert "RLV2ObservabilityAccumulator" in source
    assert "record_action" in called
    assert "record_do_predict" in called
    assert "record_pre_trade_signal" in called
    assert "set_raw_backtest_trades" not in called
    assert "set_strict_oos_counts" not in called

    observability = _read_json(RUNTIME_DESCRIPTOR)["observability_binding"]
    assert observability["action_histogram_includes_zero_count_actions"] is True
    assert observability["do_predict_accepted_rejected_by_pair"] is True
    assert observability["pre_trade_entry_exit_signals_by_pair"] is True
    assert observability["raw_backtest_trade_count"] is True
    assert observability["strict_oos_input_included_excluded_counts"] is True
    assert observability["runtime_counts_fabricated_without_execution"] is False


def test_static_validation_does_not_import_heavy_runtime_modules() -> None:
    ast.parse(_read_source(MODEL_SOURCE))
    ast.parse(_read_source(STRATEGY_SOURCE))

    safety = _read_json(RUNTIME_DESCRIPTOR)["heavy_runtime_safety"]
    assert safety == {
        "freqai_rl_import_required_for_static_tests": False,
        "training_required_for_validation": False,
        "backtest_required_for_validation": False,
        "market_data_required_for_validation": False,
    }
