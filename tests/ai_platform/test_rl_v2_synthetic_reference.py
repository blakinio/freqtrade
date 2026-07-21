import json
import subprocess
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_design_contract import (
    CONTRACT_PATH as DESIGN_CONTRACT_PATH,
)
from ai_platform.scripts.rl_v2_synthetic_reference import (
    DESCRIPTOR_PATH,
    REWARD_REFERENCE,
    DesiredPosition,
    PositionState,
    RLV2ObservabilityAccumulator,
    RLV2SyntheticReferenceError,
    Transition,
    canonical_synthetic_descriptor,
    desired_position_label,
    inference_style_transition,
    reference_reward,
    training_style_transition,
    validate_synthetic_implementation,
)


def test_canonical_synthetic_descriptor_is_valid_and_contract_bound() -> None:
    descriptor = validate_synthetic_implementation()

    assert descriptor == canonical_synthetic_descriptor()
    assert descriptor["design_contract"]["contract_id"] == "rl-v2-design-contract-v1"
    assert descriptor["selected_design_mode"] == "position_independent_action_semantics"


def test_synthetic_descriptor_authorizes_no_runtime_execution() -> None:
    scope = canonical_synthetic_descriptor()["scope"]

    assert scope["pure_reference_implementation_allowed"] is True
    assert scope["unit_tests_allowed"] is True
    assert scope["synthetic_tests_allowed"] is True
    assert scope["rl_v2_freqai_model_allowed"] is False
    assert scope["rl_v2_strategy_allowed"] is False
    assert scope["rl_v2_config_allowed"] is False
    assert scope["experiment_manifest_allowed"] is False
    assert scope["training_allowed"] is False
    assert scope["backtest_allowed"] is False
    assert scope["market_data_download_allowed"] is False
    assert scope["performance_evaluation_allowed"] is False
    assert scope["future_evaluation_window_selection_allowed"] is False
    assert scope["promotion_allowed"] is False
    assert scope["live_trading_allowed"] is False


def test_reward_reference_is_prospectively_fixed() -> None:
    reward = canonical_synthetic_descriptor()["reward_reference"]

    assert reward == {
        "selection": "prospective_fixed_not_tuned",
        "flat_neutral_reward": -0.01,
        "valid_long_entry_reward": 0.0,
        "holding_profit_clip_abs": 0.02,
        "holding_duration_penalty_per_step": 0.0001,
        "holding_duration_penalty_cap": 0.01,
        "exit_profit_clip_abs": 0.05,
        "invalid_action_penalty": -1.0,
        "future_market_information_used": False,
    }


def test_valid_long_entry_is_strictly_preferred_to_remaining_flat() -> None:
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

    assert remain_flat == -0.01
    assert enter_long == 0.0
    assert enter_long > remain_flat


def test_perpetual_flat_neutral_episode_accumulates_negative_reward() -> None:
    episode_reward = sum(
        reference_reward(
            PositionState.FLAT,
            DesiredPosition.TARGET_FLAT,
            unrealized_profit=0.0,
            duration_steps=step,
        )
        for step in range(100)
    )

    assert episode_reward == pytest.approx(-1.0)
    assert episode_reward < 0.0


def test_invalid_action_is_penalized() -> None:
    reward = reference_reward(
        PositionState.FLAT,
        99,
        unrealized_profit=0.0,
        duration_steps=0,
    )

    assert reward == REWARD_REFERENCE.invalid_action_penalty == -1.0


def test_holding_reward_is_bounded_and_duration_penalty_is_capped() -> None:
    high_profit_short_hold = reference_reward(
        PositionState.LONG,
        DesiredPosition.TARGET_LONG,
        unrealized_profit=10.0,
        duration_steps=0,
    )
    low_profit_long_hold = reference_reward(
        PositionState.LONG,
        DesiredPosition.TARGET_LONG,
        unrealized_profit=-10.0,
        duration_steps=1_000_000,
    )
    low_profit_cap_hold = reference_reward(
        PositionState.LONG,
        DesiredPosition.TARGET_LONG,
        unrealized_profit=-10.0,
        duration_steps=100,
    )

    assert high_profit_short_hold == pytest.approx(0.02)
    assert low_profit_long_hold == pytest.approx(-0.03)
    assert low_profit_cap_hold == pytest.approx(-0.03)


def test_exit_reward_uses_supplied_decision_time_profit_and_ignores_duration() -> None:
    early = reference_reward(
        PositionState.LONG,
        DesiredPosition.TARGET_FLAT,
        unrealized_profit=0.0125,
        duration_steps=1,
    )
    late = reference_reward(
        PositionState.LONG,
        DesiredPosition.TARGET_FLAT,
        unrealized_profit=0.0125,
        duration_steps=100_000,
    )
    clipped_gain = reference_reward(
        PositionState.LONG,
        DesiredPosition.TARGET_FLAT,
        unrealized_profit=5.0,
        duration_steps=1,
    )
    clipped_loss = reference_reward(
        PositionState.LONG,
        DesiredPosition.TARGET_FLAT,
        unrealized_profit=-5.0,
        duration_steps=1,
    )

    assert early == late == pytest.approx(0.0125)
    assert clipped_gain == pytest.approx(0.05)
    assert clipped_loss == pytest.approx(-0.05)


