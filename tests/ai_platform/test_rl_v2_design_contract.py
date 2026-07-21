import copy
import json
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_design_contract import (
    CONTRACT_PATH,
    RLV2DesignContractError,
    canonical_rl_v2_design_contract,
    validate_rl_v2_design_contract,
)


def _write_contract(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mutated_contract(tmp_path: Path, mutate) -> Path:
    payload = copy.deepcopy(canonical_rl_v2_design_contract())
    mutate(payload)
    path = tmp_path / "contract.json"
    _write_contract(path, payload)
    return path


def test_repository_contract_matches_canonical_design_contract() -> None:
    assert (
        validate_rl_v2_design_contract(CONTRACT_PATH)
        == canonical_rl_v2_design_contract()
    )


def test_contract_rejects_unpenalized_perpetual_neutral_policy(tmp_path: Path) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["reward_contract"].update(
            {"perpetual_neutral_unpenalized_allowed": True}
        ),
    )

    with pytest.raises(RLV2DesignContractError, match="reward_contract"):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_flat_neutral_reward_without_strict_entry_advantage(
    tmp_path: Path,
) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["reward_contract"].update(
            {"flat_neutral_reward_relation": "equal_to_valid_long_entry_reward"}
        ),
    )

    with pytest.raises(RLV2DesignContractError, match="reward_contract"):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_future_derived_reward_inputs(tmp_path: Path) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["reward_contract"].update(
            {"future_market_information_used": True}
        ),
    )

    with pytest.raises(RLV2DesignContractError, match="reward_contract"):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_runtime_implementation_or_execution_authorization(
    tmp_path: Path,
) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["scope"].update(
            {"rl_v2_model_implementation_allowed": True, "training_allowed": True}
        ),
    )

    with pytest.raises(RLV2DesignContractError, match="scope"):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_hidden_position_state_without_parity_requirement(
    tmp_path: Path,
) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["position_state_inference_contract"].update(
            {
                "training_historical_inference_parity_required": False,
                "hidden_position_dependent_action_validity_without_observation_allowed": True,
            }
        ),
    )

    with pytest.raises(
        RLV2DesignContractError,
        match="position_state_inference_contract",
    ):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_missing_action_observability(tmp_path: Path) -> None:
    def mutate(payload: dict) -> None:
        payload["observability_contract"]["mandatory_counts"].remove(
            "deterministic_inference_actions_by_pair_and_action"
        )

    path = _mutated_contract(tmp_path, mutate)

    with pytest.raises(RLV2DesignContractError, match="observability_contract"):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_consumed_historical_oos_reuse(tmp_path: Path) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["evaluation_isolation"]["consumed_historical_oos"].update(
            {"usage": "allowed"}
        ),
    )

    with pytest.raises(RLV2DesignContractError, match="evaluation_isolation"):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_protected_final_holdout_use(tmp_path: Path) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["evaluation_isolation"]["protected_final_holdout"].update(
            {"used": True, "usage": "allowed"}
        ),
    )

    with pytest.raises(RLV2DesignContractError, match="evaluation_isolation"):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_future_evaluation_window_selected_in_design_task(
    tmp_path: Path,
) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["evaluation_isolation"]["future_evaluation_window"].update(
            {"selected": True, "selection_allowed_in_this_task": True}
        ),
    )

    with pytest.raises(RLV2DesignContractError, match="evaluation_isolation"):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_phase6_consumption_or_membership(tmp_path: Path) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["phase6_isolation"].update(
            {"member": True, "may_consume_rl_v2_results": True}
        ),
    )

    with pytest.raises(RLV2DesignContractError, match="phase6_isolation"):
        validate_rl_v2_design_contract(path)


def test_contract_rejects_frozen_threshold_drift(tmp_path: Path) -> None:
    path = _mutated_contract(
        tmp_path,
        lambda payload: payload["frozen_candidate_reference"].update(
            {"entry_prediction_threshold": 0.007}
        ),
    )

    with pytest.raises(RLV2DesignContractError, match="frozen_candidate_reference"):
        validate_rl_v2_design_contract(path)
