from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "ai_platform/configs/rl_v2_training_research.json"
DESCRIPTOR_PATH = (
    ROOT / "ai_platform/experimental_model_research/rl-v2-training-configuration-v1.json"
)
PREFLIGHT_PATH = ROOT / "ai_platform/experimental_model_research/rl-v2-execution-preflight-v1.json"
RUNTIME_PATH = ROOT / "ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json"
MODEL_PATH = ROOT / "ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py"
STRATEGY_PATH = ROOT / "ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py"

FORBIDDEN_CONFIG_KEYS = {
    "timerange",
    "train_period_days",
    "backtest_period_days",
    "live_retrain_hours",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()


def _called_names(function: ast.FunctionDef) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            names.add(node.func.id)
    return names


def _find_method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise AssertionError(f"Missing {class_name}.{method_name}")


def test_config_is_research_only_spot_and_stopped() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["dry_run"] is True
    assert config["trading_mode"] == "spot"
    assert config["initial_state"] == "stopped"
    assert config["force_entry_enable"] is False
    assert config["exchange"]["key"] == ""
    assert config["exchange"]["secret"] == ""
    assert config["exchange"]["pair_whitelist"] == ["BTC/USDT", "ETH/USDT"]


def test_config_binds_exact_frozen_rl_v2_runtime() -> None:
    config = _load_json(CONFIG_PATH)
    freqai = config["freqai"]
    rl_config = freqai["rl_config"]

    assert config["freqaimodel"] == "DesiredPositionReinforcementLearner"
    assert config["freqaimodel_path"] == "ai_platform/freqaimodels"
    assert config["strategy"] == "AiDesiredPositionRLResearchStrategy"
    assert config["strategy_path"] == "ai_platform/strategies"
    assert freqai["identifier"] == "ai-platform-rl-v2-training-research-v1"
    assert rl_config["model_type"] == "PPO"
    assert rl_config["policy_type"] == "MlpPolicy"
    assert rl_config["add_state_info"] is False
    assert rl_config["randomize_starting_position"] is False


def test_config_contains_no_execution_geometry_or_reward_redefinition() -> None:
    config = _load_json(CONFIG_PATH)
    all_keys = _collect_keys(config)

    assert FORBIDDEN_CONFIG_KEYS.isdisjoint(all_keys)
    assert config["freqai"]["rl_config"]["model_reward_parameters"] == {}


def test_descriptor_matches_config_and_parent_contracts() -> None:
    config = _load_json(CONFIG_PATH)
    descriptor = _load_json(DESCRIPTOR_PATH)
    preflight = _load_json(PREFLIGHT_PATH)
    runtime = _load_json(RUNTIME_PATH)

    assert descriptor["configuration_id"] == "rl-v2-training-configuration-v1"
    assert descriptor["config_path"] == "ai_platform/configs/rl_v2_training_research.json"
    assert descriptor["parent_execution_preflight"]["preflight_id"] == preflight["preflight_id"]
    assert descriptor["parent_runtime_integration"]["integration_id"] == runtime["integration_id"]

    binding = descriptor["runtime_binding"]
    assert binding["freqai_model"] == config["freqaimodel"]
    assert binding["strategy"] == config["strategy"]
    assert binding["model_type"] == config["freqai"]["rl_config"]["model_type"]
    assert binding["policy_type"] == config["freqai"]["rl_config"]["policy_type"]
    assert binding["trading_mode"] == config["trading_mode"]
    assert binding["dry_run"] == config["dry_run"]
    assert binding["initial_state"] == config["initial_state"]
    assert binding["can_short"] is False


def test_descriptor_fixed_training_surface_matches_config() -> None:
    config = _load_json(CONFIG_PATH)
    descriptor = _load_json(DESCRIPTOR_PATH)
    fixed = descriptor["fixed_training_surface"]
    config_rl = config["freqai"]["rl_config"]

    assert fixed["performance_tuned"] is False
    assert fixed["hyperparameter_search_performed"] is False
    assert fixed["model_training_parameters"] == config["freqai"]["model_training_parameters"]
    for key, value in fixed["rl_config"].items():
        assert config_rl[key] == value
    assert fixed["rl_config"]["model_reward_parameters"] == {}


def test_descriptor_freezes_desired_position_semantics_and_isolation() -> None:
    descriptor = _load_json(DESCRIPTOR_PATH)
    semantic = descriptor["semantic_binding"]
    scope = descriptor["scope"]
    isolation = descriptor["isolation"]

    assert semantic["action_space"] == {"0": "target_flat", "1": "target_long"}
    assert semantic["action_space_size"] == 2
    assert semantic["long_only"] is True
    assert semantic["short_actions_present"] is False
    assert semantic["policy_requires_hidden_current_position"] is False
    assert semantic["reward_constants_redefined_in_config"] is False

    assert scope["committed_training_configuration_allowed"] is True
    for key, value in scope.items():
        if key != "committed_training_configuration_allowed":
            assert value is False, key

    assert isolation["consumed_historical_oos"] == {
        "timerange": "20260501-20260630",
        "usage": "forbidden",
    }
    assert isolation["protected_final_holdout"] == {
        "timerange": "20260801-20260930",
        "usage": "forbidden",
    }
    assert isolation["frozen_entry_prediction_threshold"] == 0.006
    assert isolation["frozen_exit_prediction_threshold"] == -0.009
    assert isolation["phase6_authoritative_selected_model"] is None
    assert isolation["phase6_member"] is False
    assert isolation["pytorch_rl_ranking_allowed"] is False


def test_runtime_source_still_delegates_transition_and_reward() -> None:
    tree = ast.parse(MODEL_PATH.read_text(encoding="utf-8"))
    transition_method = _find_method(tree, "DesiredPositionEnvironment", "_transition")
    reward_method = _find_method(tree, "DesiredPositionEnvironment", "calculate_reward")

    assert "desired_position_transition" in _called_names(transition_method)
    assert "reference_reward" in _called_names(reward_method)


def test_strategy_source_has_no_short_signal_surface() -> None:
    source = STRATEGY_PATH.read_text(encoding="utf-8")

    assert "enter_short" not in source
    assert "exit_short" not in source
    assert "freqai_rl_v2_target_long" in source
    assert "freqai_rl_v2_target_flat" in source