@pytest.mark.parametrize(
    ("position", "action", "expected"),
    [
        (PositionState.FLAT, DesiredPosition.TARGET_FLAT, Transition.HOLD_FLAT),
        (PositionState.FLAT, DesiredPosition.TARGET_LONG, Transition.ENTER_LONG),
        (PositionState.LONG, DesiredPosition.TARGET_LONG, Transition.HOLD_LONG),
        (PositionState.LONG, DesiredPosition.TARGET_FLAT, Transition.EXIT_LONG),
    ],
)
def test_training_and_inference_desired_position_semantics_are_identical(
    position: PositionState,
    action: DesiredPosition,
    expected: Transition,
) -> None:
    assert training_style_transition(position, action) is expected
    assert inference_style_transition(position, action) is expected


def test_policy_facing_action_meaning_is_independent_of_current_position() -> None:
    for position in PositionState:
        assert desired_position_label(DesiredPosition.TARGET_FLAT) == "target_flat"
        assert desired_position_label(DesiredPosition.TARGET_LONG) == "target_long"
        assert training_style_transition(position, DesiredPosition.TARGET_FLAT)
        assert training_style_transition(position, DesiredPosition.TARGET_LONG)


def test_invalid_transition_action_fails_closed() -> None:
    with pytest.raises(RLV2SyntheticReferenceError, match="Unsupported desired-position action"):
        training_style_transition(PositionState.FLAT, 99)


def test_observability_snapshot_includes_zero_count_actions_for_every_pair() -> None:
    accumulator = RLV2ObservabilityAccumulator(["ETH/USDT", "BTC/USDT"])

    snapshot = accumulator.snapshot()

    assert list(snapshot["pairs"]) == ["BTC/USDT", "ETH/USDT"]
    for pair in snapshot["pairs"].values():
        assert pair["actions"] == {"target_flat": 0, "target_long": 0}
        assert pair["do_predict"] == {"accepted": 0, "rejected": 0}
        assert pair["pre_trade_signals"] == {"entry": 0, "exit": 0}
    assert snapshot["raw_backtest_trades"] == 0
    assert snapshot["strict_oos"] == {"input": 0, "included": 0, "excluded": 0}


def test_observability_records_separate_prediction_signal_and_trade_layers() -> None:
    accumulator = RLV2ObservabilityAccumulator(["BTC/USDT", "ETH/USDT"])
    accumulator.record_action("BTC/USDT", DesiredPosition.TARGET_LONG)
    accumulator.record_action("BTC/USDT", DesiredPosition.TARGET_LONG)
    accumulator.record_action("ETH/USDT", DesiredPosition.TARGET_FLAT)
    accumulator.record_do_predict("BTC/USDT", accepted=True)
    accumulator.record_do_predict("BTC/USDT", accepted=False)
    accumulator.record_do_predict("ETH/USDT", accepted=True)
    accumulator.record_pre_trade_signal("BTC/USDT", enter_long=True)
    accumulator.record_pre_trade_signal("BTC/USDT", exit_long=True)
    accumulator.set_raw_backtest_trades(1)
    accumulator.set_strict_oos_counts(input_count=1, included=1, excluded=0)

    snapshot = accumulator.snapshot()

    assert snapshot["pairs"]["BTC/USDT"]["actions"] == {
        "target_flat": 0,
        "target_long": 2,
    }
    assert snapshot["pairs"]["ETH/USDT"]["actions"] == {
        "target_flat": 1,
        "target_long": 0,
    }
    assert snapshot["totals"]["actions"] == {"target_flat": 1, "target_long": 2}
    assert snapshot["totals"]["do_predict"] == {"accepted": 2, "rejected": 1}
    assert snapshot["totals"]["pre_trade_signals"] == {"entry": 1, "exit": 1}
    assert snapshot["raw_backtest_trades"] == 1
    assert snapshot["strict_oos"] == {"input": 1, "included": 1, "excluded": 0}
    assert json.loads(json.dumps(snapshot, sort_keys=True)) == snapshot


def test_strict_oos_observability_counts_must_reconcile() -> None:
    accumulator = RLV2ObservabilityAccumulator(["BTC/USDT"])

    with pytest.raises(RLV2SyntheticReferenceError, match="must equal input count"):
        accumulator.set_strict_oos_counts(input_count=3, included=1, excluded=1)


def test_unknown_observability_pair_fails_closed() -> None:
    accumulator = RLV2ObservabilityAccumulator(["BTC/USDT"])

    with pytest.raises(RLV2SyntheticReferenceError, match="Unknown observability pair"):
        accumulator.record_action("ETH/USDT", DesiredPosition.TARGET_LONG)


def test_descriptor_drift_fails_closed(tmp_path: Path) -> None:
    descriptor = canonical_synthetic_descriptor()
    descriptor["scope"]["backtest_allowed"] = True
    path = tmp_path / "descriptor.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")

    with pytest.raises(RLV2SyntheticReferenceError, match="descriptor drifted"):
        validate_synthetic_implementation(path)


def test_invalid_design_contract_binding_fails_closed(tmp_path: Path) -> None:
    design_contract = json.loads(DESIGN_CONTRACT_PATH.read_text(encoding="utf-8"))
    design_contract["scope"]["training_allowed"] = True
    path = tmp_path / "design-contract.json"
    path.write_text(json.dumps(design_contract), encoding="utf-8")

    with pytest.raises(RLV2SyntheticReferenceError, match="design contract invalid"):
        validate_synthetic_implementation(DESCRIPTOR_PATH, path)


def test_temporary_ruff_diagnostics() -> None:
    result = subprocess.run(
        [
            "ruff",
            "check",
            "ai_platform/scripts/rl_v2_synthetic_reference.py",
            "tests/ai_platform/test_rl_v2_synthetic_reference.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
