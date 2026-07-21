import copy
import json
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_synthetic_reference import (
    DESCRIPTOR_PATH,
    FLAT_NEUTRAL_REWARD,
    FLAT_TO_LONG_REWARD,
    INVALID_ACTION_PENALTY,
    LONG_HOLD_PENALTY_CEILING,
    LONG_HOLD_PENALTY_FLOOR,
    DesiredPositionAction,
    RLV2SyntheticReferenceError,
    SyntheticDecisionState,
    SyntheticObservability,
    canonical_rl_v2_synthetic_implementation,
    desired_position,
    inference_desired_position,
    reference_reward,
    training_desired_position,
    validate_rl_v2_synthetic_implementation,
)


def _write_descriptor(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_repository_descriptor_matches_canonical_synthetic_implementation() -> None:
    assert (
        validate_rl_v2_synthetic_implementation(DESCRIPTOR_PATH)
        == canonical_rl_v2_synthetic_implementation()
    )


def test_desired_position_action_semantics_are_position_independent() -> None:
    assert desired_position(DesiredPositionAction.TARGET_FLAT) == "target_flat"
    assert desired_position(DesiredPositionAction.TARGET_LONG) == "target_long"

    for action in DesiredPositionAction:
        assert training_desired_position(action) == inference_desired_position(action)


def test_unknown_action_semantics_fail_closed() -> None:
    with pytest.raises(RLV2SyntheticReferenceError, match="Unknown desired-position action"):
        desired_position(99)


def test_flat_neutral_reward_is_strictly_below_valid_long_target_reward() -> None:
    state = SyntheticDecisionState(position="flat")

    stay_flat = reference_reward(state, DesiredPositionAction.TARGET_FLAT)
    target_long = reference_reward(state, DesiredPositionAction.TARGET_LONG)

    assert stay_flat == FLAT_NEUTRAL_REWARD
    assert target_long == FLAT_TO_LONG_REWARD
    assert stay_flat < target_long


def test_perpetual_flat_neutral_episode_is_not_unpenalized() -> None:
    state = SyntheticDecisionState(position="flat")
    episode_reward = sum(
        reference_reward(state, DesiredPositionAction.TARGET_FLAT) for _ in range(10)
    )

    assert episode_reward < 0.0


def test_invalid_action_is_penalized() -> None:
    state = SyntheticDecisionState(position="flat")

    assert reference_reward(state, 99) == INVALID_ACTION_PENALTY


def test_holding_reward_is_bounded() -> None:
    rewards = [
        reference_reward(
            SyntheticDecisionState(position="long", trade_duration_ratio=ratio),
            DesiredPositionAction.TARGET_LONG,
        )
        for ratio in (-1.0, 0.0, 0.25, 1.0, 2.0)
    ]

    assert all(LONG_HOLD_PENALTY_FLOOR <= reward <= LONG_HOLD_PENALTY_CEILING for reward in rewards)
    assert rewards[0] == LONG_HOLD_PENALTY_CEILING
    assert rewards[-1] == LONG_HOLD_PENALTY_FLOOR


def test_flatten_reward_uses_only_supplied_decision_time_state() -> None:
    profitable = SyntheticDecisionState(position="long", unrealized_profit_pct=0.02)
    losing = SyntheticDecisionState(position="long", unrealized_profit_pct=-0.01)

    assert reference_reward(profitable, DesiredPositionAction.TARGET_FLAT) == 2.0
    assert reference_reward(losing, DesiredPositionAction.TARGET_FLAT) == -1.0


def test_unknown_position_fails_closed() -> None:
    state = SyntheticDecisionState(position="invalid")  # type: ignore[arg-type]

    with pytest.raises(RLV2SyntheticReferenceError, match="Unknown synthetic position"):
        reference_reward(state, DesiredPositionAction.TARGET_FLAT)


def test_observability_snapshot_includes_zero_count_actions_and_sorted_pairs() -> None:
    observability = SyntheticObservability(["ETH/USDT", "BTC/USDT"])

    snapshot = observability.snapshot()

    assert list(snapshot["pairs"]) == ["BTC/USDT", "ETH/USDT"]
    assert snapshot["pairs"]["BTC/USDT"]["actions"] == {"0": 0, "1": 0}
    assert snapshot["pairs"]["ETH/USDT"]["actions"] == {"0": 0, "1": 0}
    json.dumps(snapshot, sort_keys=True)


def test_observability_records_each_required_layer_separately() -> None:
    observability = SyntheticObservability(["BTC/USDT"])
    observability.record_action("BTC/USDT", DesiredPositionAction.TARGET_LONG)
    observability.record_action("BTC/USDT", DesiredPositionAction.TARGET_LONG)
    observability.record_action("BTC/USDT", DesiredPositionAction.TARGET_FLAT)
    observability.record_do_predict("BTC/USDT", accepted=True)
    observability.record_do_predict("BTC/USDT", accepted=False)
    observability.record_pre_trade_signals("BTC/USDT", entry=2, exit=1)
    observability.set_raw_backtest_trades(1)
    observability.set_strict_oos_counts(input_trades=1, included_trades=1, excluded_trades=0)

    snapshot = observability.snapshot()
    pair = snapshot["pairs"]["BTC/USDT"]

    assert pair["actions"] == {"0": 1, "1": 2}
    assert pair["do_predict"] == {"accepted": 1, "rejected": 1}
    assert pair["pre_trade_signals"] == {"entry": 2, "exit": 1}
    assert snapshot["raw_backtest_trades"] == 1
    assert snapshot["strict_oos"] == {"input": 1, "included": 1, "excluded": 0}


def test_observability_rejects_unknown_pairs_and_invalid_counts() -> None:
    observability = SyntheticObservability(["BTC/USDT"])

    with pytest.raises(RLV2SyntheticReferenceError, match="Unknown observability pair"):
        observability.record_action("ETH/USDT", DesiredPositionAction.TARGET_LONG)
    with pytest.raises(RLV2SyntheticReferenceError, match="Signal counts must be non-negative"):
        observability.record_pre_trade_signals("BTC/USDT", entry=-1)
    with pytest.raises(RLV2SyntheticReferenceError, match="Raw backtest trade count"):
        observability.set_raw_backtest_trades(-1)
    with pytest.raises(RLV2SyntheticReferenceError, match="included plus excluded"):
        observability.set_strict_oos_counts(
            input_trades=2,
            included_trades=1,
            excluded_trades=0,
        )


def test_descriptor_rejects_runtime_execution_authorization(tmp_path: Path) -> None:
    payload = copy.deepcopy(canonical_rl_v2_synthetic_implementation())
    payload["scope"]["training_allowed"] = True
    path = tmp_path / "descriptor.json"
    _write_descriptor(path, payload)

    with pytest.raises(RLV2SyntheticReferenceError, match="descriptor drifted"):
        validate_rl_v2_synthetic_implementation(path)


def test_descriptor_rejects_design_mode_drift(tmp_path: Path) -> None:
    payload = copy.deepcopy(canonical_rl_v2_synthetic_implementation())
    payload["selected_design_mode"] = "explicit_position_state_training_and_historical_inference_parity"
    path = tmp_path / "descriptor.json"
    _write_descriptor(path, payload)

    with pytest.raises(RLV2SyntheticReferenceError, match="descriptor drifted"):
        validate_rl_v2_synthetic_implementation(path)


def test_descriptor_keeps_evaluation_and_phase6_isolated() -> None:
    descriptor = canonical_rl_v2_synthetic_implementation()

    assert descriptor["evaluation_isolation"]["consumed_historical_oos"]["usage"] == "forbidden"
    assert descriptor["evaluation_isolation"]["protected_final_holdout"]["usage"] == "forbidden"
    assert descriptor["evaluation_isolation"]["future_evaluation_window_selected"] is False
    assert descriptor["phase6_isolation"]["member"] is False
    assert descriptor["phase6_isolation"]["may_consume_results"] is False
    assert descriptor["phase6_isolation"]["authoritative_selected_model"] is None
