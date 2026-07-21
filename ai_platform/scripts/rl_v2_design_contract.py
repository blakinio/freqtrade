#!/usr/bin/env python3
"""Validate the non-executable RL-v2 design contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_CONTRACT_ID = "rl-v2-design-contract-v1"
CONSUMED_HISTORICAL_OOS = "20260501-20260630"
PROTECTED_FINAL_HOLDOUT = "20260801-20260930"
EXPECTED_ACTIONS = {"0": "target_flat", "1": "target_long"}
REQUIRED_EVIDENCE = {
    "deterministic_action_counts_by_pair",
    "deterministic_action_counts_total",
    "do_predict_accepted_count",
    "do_predict_rejected_count",
    "pre_execution_enter_signal_count",
    "pre_execution_exit_signal_count",
    "rejected_signal_count",
    "raw_backtest_trade_count",
    "strict_oos_input_trade_count",
    "strict_oos_included_trade_count",
    "strict_oos_excluded_trade_count",
    "deterministic_eval_episode_reward",
    "git_commit",
    "freqai_identifier",
    "model_class",
    "config_sha256",
    "strategy_sha256",
    "model_source_sha256",
    "contract_sha256",
}
REQUIRED_PRE_EXECUTION_GATES = {
    "design_contract_validation_pass",
    "reward_unit_tests_pass",
    "synthetic_reward_tests_pass",
    "desired_position_action_semantics_tests_pass",
    "training_inference_parity_tests_pass",
    "execution_observability_instrumented",
    "fresh_evaluation_window_prospectively_declared",
    "forbidden_window_overlap_check_pass",
    "protected_final_holdout_check_pass",
    "canonical_identity_hashes_pinned",
}


class ContractValidationError(RuntimeError):
    """Raised when the RL-v2 contract fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractValidationError(message)


def load_contract(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"Unable to read contract {path}: {exc}") from exc
    _require(isinstance(payload, dict), "Contract root must be a JSON object")
    return payload


def _validate_authorization(contract: dict[str, Any]) -> None:
    authorization = contract.get("authorization")
    _require(isinstance(authorization, dict), "authorization must be an object")
    required = {
        "model_implementation_allowed",
        "strategy_implementation_allowed",
        "training_allowed",
        "backtest_allowed",
        "market_data_download_allowed",
        "historical_oos_execution_allowed",
        "promotion_allowed",
        "live_trading_allowed",
    }
    _require(required.issubset(authorization), "authorization is missing required fields")
    _require(
        all(authorization[field] is False for field in required),
        "RL-v2 design contract must not authorize implementation or execution",
    )


def _validate_isolation(contract: dict[str, Any]) -> None:
    isolation = contract.get("isolation", {})
    _require(isolation.get("phase6_member") is False, "RL-v2 must remain outside Phase 6")
    _require(isolation.get("may_change_phase6") is False, "RL-v2 may not change Phase 6")
    _require(
        isolation.get("cross_track_selection_allowed") is False,
        "Cross-track selection must remain forbidden",
    )
    _require(
        isolation.get("consumed_oos_retuning_allowed") is False,
        "Consumed historical OOS may not be used for retuning",
    )
    _require(
        isolation.get("frozen_entry_prediction_threshold") == 0.006,
        "Frozen entry threshold must remain 0.006",
    )
    _require(
        isolation.get("frozen_exit_prediction_threshold") == -0.009,
        "Frozen exit threshold must remain -0.009",
    )


def _validate_algorithm_scope(contract: dict[str, Any]) -> None:
    scope = contract.get("algorithm_scope", {})
    _require(scope.get("algorithm") == "PPO", "Algorithm must remain PPO in this design slice")
    _require(scope.get("policy_type") == "MlpPolicy", "Policy type must remain MlpPolicy")
    _require(scope.get("seed") == 42, "Seed must remain 42")
    for field in (
        "algorithm_change_allowed",
        "feature_search_allowed",
        "hyperparameter_sweep_allowed",
        "reward_sweep_allowed",
    ):
        _require(scope.get(field) is False, f"{field} must remain false")


def _validate_reward_geometry(contract: dict[str, Any]) -> None:
    reward = contract.get("reward_geometry", {})
    _require(reward.get("decision_time_information_only") is True, "Reward must be decision-time only")
    _require(
        reward.get("future_candle_information_allowed") is False,
        "Future candle information must remain forbidden",
    )
    _require(
        reward.get("valid_long_entry_strictly_preferred_to_neutral_while_flat") is True,
        "Valid long entry must be strictly preferred to remaining neutral while flat",
    )
    _require(
        reward.get("perpetual_neutral_inactivity_unpenalized") is False,
        "Perpetual neutral inactivity may not remain an unpenalized solution",
    )
    _require(reward.get("invalid_actions_penalized") is True, "Invalid actions must be penalized")
    _require(
        reward.get("numeric_reward_values_status")
        == "must_be_frozen_in_later_implementation_task_before_execution",
        "Numeric reward values must be frozen prospectively before execution",
    )
    _require(
        reward.get("synthetic_reward_tests_required") is True,
        "Synthetic reward tests must be required",
    )


