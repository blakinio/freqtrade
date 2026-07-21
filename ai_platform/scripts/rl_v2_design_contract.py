#!/usr/bin/env python3
"""Validate the frozen RL-v2 design-only research contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT / "ai_platform/experimental_model_research/rl-v2-design-contract-v1.json"
)


class RLV2DesignContractError(RuntimeError):
    """Raised when the prospective RL-v2 design contract drifts."""


def canonical_rl_v2_design_contract() -> dict[str, Any]:
    """Return the only RL-v2 design contract authorized by this bounded task."""
    return {
        "schema_version": 1,
        "contract_id": "rl-v2-design-contract-v1",
        "status": "design_only",
        "task": "docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md",
        "source_diagnosis": "docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md",
        "predecessor": {
            "track_id": "rl-research-v1",
            "immutable": True,
            "model": "LongOnlyReinforcementLearner",
            "strategy": "AiLongOnlyRLResearchStrategy",
            "historical_evidence_may_be_reinterpreted_as_fresh_validation": False,
        },
        "scope": {
            "contract_validation_allowed": True,
            "rl_v2_model_implementation_allowed": False,
            "rl_v2_strategy_implementation_allowed": False,
            "rl_v2_config_implementation_allowed": False,
            "training_allowed": False,
            "backtest_allowed": False,
            "market_data_download_allowed": False,
            "hyperopt_allowed": False,
            "performance_evaluation_allowed": False,
            "promotion_allowed": False,
            "profitability_claim_allowed": False,
            "superiority_claim_allowed": False,
        },
        "reward_contract": {
            "decision_time_state_only": True,
            "future_market_information_used": False,
            "perpetual_neutral_unpenalized_allowed": False,
            "flat_neutral_reward_relation": "strictly_less_than_valid_long_entry_reward",
            "invalid_action_penalty_required": True,
            "reward_magnitude_tuning_allowed_in_this_task": False,
            "required_synthetic_cases": [
                "flat_neutral_vs_valid_long_entry",
                "invalid_action_is_penalized",
                "holding_behavior_is_bounded",
                "exit_reward_uses_decision_time_state_only",
                "perpetual_neutral_episode_is_not_unpenalized",
            ],
        },
        "position_state_inference_contract": {
            "implementation_must_choose_exactly_one_design_mode": True,
            "allowed_design_modes": [
                "explicit_position_state_training_and_historical_inference_parity",
                "position_independent_action_semantics",
            ],
            "selected_design_mode": None,
            "selection_deferred_to_separate_implementation_task": True,
            "training_historical_inference_parity_required": True,
            "synthetic_parity_test_required": True,
            "hidden_position_dependent_action_validity_without_observation_allowed": False,
            "assume_add_state_info_available_in_backtesting": False,
        },
        "observability_contract": {
            "evidence_required_before_performance_interpretation": True,
            "mandatory_counts": [
                "deterministic_inference_actions_by_pair_and_action",
                "do_predict_accepted_rejected_by_pair",
                "pre_trade_entry_exit_signals_by_pair",
                "raw_backtest_trades",
                "strict_oos_input_included_excluded_trades",
            ],
            "action_histogram_must_include_zero_count_actions": True,
            "raw_and_strict_oos_trade_counts_must_remain_separately_attributable": True,
        },
        "evaluation_isolation": {
            "consumed_historical_oos": {
                "timerange": "20260501-20260630",
                "status": "consumed_historical_oos",
                "usage": "forbidden",
            },
            "protected_final_holdout": {
                "timerange": "20260801-20260930",
                "used": False,
                "usage": "forbidden",
                "not_before": "2026-10-01T00:00:00Z",
            },
            "future_evaluation_window": {
                "selected": False,
                "selection_allowed_in_this_task": False,
                "prospective_declaration_required": True,
                "must_be_non_protected_and_unconsumed": True,
            },
        },
        "phase6_isolation": {
            "member": False,
            "may_change_candidates": False,
            "may_change_selection_policy": False,
            "may_consume_rl_v2_results": False,
            "authoritative_selected_model": None,
        },
        "frozen_candidate_reference": {
            "entry_prediction_threshold": 0.006,
            "exit_prediction_threshold": -0.009,
            "may_change": False,
        },
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RLV2DesignContractError(
            f"Unable to read RL-v2 design contract {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RLV2DesignContractError("RL-v2 design contract must contain a JSON object")
    return payload


def validate_rl_v2_design_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    """Validate exact prospective design identity and all safety boundaries."""
    actual = _read_json(path)
    expected = canonical_rl_v2_design_contract()

    actual_keys = set(actual)
    expected_keys = set(expected)
    if actual_keys != expected_keys:
        missing = ",".join(sorted(expected_keys - actual_keys)) or "none"
        extra = ",".join(sorted(actual_keys - expected_keys)) or "none"
        raise RLV2DesignContractError(
            f"RL-v2 design contract top-level fields drifted: missing={missing}; extra={extra}"
        )

    for field, expected_value in expected.items():
        if actual[field] != expected_value:
            raise RLV2DesignContractError(f"RL-v2 design contract field {field} drifted")

    return actual


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "contract",
        nargs="?",
        type=Path,
        default=CONTRACT_PATH,
        help="Path to the RL-v2 design contract JSON",
    )
    parser.add_argument(
        "--print-canonical",
        action="store_true",
        help="Print the canonical design-only contract instead of validating a file",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.print_canonical:
        print(json.dumps(canonical_rl_v2_design_contract(), indent=2, sort_keys=True))
        return 0

    try:
        contract = validate_rl_v2_design_contract(args.contract)
    except RLV2DesignContractError as exc:
        print(f"RL-v2 design contract invalid: {exc}", file=sys.stderr)
        return 1

    print(contract["contract_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
