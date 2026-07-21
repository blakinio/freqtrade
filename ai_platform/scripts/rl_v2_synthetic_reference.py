#!/usr/bin/env python3
"""Pure synthetic RL-v2 action, reward, and observability reference."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any, Literal

from ai_platform.scripts.rl_v2_design_contract import (
    RLV2DesignContractError,
    validate_rl_v2_design_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DESCRIPTOR_PATH = (
    REPO_ROOT
    / "ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json"
)

Position = Literal["flat", "long"]
DesiredPosition = Literal["target_flat", "target_long"]

INVALID_ACTION_PENALTY = -1.0
FLAT_NEUTRAL_REWARD = -0.1
FLAT_TO_LONG_REWARD = 0.1
LONG_HOLD_PENALTY_FLOOR = -0.01
LONG_HOLD_PENALTY_CEILING = 0.0
EXIT_PROFIT_MULTIPLIER = 100.0


class RLV2SyntheticReferenceError(RuntimeError):
    """Raised when the synthetic RL-v2 reference or descriptor is invalid."""


class DesiredPositionAction(IntEnum):
    """Position-independent policy-facing action semantics."""

    TARGET_FLAT = 0
    TARGET_LONG = 1


ACTION_LABELS: dict[DesiredPositionAction, DesiredPosition] = {
    DesiredPositionAction.TARGET_FLAT: "target_flat",
    DesiredPositionAction.TARGET_LONG: "target_long",
}


@dataclass(frozen=True)
class SyntheticDecisionState:
    """Decision-time state supplied explicitly to the pure reward reference."""

    position: Position
    unrealized_profit_pct: float = 0.0
    trade_duration_ratio: float = 0.0


def desired_position(action: int | DesiredPositionAction) -> DesiredPosition:
    """Return the desired-position meaning for a policy-facing action."""
    try:
        normalized = DesiredPositionAction(action)
    except ValueError as exc:
        raise RLV2SyntheticReferenceError(f"Unknown desired-position action: {action}") from exc
    return ACTION_LABELS[normalized]


def training_desired_position(action: int | DesiredPositionAction) -> DesiredPosition:
    """Return training-style action meaning using the shared position-independent mapping."""
    return desired_position(action)


def inference_desired_position(action: int | DesiredPositionAction) -> DesiredPosition:
    """Return inference-style action meaning using the shared position-independent mapping."""
    return desired_position(action)


def reference_reward(
    state: SyntheticDecisionState,
    action: int | DesiredPositionAction,
) -> float:
    """Compute a prospective decision-time-only synthetic reward reference."""
    if state.position not in ("flat", "long"):
        raise RLV2SyntheticReferenceError(f"Unknown synthetic position: {state.position}")

    try:
        normalized = DesiredPositionAction(action)
    except ValueError:
        return INVALID_ACTION_PENALTY

    if state.position == "flat":
        if normalized is DesiredPositionAction.TARGET_FLAT:
            return FLAT_NEUTRAL_REWARD
        return FLAT_TO_LONG_REWARD

    if normalized is DesiredPositionAction.TARGET_FLAT:
        return state.unrealized_profit_pct * EXIT_PROFIT_MULTIPLIER

    bounded_ratio = min(max(state.trade_duration_ratio, 0.0), 1.0)
    return LONG_HOLD_PENALTY_FLOOR * bounded_ratio


class SyntheticObservability:
    """Collect deterministic, JSON-serializable synthetic observability counters."""

    def __init__(self, pairs: list[str] | tuple[str, ...]) -> None:
        normalized_pairs = tuple(sorted(set(pairs)))
        if not normalized_pairs:
            raise RLV2SyntheticReferenceError("At least one pair is required for observability")
        if any(not pair for pair in normalized_pairs):
            raise RLV2SyntheticReferenceError("Observability pair names must be non-empty")

        self._pairs = normalized_pairs
        self._action_counts = {
            pair: {str(int(action)): 0 for action in DesiredPositionAction}
            for pair in self._pairs
        }
        self._do_predict = {
            pair: {"accepted": 0, "rejected": 0} for pair in self._pairs
        }
        self._signals = {pair: {"entry": 0, "exit": 0} for pair in self._pairs}
        self._raw_backtest_trades = 0
        self._strict_oos = {"input": 0, "included": 0, "excluded": 0}

    def _require_pair(self, pair: str) -> None:
        if pair not in self._action_counts:
            raise RLV2SyntheticReferenceError(f"Unknown observability pair: {pair}")

    def record_action(self, pair: str, action: int | DesiredPositionAction) -> None:
        """Record one deterministic inference action."""
        self._require_pair(pair)
        try:
            normalized = DesiredPositionAction(action)
        except ValueError as exc:
            raise RLV2SyntheticReferenceError(f"Unknown desired-position action: {action}") from exc
        self._action_counts[pair][str(int(normalized))] += 1

    def record_do_predict(self, pair: str, *, accepted: bool) -> None:
        """Record one accepted or rejected FreqAI-style prediction gate outcome."""
        self._require_pair(pair)
        bucket = "accepted" if accepted else "rejected"
        self._do_predict[pair][bucket] += 1

    def record_pre_trade_signals(
        self,
        pair: str,
        *,
        entry: int = 0,
        exit: int = 0,
    ) -> None:
        """Record pre-trade strategy signal counts."""
        self._require_pair(pair)
        if entry < 0 or exit < 0:
            raise RLV2SyntheticReferenceError("Signal counts must be non-negative")
        self._signals[pair]["entry"] += entry
        self._signals[pair]["exit"] += exit

    def set_raw_backtest_trades(self, count: int) -> None:
        """Set the independently attributable raw backtest trade count."""
        if count < 0:
            raise RLV2SyntheticReferenceError("Raw backtest trade count must be non-negative")
        self._raw_backtest_trades = count

    def set_strict_oos_counts(
        self,
        *,
        input_trades: int,
        included_trades: int,
        excluded_trades: int,
    ) -> None:
        """Set strict-OOS input/included/excluded counts with a fail-closed identity check."""
        counts = (input_trades, included_trades, excluded_trades)
        if any(count < 0 for count in counts):
            raise RLV2SyntheticReferenceError("Strict-OOS counts must be non-negative")
        if included_trades + excluded_trades != input_trades:
            raise RLV2SyntheticReferenceError(
                "Strict-OOS included plus excluded trades must equal input trades"
            )
        self._strict_oos = {
            "input": input_trades,
            "included": included_trades,
            "excluded": excluded_trades,
        }

    def snapshot(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable evidence snapshot."""
        pair_evidence = {
            pair: {
                "actions": dict(self._action_counts[pair]),
                "do_predict": dict(self._do_predict[pair]),
                "pre_trade_signals": dict(self._signals[pair]),
            }
            for pair in self._pairs
        }
        return {
            "pairs": pair_evidence,
            "raw_backtest_trades": self._raw_backtest_trades,
            "strict_oos": dict(self._strict_oos),
        }