def _validate_position_inference_parity(contract: dict[str, Any]) -> None:
    parity = contract.get("position_inference_parity", {})
    _require(
        parity.get("policy_action_semantics") == "desired_position",
        "RL-v2 policy actions must express desired position",
    )
    action_space = parity.get("action_space", {})
    _require(action_space.get("type") == "Discrete(2)", "Desired-position action space must be Discrete(2)")
    _require(action_space.get("actions") == EXPECTED_ACTIONS, "Desired-position action mapping is invalid")
    _require(
        parity.get("policy_requires_current_position_observation") is False,
        "Policy must not require hidden current-position state",
    )
    _require(
        parity.get("backtest_add_state_info_assumed_available") is False,
        "Contract may not assume backtest add_state_info is available",
    )
    _require(
        parity.get("training_and_historical_inference_semantics_identical") is True,
        "Training and historical inference action semantics must match",
    )
    _require(
        parity.get("synthetic_parity_test_required") is True,
        "Synthetic training/inference parity test must be required",
    )
    translation = parity.get("strategy_translation", {})
    _require(
        translation.get("current_trade_state_owner") == "freqtrade_trade_lifecycle",
        "Current trade state must remain owned by Freqtrade trade lifecycle",
    )


def _validate_observability(contract: dict[str, Any]) -> None:
    observability = contract.get("observability", {})
    evidence = observability.get("required_evidence")
    _require(isinstance(evidence, list), "observability.required_evidence must be a list")
    _require(REQUIRED_EVIDENCE.issubset(set(evidence)), "Mandatory execution evidence is incomplete")
    for field in (
        "action_histogram_required_before_artifact_upload",
        "prediction_gate_histogram_required_before_artifact_upload",
        "pre_trade_signal_histogram_required_before_artifact_upload",
    ):
        _require(observability.get(field) is True, f"{field} must be required")


def _validate_evaluation_isolation(contract: dict[str, Any]) -> None:
    evaluation = contract.get("evaluation_isolation", {})
    _require(
        evaluation.get("consumed_historical_oos") == CONSUMED_HISTORICAL_OOS,
        "Consumed historical OOS identity changed",
    )
    _require(
        evaluation.get("protected_final_holdout") == PROTECTED_FINAL_HOLDOUT,
        "Protected final holdout identity changed",
    )
    forbidden = evaluation.get("forbidden_windows")
    _require(isinstance(forbidden, list), "forbidden_windows must be a list")
    _require(
        {CONSUMED_HISTORICAL_OOS, PROTECTED_FINAL_HOLDOUT}.issubset(set(forbidden)),
        "Consumed OOS and protected final holdout must both remain forbidden",
    )
    _require(evaluation.get("future_evaluation_window") is None, "Future evaluation window is not declared yet")
    _require(evaluation.get("future_evaluation_status") == "not_declared", "Future evaluation must remain undeclared")
    _require(
        evaluation.get("prospective_declaration_required") is True,
        "Future evaluation must require prospective declaration",
    )
    _require(
        evaluation.get("fresh_non_protected_data_required") is True,
        "Future evaluation must require fresh non-protected data",
    )
    _require(
        evaluation.get("separate_execution_request_required") is True,
        "Future execution must require a separate request",
    )


def validate_contract(contract: dict[str, Any]) -> None:
    _require(contract.get("schema_version") == 1, "Only schema_version 1 is supported")
    _require(contract.get("contract_id") == EXPECTED_CONTRACT_ID, "Unexpected contract_id")
    _require(contract.get("status") == "design_only", "Contract must remain design_only")
    source = contract.get("source", {})
    _require(source.get("predecessor_track") == "rl-research-v1", "Unexpected predecessor track")
    _require(
        source.get("diagnosis") == "docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md",
        "RL-v2 contract must reference the durable v1 diagnosis",
    )
    _validate_authorization(contract)
    _validate_isolation(contract)
    _validate_algorithm_scope(contract)
    _validate_reward_geometry(contract)
    _validate_position_inference_parity(contract)
    _validate_observability(contract)
    _validate_evaluation_isolation(contract)
    gates = contract.get("pre_execution_gates")
    _require(isinstance(gates, list), "pre_execution_gates must be a list")
    _require(
        REQUIRED_PRE_EXECUTION_GATES.issubset(set(gates)),
        "Pre-execution gate contract is incomplete",
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to RL-v2 design contract JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        contract = load_contract(args.contract.resolve())
        validate_contract(contract)
    except ContractValidationError as exc:
        print(f"RL-v2 contract validation failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"contract_id": contract["contract_id"], "status": "valid"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
