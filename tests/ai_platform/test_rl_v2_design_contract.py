import copy
import json
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_design_contract import (
    CONSUMED_HISTORICAL_OOS,
    PROTECTED_FINAL_HOLDOUT,
    REQUIRED_EVIDENCE,
    ContractValidationError,
    load_contract,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT / "ai_platform" / "experimental_model_research" / "rl-v2-design-contract-v1.json"
)


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_canonical_rl_v2_design_contract_is_valid() -> None:
    contract = load_contract(CONTRACT_PATH)

    validate_contract(contract)


def test_rl_v2_contract_fails_closed_if_execution_is_authorized() -> None:
    contract = _contract()
    contract["authorization"]["training_allowed"] = True

    with pytest.raises(ContractValidationError, match="must not authorize"):
        validate_contract(contract)


def test_rl_v2_contract_preserves_consumed_oos_and_final_holdout_isolation() -> None:
    contract = _contract()
    evaluation = contract["evaluation_isolation"]

    assert evaluation["consumed_historical_oos"] == CONSUMED_HISTORICAL_OOS
    assert evaluation["protected_final_holdout"] == PROTECTED_FINAL_HOLDOUT
    assert {CONSUMED_HISTORICAL_OOS, PROTECTED_FINAL_HOLDOUT}.issubset(
        set(evaluation["forbidden_windows"])
    )
    assert evaluation["future_evaluation_window"] is None
    assert evaluation["future_evaluation_status"] == "not_declared"


def test_rl_v2_contract_rejects_a_declared_evaluation_window() -> None:
    contract = _contract()
    contract["evaluation_isolation"]["future_evaluation_window"] = "20261001-20261130"

    with pytest.raises(ContractValidationError, match="not declared yet"):
        validate_contract(contract)


def test_rl_v2_contract_rejects_missing_forbidden_window() -> None:
    contract = _contract()
    contract["evaluation_isolation"]["forbidden_windows"] = [CONSUMED_HISTORICAL_OOS]

    with pytest.raises(ContractValidationError, match="must both remain forbidden"):
        validate_contract(contract)


def test_rl_v2_reward_contract_rejects_neutral_policy_attractor() -> None:
    contract = _contract()
    contract["reward_geometry"]["perpetual_neutral_inactivity_unpenalized"] = True

    with pytest.raises(ContractValidationError, match="Perpetual neutral inactivity"):
        validate_contract(contract)


def test_rl_v2_reward_contract_requires_entry_preference() -> None:
    contract = _contract()
    contract["reward_geometry"]["valid_long_entry_strictly_preferred_to_neutral_while_flat"] = False

    with pytest.raises(ContractValidationError, match="strictly preferred"):
        validate_contract(contract)


def test_rl_v2_action_semantics_remove_hidden_position_requirement() -> None:
    contract = _contract()
    parity = contract["position_inference_parity"]

    assert parity["policy_action_semantics"] == "desired_position"
    assert parity["action_space"]["actions"] == {
        "0": "target_flat",
        "1": "target_long",
    }
    assert parity["policy_requires_current_position_observation"] is False
    assert parity["backtest_add_state_info_assumed_available"] is False
    assert parity["training_and_historical_inference_semantics_identical"] is True


def test_rl_v2_contract_rejects_transition_actions_that_require_hidden_state() -> None:
    contract = _contract()
    contract["position_inference_parity"]["policy_action_semantics"] = "transition_action"

    with pytest.raises(ContractValidationError, match="desired position"):
        validate_contract(contract)


def test_rl_v2_observability_closes_v1_action_evidence_gap() -> None:
    contract = _contract()
    evidence = set(contract["observability"]["required_evidence"])

    assert REQUIRED_EVIDENCE.issubset(evidence)
    assert {
        "deterministic_action_counts_by_pair",
        "do_predict_accepted_count",
        "do_predict_rejected_count",
        "pre_execution_enter_signal_count",
        "pre_execution_exit_signal_count",
        "raw_backtest_trade_count",
        "strict_oos_input_trade_count",
    }.issubset(evidence)


def test_rl_v2_contract_rejects_missing_action_histogram_evidence() -> None:
    contract = _contract()
    contract["observability"]["required_evidence"].remove("deterministic_action_counts_by_pair")

    with pytest.raises(ContractValidationError, match="evidence is incomplete"):
        validate_contract(contract)


def test_rl_v2_contract_rejects_phase6_membership() -> None:
    contract = _contract()
    contract["isolation"]["phase6_member"] = True

    with pytest.raises(ContractValidationError, match="outside Phase 6"):
        validate_contract(contract)


def test_rl_v2_contract_validation_is_side_effect_free() -> None:
    contract = _contract()
    original = copy.deepcopy(contract)

    validate_contract(contract)

    assert contract == original
