#!/usr/bin/env python3
"""Run the bounded non-result-producing RL-v2 execution preflight."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, cast


REPO_ROOT = Path(__file__).resolve().parents[2]
DESCRIPTOR_PATH = (
    REPO_ROOT / "ai_platform" / "experimental_model_research" / "rl-v2-execution-preflight-v1.json"
)
PAIR = "BTC/USDT"


class RLV2ExecutionPreflightError(RuntimeError):
    """Raised when the RL-v2 execution preflight fails closed."""


def _read_descriptor(path: Path = DESCRIPTOR_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RLV2ExecutionPreflightError(f"Unable to read preflight descriptor: {exc}") from exc
    if not isinstance(payload, dict):
        raise RLV2ExecutionPreflightError("Preflight descriptor must contain a JSON object")
    return payload


def validate_descriptor(path: Path = DESCRIPTOR_PATH) -> dict[str, Any]:
    descriptor = _read_descriptor(path)
    if descriptor.get("preflight_id") != "rl-v2-execution-preflight-v1":
        raise RLV2ExecutionPreflightError("Unexpected RL-v2 execution preflight identity")

    runtime = descriptor.get("runtime_resolution", {})
    expected_runtime = {
        "freqai_model": "DesiredPositionReinforcementLearner",
        "strategy": "AiDesiredPositionRLResearchStrategy",
        "model_type": "PPO",
        "policy_type": "MlpPolicy",
        "trading_mode": "spot",
        "dry_run": True,
        "can_short": False,
    }
    for key, expected in expected_runtime.items():
        if runtime.get(key) != expected:
            raise RLV2ExecutionPreflightError(f"Runtime descriptor drifted for {key}")

    actions = descriptor.get("semantic_binding", {}).get("action_space", {})
    if actions != {"0": "target_flat", "1": "target_long"}:
        raise RLV2ExecutionPreflightError("Desired-position action contract drifted")

    scope = descriptor.get("scope", {})
    required_false = (
        "training_config_commit_allowed",
        "experiment_manifest_allowed",
        "run_request_allowed",
        "training_allowed",
        "model_fitting_allowed",
        "backtest_allowed",
        "market_data_download_allowed",
        "exchange_data_access_allowed",
        "historical_evaluation_window_selection_allowed",
        "future_evaluation_window_selection_allowed",
        "strict_oos_execution_allowed",
        "performance_evaluation_allowed",
        "promotion_allowed",
        "live_trading_allowed",
    )
    if any(scope.get(key) is not False for key in required_false):
        raise RLV2ExecutionPreflightError("Preflight descriptor authorizes result-producing work")
    return descriptor


def build_ephemeral_config(user_data_dir: Path) -> dict[str, Any]:
    """Build the smallest construction-only config without execution geometry."""
    return {
        "dry_run": True,
        "trading_mode": "spot",
        "stake_currency": "USDT",
        "stake_amount": 100,
        "max_open_trades": 1,
        "timeframe": "15m",
        "user_data_dir": user_data_dir,
        "exchange": {
            "name": "kraken",
            "key": "",
            "secret": "",
            "pair_whitelist": [PAIR],
            "pair_blacklist": [],
        },
        "freqaimodel": "DesiredPositionReinforcementLearner",
        "freqaimodel_path": str(REPO_ROOT / "ai_platform" / "freqaimodels"),
        "strategy": "AiDesiredPositionRLResearchStrategy",
        "strategy_path": str(REPO_ROOT / "ai_platform" / "strategies"),
        "freqai": {
            "enabled": True,
            "identifier": "rl-v2-execution-preflight-v1",
            "save_backtest_models": False,
            "activate_tensorboard": False,
            "continual_learning": False,
            "feature_parameters": {
                "include_timeframes": ["15m"],
                "include_corr_pairlist": [],
                "include_shifted_candles": 0,
                "indicator_periods_candles": [14],
                "DI_threshold": 0,
                "principal_component_analysis": False,
                "use_SVM_to_remove_outliers": False,
                "plot_feature_importances": 0,
            },
            "data_split_parameters": {
                "test_size": 0.0,
                "shuffle": False,
            },
            "model_training_parameters": {
                "seed": 42,
            },
            "rl_config": {
                "model_type": "PPO",
                "policy_type": "MlpPolicy",
                "cpu_count": 1,
                "add_state_info": False,
                "max_training_drawdown_pct": 0.2,
                "training_fee": 0.002,
                "model_reward_parameters": {
                    "rr": 1.0,
                    "profit_aim": 0.01,
                },
            },
        },
    }


def _lookup(config: dict[str, Any], dotted_path: str) -> Any:
    value: Any = config
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise RLV2ExecutionPreflightError(f"Missing required configuration key: {dotted_path}")
        value = value[part]
    return value


def _path_exists(config: dict[str, Any], dotted_path: str) -> bool:
    value: Any = config
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    return True


def validate_ephemeral_config(
    config: dict[str, Any],
    descriptor: dict[str, Any] | None = None,
) -> None:
    descriptor = descriptor or validate_descriptor()
    surface = descriptor["ephemeral_configuration_surface"]
    for dotted_path in surface["top_level_required"]:
        _lookup(config, dotted_path)
    for key in surface["freqai_required"]:
        _lookup(config, f"freqai.{key}")
    for key in surface["rl_config_required"]:
        _lookup(config, f"freqai.rl_config.{key}")
    for dotted_path in surface["forbidden_execution_geometry"]:
        if _path_exists(config, dotted_path):
            raise RLV2ExecutionPreflightError(
                f"Execution geometry is forbidden in RL-v2 preflight config: {dotted_path}"
            )

    if config.get("dry_run") is not True:
        raise RLV2ExecutionPreflightError("RL-v2 execution preflight requires dry_run=true")
    if config.get("trading_mode") != "spot":
        raise RLV2ExecutionPreflightError("RL-v2 execution preflight requires spot trading mode")
    rl_config = config["freqai"]["rl_config"]
    if rl_config.get("model_type") != "PPO":
        raise RLV2ExecutionPreflightError("RL-v2 execution preflight requires PPO")
    if rl_config.get("policy_type") != "MlpPolicy":
        raise RLV2ExecutionPreflightError("RL-v2 execution preflight requires MlpPolicy")


def _check_transition_binding(position_state: Any, transition: Any, transition_fn: Any) -> None:
    expected = {
        (position_state.FLAT, 0): transition.HOLD_FLAT,
        (position_state.FLAT, 1): transition.ENTER_LONG,
        (position_state.LONG, 0): transition.EXIT_LONG,
        (position_state.LONG, 1): transition.HOLD_LONG,
    }
    for key, expected_transition in expected.items():
        if transition_fn(*key) is not expected_transition:
            raise RLV2ExecutionPreflightError(
                "Canonical desired-position transition binding drifted"
            )


def _check_strategy_mapping(config: dict[str, Any], pandas: Any, resolver: Any) -> Any:
    strategy = resolver.load_strategy(copy.deepcopy(config))
    if strategy.__class__.__name__ != "AiDesiredPositionRLResearchStrategy" or strategy.can_short:
        raise RLV2ExecutionPreflightError("Resolved RL-v2 strategy or long-only binding drifted")

    frame = pandas.DataFrame(
        {
            "do_predict": [1, 1, 0],
            "&-action": [1, 0, 1],
            "volume": [1.0, 1.0, 1.0],
        }
    )
    frame = strategy.populate_entry_trend(frame, metadata={"pair": PAIR})
    frame = strategy.populate_exit_trend(frame, metadata={"pair": PAIR})
    if frame["enter_long"].fillna(0).tolist() != [1, 0, 0]:
        raise RLV2ExecutionPreflightError("target_long strategy mapping drifted")
    if frame["exit_long"].fillna(0).tolist() != [0, 1, 0]:
        raise RLV2ExecutionPreflightError("target_flat strategy mapping drifted")
    return strategy


def _check_observability(strategy: Any) -> None:
    snapshot = strategy.new_observability_accumulator([PAIR]).snapshot()
    expected_actions = {"target_flat": 0, "target_long": 0}
    if snapshot["pairs"][PAIR]["actions"] != expected_actions:
        raise RLV2ExecutionPreflightError(
            "Zero-count desired-position observability buckets drifted"
        )
    expected_oos = {"input": 0, "included": 0, "excluded": 0}
    if snapshot["raw_backtest_trades"] != 0 or snapshot["strict_oos"] != expected_oos:
        raise RLV2ExecutionPreflightError("Preflight fabricated trade or strict-OOS counts")


def _runtime_checks(config: dict[str, Any]) -> dict[str, Any]:
    import pandas as pd

    from ai_platform.freqaimodels.DesiredPositionReinforcementLearner import (
        DesiredPositionActions,
        DesiredPositionEnvironment,
    )
    from ai_platform.scripts.rl_v2_synthetic_reference import (
        PositionState,
        Transition,
        desired_position_transition,
    )
    from freqtrade.resolvers.freqaimodel_resolver import FreqaiModelResolver
    from freqtrade.resolvers.strategy_resolver import StrategyResolver

    learner = cast(Any, FreqaiModelResolver.load_freqaimodel(config))
    if learner.__class__.__name__ != "DesiredPositionReinforcementLearner":
        raise RLV2ExecutionPreflightError("FreqAI resolver returned an unexpected RL-v2 model")
    learner.live = False
    learner.can_short = False
    if learner.MODELCLASS.__name__ != "PPO" or learner.policy_type != "MlpPolicy":
        raise RLV2ExecutionPreflightError("Resolved RL-v2 backend or policy drifted")
    if learner.MyRLEnv.__name__ != DesiredPositionEnvironment.__name__:
        raise RLV2ExecutionPreflightError("Resolved RL-v2 environment binding drifted")

    features = pd.DataFrame(
        {
            "%feature_a": [0.0, 0.1, 0.2, 0.3],
            "%feature_b": [0.3, 0.2, 0.1, 0.0],
        }
    )
    prices = pd.DataFrame(
        {
            "open": [100.0, 100.1, 100.2, 100.3],
            "high": [100.2, 100.3, 100.4, 100.5],
            "low": [99.8, 99.9, 100.0, 100.1],
            "close": [100.1, 100.2, 100.3, 100.4],
        }
    )
    learner.df_raw = prices.copy()
    environment = learner.MyRLEnv(
        df=features,
        prices=prices,
        **copy.deepcopy(learner.pack_env_dict(PAIR)),
    )
    actions = {
        int(DesiredPositionActions.Target_flat.value): "target_flat",
        int(DesiredPositionActions.Target_long.value): "target_long",
    }
    if actions != {0: "target_flat", 1: "target_long"}:
        raise RLV2ExecutionPreflightError("Runtime desired-position enum drifted")
    if environment.action_space.n != 2 or environment.action_masks() != [True, True]:
        raise RLV2ExecutionPreflightError(
            "Runtime environment action space is not exactly two actions"
        )

    _check_transition_binding(PositionState, Transition, desired_position_transition)
    strategy = _check_strategy_mapping(config, pd, StrategyResolver)
    _check_observability(strategy)

    return {
        "model": learner.__class__.__name__,
        "strategy": strategy.__class__.__name__,
        "backend": learner.MODELCLASS.__name__,
        "policy": learner.policy_type,
        "actions": actions,
        "action_space_size": int(environment.action_space.n),
        "dry_run": True,
        "trading_mode": "spot",
        "training_performed": False,
        "model_fitting_performed": False,
        "backtest_performed": False,
        "market_data_accessed": False,
        "evaluation_window_selected": False,
        "historical_oos_scored": False,
        "final_holdout_used": False,
        "performance_scored": False,
    }


def run_preflight() -> dict[str, Any]:
    descriptor = validate_descriptor()
    with tempfile.TemporaryDirectory(prefix="ai-platform-rl-v2-preflight-") as tmp:
        config = build_ephemeral_config(Path(tmp))
        validate_ephemeral_config(config, descriptor)
        runtime = _runtime_checks(config)
    return {
        "preflight_id": descriptor["preflight_id"],
        "status": "pass",
        "runtime": runtime,
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
        "phase6_member": False,
        "promotion_allowed": False,
        "profitability_claim_allowed": False,
        "superiority_claim_allowed": False,
    }


def main() -> int:
    try:
        result = run_preflight()
    except RLV2ExecutionPreflightError as exc:
        print(f"RL-v2 execution preflight failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
