import ast
import json
from pathlib import Path

from ai_platform.scripts.rl_v2_synthetic_reference import (
    DesiredPosition,
    PositionState,
    RLV2ObservabilityAccumulator,
    Transition,
    desired_position_transition,
    reference_reward,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DESCRIPTOR_PATH = (
    REPO_ROOT
    / "ai_platform"
    / "experimental_model_research"
    / "rl-v2-runtime-integration-v1.json"
)
MODEL_PATH = REPO_ROOT / "ai_platform" / "freqaimodels" / "DesiredPositionReinforcementLearner.py"
STRATEGY_PATH = REPO_ROOT / "ai_platform" / "strategies" / "AiDesiredPositionRLResearchStrategy.py"


def _descriptor() -> dict:
    return json.loads(DESCRIPTOR_PATH.read_text(encoding="utf-8"))


def test_runtime_descriptor_freezes_two_action_desired_position_contract() -> None:
    descriptor = _descriptor()

    assert descriptor["integration_id"] == "rl-v2-runtime-integration-v1"
    assert descriptor["status"] == "runtime_integration_only"
    assert descriptor["runtime"] == {
        "backend_family": "stable_baselines3",
        "model_type": "PPO",
        "policy_type": "MlpPolicy",
        "market_semantics": "long_only_spot",
        "freqai_model": "DesiredPositionReinforcementLearner",
        "environment": "DesiredPositionEnvironment",
        "strategy": "AiDesiredPositionRLResearchStrategy",
    }
    assert descriptor["action_semantics"] == {
        "type": "desired_position",
        "actions": {"0": "target_flat", "1": "target_long"},
        "action_space_size": 2,
        "training_inference_meaning_identical": True,
        "policy_requires_hidden_current_position": False,
        "short_actions_allowed": False,
    }


def test_runtime_descriptor_preserves_non_execution_and_isolation_boundaries() -> None:
    descriptor = _descriptor()
    scope = descriptor["scope"]

    assert scope["runtime_adapter_allowed"] is True
    assert scope["strategy_adapter_allowed"] is True
    for key in (
        "training_config_allowed",
        "experiment_manifest_allowed",
        "run_request_allowed",
        "training_allowed",
        "model_fitting_allowed",
        "backtest_allowed",
        "market_data_download_allowed",
        "historical_evaluation_allowed",
        "strict_oos_execution_allowed",
        "future_evaluation_window_declaration_allowed",
        "hyperopt_allowed",
        "reward_search_allowed",
        "feature_search_allowed",
        "hyperparameter_search_allowed",
        "promotion_allowed",
        "profitability_claim_allowed",
        "superiority_claim_allowed",
        "live_trading_allowed",
    ):
        assert scope[key] is False

    isolation = descriptor["isolation"]
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
    assert isolation["pytorch_rl_ranking_allowed"] is False


def test_runtime_binding_points_to_canonical_synthetic_reference() -> None:
    binding = _descriptor()["binding"]
    transition = "ai_platform.scripts.rl_v2_synthetic_reference.desired_position_transition"
    reward = "ai_platform.scripts.rl_v2_synthetic_reference.reference_reward"
    action_label = "ai_platform.scripts.rl_v2_synthetic_reference.desired_position_label"
    obs = "ai_platform.scripts.rl_v2_synthetic_reference.RLV2ObservabilityAccumulator"

    assert binding["transition_function"] == transition
    assert binding["reward_function"] == reward
    assert binding["action_label_function"] == action_label
    assert binding["observability_accumulator"] == obs
    assert binding["reward_constants_redefined"] is False
    assert binding["action_semantics_redefined"] is False


def test_desired_position_actions_remain_valid_semantics_in_both_position_states() -> None:
    flat_hold = desired_position_transition(PositionState.FLAT, DesiredPosition.TARGET_FLAT)
    flat_enter = desired_position_transition(PositionState.FLAT, DesiredPosition.TARGET_LONG)
    long_hold = desired_position_transition(PositionState.LONG, DesiredPosition.TARGET_LONG)
    long_exit = desired_position_transition(PositionState.LONG, DesiredPosition.TARGET_FLAT)

    assert flat_hold is Transition.HOLD_FLAT
    assert flat_enter is Transition.ENTER_LONG
    assert long_hold is Transition.HOLD_LONG
    assert long_exit is Transition.EXIT_LONG


def test_runtime_reward_contract_uses_frozen_reference_for_valid_and_invalid_actions() -> None:
    remain_flat = reference_reward(
        PositionState.FLAT,
        DesiredPosition.TARGET_FLAT,
        unrealized_profit=0.0,
        duration_steps=0,
    )
    enter_long = reference_reward(
        PositionState.FLAT,
        DesiredPosition.TARGET_LONG,
        unrealized_profit=0.0,
        duration_steps=0,
    )
    invalid = reference_reward(
        PositionState.FLAT,
        99,
        unrealized_profit=0.0,
        duration_steps=0,
    )

    assert remain_flat == -0.01
    assert enter_long == 0.0
    assert invalid == -1.0


def test_model_adapter_source_binds_environment_to_canonical_functions() -> None:
    source = MODEL_PATH.read_text(encoding="utf-8")
    ast.parse(source)

    assert "self.action_space = spaces.Discrete(len(DesiredPosition))" in source
    assert "self.actions = DesiredPosition" in source
    assert "desired_position_transition(self._position_state(), action)" in source
    assert "return reference_reward(" in source
    assert "desired_position_label(action)" in source
    assert "return RLV2ObservabilityAccumulator(pairs)" in source
    assert "class DesiredPositionReinforcementLearner(ReinforcementLearner)" in source
    assert "MyRLEnv = DesiredPositionEnvironment" in source


def test_strategy_adapter_maps_prediction_gate_to_desired_position_intents_only() -> None:
    source = STRATEGY_PATH.read_text(encoding="utf-8")
    ast.parse(source)

    assert '(dataframe["do_predict"] == 1)' in source
    assert 'dataframe["&-action"] == DesiredPosition.TARGET_LONG.value' in source
    assert 'dataframe["&-action"] == DesiredPosition.TARGET_FLAT.value' in source
    assert '"enter_long"' in source
    assert '"exit_long"' in source
    assert "enter_short" not in source
    assert "exit_short" not in source
    assert "can_short = False" in source


def test_observability_binding_preserves_zero_buckets_and_separate_layers() -> None:
    accumulator = RLV2ObservabilityAccumulator(["BTC/USDT", "ETH/USDT"])
    snapshot = accumulator.snapshot()

    for pair in snapshot["pairs"].values():
        assert pair["actions"] == {"target_flat": 0, "target_long": 0}
        assert pair["do_predict"] == {"accepted": 0, "rejected": 0}
        assert pair["pre_trade_signals"] == {"entry": 0, "exit": 0}
    assert snapshot["raw_backtest_trades"] == 0
    assert snapshot["strict_oos"] == {"input": 0, "included": 0, "excluded": 0}
    assert _descriptor()["observability"]["runtime_counts_fabricated_by_this_task"] is False