def canonical_rl_v2_synthetic_implementation() -> dict[str, Any]:
    """Return the only synthetic implementation descriptor authorized by this task."""
    return {
        "schema_version": 1,
        "implementation_id": "rl-v2-synthetic-implementation-v1",
        "status": "synthetic_only",
        "task": "docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md",
        "design_contract": (
            "ai_platform/experimental_model_research/rl-v2-design-contract-v1.json"
        ),
        "selected_design_mode": "position_independent_action_semantics",
        "scope": {
            "synthetic_reference_allowed": True,
            "unit_tests_allowed": True,
            "freqai_model_implementation_allowed": False,
            "strategy_implementation_allowed": False,
            "freqtrade_config_implementation_allowed": False,
            "experiment_manifest_implementation_allowed": False,
            "training_allowed": False,
            "backtest_allowed": False,
            "market_data_download_allowed": False,
            "hyperopt_allowed": False,
            "strict_oos_execution_allowed": False,
            "performance_evaluation_allowed": False,
        },
        "action_semantics": {
            "0": "target_flat",
            "1": "target_long",
            "meaning_depends_on_hidden_current_position": False,
            "training_inference_semantics_identical": True,
        },
        "reward_reference": {
            "invalid_action_penalty": INVALID_ACTION_PENALTY,
            "flat_neutral_reward": FLAT_NEUTRAL_REWARD,
            "flat_to_long_reward": FLAT_TO_LONG_REWARD,
            "long_hold_penalty_floor": LONG_HOLD_PENALTY_FLOOR,
            "long_hold_penalty_ceiling": LONG_HOLD_PENALTY_CEILING,
            "long_to_flat_reward": "decision_time_unrealized_profit_pct_x100",
            "future_market_information_used": False,
        },
        "observability": {
            "action_counts_by_pair_and_action": True,
            "zero_count_actions_included": True,
            "do_predict_accepted_rejected_by_pair": True,
            "pre_trade_entry_exit_signals_by_pair": True,
            "raw_backtest_trade_count": True,
            "strict_oos_input_included_excluded_counts": True,
            "json_serializable_snapshot": True,
        },
        "evaluation_isolation": {
            "consumed_historical_oos": {
                "timerange": "20260501-20260630",
                "usage": "forbidden",
            },
            "protected_final_holdout": {
                "timerange": "20260801-20260930",
                "usage": "forbidden",
                "not_before": "2026-10-01T00:00:00Z",
            },
            "future_evaluation_window_selected": False,
        },
        "phase6_isolation": {
            "member": False,
            "may_change_candidates": False,
            "may_change_selection_policy": False,
            "may_consume_results": False,
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
        raise RLV2SyntheticReferenceError(
            f"Unable to read RL-v2 synthetic implementation descriptor {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RLV2SyntheticReferenceError(
            "RL-v2 synthetic implementation descriptor must contain a JSON object"
        )
    return payload


def validate_rl_v2_synthetic_implementation(
    path: Path = DESCRIPTOR_PATH,
) -> dict[str, Any]:
    """Validate descriptor identity and binding to the merged RL-v2 design contract."""
    try:
        design_contract = validate_rl_v2_design_contract()
    except RLV2DesignContractError as exc:
        raise RLV2SyntheticReferenceError(str(exc)) from exc

    actual = _read_json(path)
    expected = canonical_rl_v2_synthetic_implementation()
    if actual != expected:
        raise RLV2SyntheticReferenceError("RL-v2 synthetic implementation descriptor drifted")

    selected_mode = actual["selected_design_mode"]
    allowed_modes = design_contract["position_state_inference_contract"]["allowed_design_modes"]
    if selected_mode not in allowed_modes:
        raise RLV2SyntheticReferenceError("Selected RL-v2 design mode is not contract-authorized")
    if selected_mode != "position_independent_action_semantics":
        raise RLV2SyntheticReferenceError("Synthetic task selected an unexpected RL-v2 design mode")

    return actual


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "descriptor",
        nargs="?",
        type=Path,
        default=DESCRIPTOR_PATH,
        help="Path to the RL-v2 synthetic implementation descriptor JSON",
    )
    parser.add_argument(
        "--print-canonical",
        action="store_true",
        help="Print the canonical synthetic implementation descriptor",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.print_canonical:
        print(json.dumps(canonical_rl_v2_synthetic_implementation(), indent=2, sort_keys=True))
        return 0

    try:
        descriptor = validate_rl_v2_synthetic_implementation(args.descriptor)
    except RLV2SyntheticReferenceError as exc:
        print(f"RL-v2 synthetic reference invalid: {exc}", file=sys.stderr)
        return 1

    print(descriptor["implementation_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
