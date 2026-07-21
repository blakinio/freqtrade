#!/usr/bin/env python3
"""Pure synthetic RL-v2 reward, action-parity, and observability reference."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any

from ai_platform.scripts.rl_v2_design_contract import (
    CONTRACT_PATH as DESIGN_CONTRACT_PATH,
    RLV2DesignContractError,
    validate_rl_v2_design_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DESCRIPTOR_PATH = (
    REPO_ROOT
    / "ai_platform"
    / "experimental_model_research"
    / "rl-v2-synthetic-implementation-v1.json"
)


class RLV2SyntheticReferenceError(RuntimeError):
    """Raised when the synthetic RL-v2 reference fails closed."""


class DesiredPosition(IntEnum):
    """Policy-facing desired-position action semantics."""

    TARGET_FLAT = 0
    TARGET_LONG = 1


class PositionState(StrEnum):
    """Externally owned current trade state used only by the transition adapter/reward."""

    FLAT = "flat"
    LONG = "long"


class Transition(StrEnum):
    """Synthetic transition emitted from current state plus desired position."""

    HOLD_FLAT = "hold_flat"
    ENTER_LONG = "enter_long"
    HOLD_LONG = "hold_long"
    EXIT_LONG = "exit_long"


@dataclass(frozen=True)
class RewardReference:
    """Prospectively frozen synthetic reward constants for this bounded task."""

    flat_neutral_reward: float = -0.01
    valid_long_entry_reward: float = 0.0
    holding_profit_clip_abs: float = 0.02
    holding_duration_penalty_per_step: float = 0.0001
    holding_duration_penalty_cap: float = 0.01
    exit_profit_clip_abs: float = 0.05
    invalid_action_penalty: float = -1.0


REWARD_REFERENCE = RewardReference()


def canonical_synthetic_descriptor() -> dict[str, Any]:
    """Return the only synthetic implementation descriptor authorized by this task."""
    return {
        "schema_version": 1,
        "implementation_id": "rl-v2-synthetic-implementation-v1",
        "status": "synthetic_only",
        "task": "docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md",
        "design_contract": {
            "path": "ai_platform/experimental_model_research/rl-v2-design-contract-v1.json",
            "contract_id": "rl-v2-design-contract-v1",
        },
        "selected_design_mode": "position_independent_action_semantics",
        "action_semantics": {
            "type": "desired_position",
            "actions": {"0": "target_flat", "1": "target_long"},
            "training_inference_meaning_identical": True,
            "policy_requires_hidden_current_position": False,
        },
        "reward_reference": {
            "selection": "prospective_fixed_not_tuned",
            "flat_neutral_reward": REWARD_REFERENCE.flat_neutral_reward,
            "valid_long_entry_reward": REWARD_REFERENCE.valid_long_entry_reward,
            "holding_profit_clip_abs": REWARD_REFERENCE.holding_profit_clip_abs,
            "holding_duration_penalty_per_step": (
                REWARD_REFERENCE.holding_duration_penalty_per_step
            ),
            "holding_duration_penalty_cap": REWARD_REFERENCE.holding_duration_penalty_cap,
            "exit_profit_clip_abs": REWARD_REFERENCE.exit_profit_clip_abs,
            "invalid_action_penalty": REWARD_REFERENCE.invalid_action_penalty,
            "future_market_information_used": False,
        },
        "observability_reference": {
            "action_counts_by_pair_and_action": True,
            "action_histogram_includes_zero_count_actions": True,
            "do_predict_accepted_rejected_by_pair": True,
            "pre_trade_entry_exit_signals_by_pair": True,
            "raw_backtest_trade_count": True,
            "strict_oos_input_included_excluded_counts": True,
            "snapshot_json_serializable": True,
        },
        "scope": {
            "pure_reference_implementation_allowed": True,
            "unit_tests_allowed": True,
            "synthetic_tests_allowed": True,
            "rl_v2_freqai_model_allowed": False,
            "rl_v2_strategy_allowed": False,
            "rl_v2_config_allowed": False,
            "experiment_manifest_allowed": False,
            "training_allowed": False,
            "backtest_allowed": False,
            "market_data_download_allowed": False,
            "hyperopt_allowed": False,
            "performance_evaluation_allowed": False,
            "future_evaluation_window_selection_allowed": False,
            "promotion_allowed": False,
            "live_trading_allowed": False,
        },
        "isolation": {
            "consumed_historical_oos": {
                "timerange": "20260501-20260630",
                "usage": "forbidden",
            },
            "protected_final_holdout": {
                "timerange": "20260801-20260930",
                "usage": "forbidden",
            },
            "frozen_entry_prediction_threshold": 0.006,
            "frozen_exit_prediction_threshold": -0.009,
            "phase6_authoritative_selected_model": None,
            "phase6_member": False,
        },
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        message = f"Unable to read RL-v2 descriptor {path}: {exc}"
        raise RLV2SyntheticReferenceError(message) from exc
    if not isinstance(payload, dict):
        raise RLV2SyntheticReferenceError("RL-v2 descriptor must contain a JSON object")
    return payload


def validate_synthetic_implementation(
    descriptor_path: Path = DESCRIPTOR_PATH,
    design_contract_path: Path = DESIGN_CONTRACT_PATH,
) -> dict[str, Any]:
    """Validate exact descriptor identity and binding to the merged design contract."""
    try:
        design_contract = validate_rl_v2_design_contract(design_contract_path)
    except RLV2DesignContractError as exc:
        raise RLV2SyntheticReferenceError(f"RL-v2 design contract invalid: {exc}") from exc

    allowed_modes = design_contract["position_state_inference_contract"]["allowed_design_modes"]
    selected_mode = canonical_synthetic_descriptor()["selected_design_mode"]
    if selected_mode not in allowed_modes:
        raise RLV2SyntheticReferenceError(
            "Selected synthetic design mode is not contract-authorized"
        )
    if selected_mode != "position_independent_action_semantics":
        raise RLV2SyntheticReferenceError(
            "Synthetic task must select position-independent semantics"
        )

    actual = _read_json(descriptor_path)
    expected = canonical_synthetic_descriptor()
    if actual != expected:
        raise RLV2SyntheticReferenceError("RL-v2 synthetic implementation descriptor drifted")
    return actual


def _normalize_position(position: PositionState | str) -> PositionState:
    try:
        return PositionState(position)
    except ValueError as exc:
        raise RLV2SyntheticReferenceError(f"Unsupported position state: {position}") from exc


def _normalize_action(action: DesiredPosition | int) -> DesiredPosition | None:
    if isinstance(action, bool):
        return None
    try:
        return DesiredPosition(action)
    except ValueError:
        return None


def desired_position_label(action: DesiredPosition | int) -> str:
    """Return stable policy-facing meaning independent of current position state."""
    normalized = _normalize_action(action)
    if normalized is None:
        raise RLV2SyntheticReferenceError(f"Unsupported desired-position action: {action}")
    return "target_flat" if normalized is DesiredPosition.TARGET_FLAT else "target_long"


def desired_position_transition(
    current_position: PositionState | str,
    action: DesiredPosition | int,
) -> Transition:
    """Translate desired position into a synthetic lifecycle transition."""
    position = _normalize_position(current_position)
    desired = _normalize_action(action)
    if desired is None:
        raise RLV2SyntheticReferenceError(f"Unsupported desired-position action: {action}")

    mapping = {
        (PositionState.FLAT, DesiredPosition.TARGET_FLAT): Transition.HOLD_FLAT,
        (PositionState.FLAT, DesiredPosition.TARGET_LONG): Transition.ENTER_LONG,
        (PositionState.LONG, DesiredPosition.TARGET_LONG): Transition.HOLD_LONG,
        (PositionState.LONG, DesiredPosition.TARGET_FLAT): Transition.EXIT_LONG,
    }
    return mapping[(position, desired)]


def training_style_transition(
    current_position: PositionState | str,
    action: DesiredPosition | int,
) -> Transition:
    """Synthetic training-style adapter using the canonical transition semantics."""
    return desired_position_transition(current_position, action)


def inference_style_transition(
    current_position: PositionState | str,
    action: DesiredPosition | int,
) -> Transition:
    """Synthetic historical-inference adapter using identical semantics."""
    return desired_position_transition(current_position, action)


def _clip(value: float, absolute_limit: float) -> float:
    return max(-absolute_limit, min(absolute_limit, value))


def reference_reward(
    current_position: PositionState | str,
    action: DesiredPosition | int,
    *,
    unrealized_profit: float,
    duration_steps: int,
    reference: RewardReference = REWARD_REFERENCE,
) -> float:
    """Calculate bounded synthetic reward from explicitly supplied decision-time state only."""
    if not math.isfinite(unrealized_profit):
        raise RLV2SyntheticReferenceError("unrealized_profit must be finite")
    invalid_duration = (
        isinstance(duration_steps, bool)
        or not isinstance(duration_steps, int)
        or duration_steps < 0
    )
    if invalid_duration:
        raise RLV2SyntheticReferenceError("duration_steps must be a non-negative integer")

    desired = _normalize_action(action)
    if desired is None:
        return reference.invalid_action_penalty

    position = _normalize_position(current_position)
    if position is PositionState.FLAT:
        if desired is DesiredPosition.TARGET_FLAT:
            return reference.flat_neutral_reward
        return reference.valid_long_entry_reward

    if desired is DesiredPosition.TARGET_FLAT:
        return _clip(unrealized_profit, reference.exit_profit_clip_abs)

    duration_penalty = min(
        duration_steps * reference.holding_duration_penalty_per_step,
        reference.holding_duration_penalty_cap,
    )
    holding_profit = _clip(unrealized_profit, reference.holding_profit_clip_abs)
    return holding_profit - duration_penalty


@dataclass
class _PairObservability:
    action_counts: dict[str, int] = field(
        default_factory=lambda: {"target_flat": 0, "target_long": 0}
    )
    do_predict: dict[str, int] = field(default_factory=lambda: {"accepted": 0, "rejected": 0})
    pre_trade_signals: dict[str, int] = field(default_factory=lambda: {"entry": 0, "exit": 0})


class RLV2ObservabilityAccumulator:
    """Deterministic synthetic telemetry accumulator for later runtime integration."""

    def __init__(self, pairs: Iterable[str]):
        normalized_pairs = sorted({pair.strip() for pair in pairs if pair.strip()})
        if not normalized_pairs:
            raise RLV2SyntheticReferenceError("At least one pair is required")
        self._pairs = {pair: _PairObservability() for pair in normalized_pairs}
        self._raw_backtest_trades = 0
        self._strict_oos = {"input": 0, "included": 0, "excluded": 0}

    def _pair(self, pair: str) -> _PairObservability:
        try:
            return self._pairs[pair]
        except KeyError as exc:
            raise RLV2SyntheticReferenceError(f"Unknown observability pair: {pair}") from exc

    def record_action(self, pair: str, action: DesiredPosition | int) -> None:
        label = desired_position_label(action)
        self._pair(pair).action_counts[label] += 1

    def record_do_predict(self, pair: str, *, accepted: bool) -> None:
        key = "accepted" if accepted else "rejected"
        self._pair(pair).do_predict[key] += 1

    def record_pre_trade_signal(
        self,
        pair: str,
        *,
        enter_long: bool = False,
        exit_long: bool = False,
    ) -> None:
        counters = self._pair(pair).pre_trade_signals
        if enter_long:
            counters["entry"] += 1
        if exit_long:
            counters["exit"] += 1

    def set_raw_backtest_trades(self, count: int) -> None:
        self._raw_backtest_trades = self._validate_count(count, "raw backtest trade count")

    def set_strict_oos_counts(self, *, input_count: int, included: int, excluded: int) -> None:
        input_value = self._validate_count(input_count, "strict OOS input count")
        included_value = self._validate_count(included, "strict OOS included count")
        excluded_value = self._validate_count(excluded, "strict OOS excluded count")
        if included_value + excluded_value != input_value:
            raise RLV2SyntheticReferenceError(
                "Strict OOS included plus excluded counts must equal input count"
            )
        self._strict_oos = {
            "input": input_value,
            "included": included_value,
            "excluded": excluded_value,
        }

    @staticmethod
    def _validate_count(count: int, label: str) -> int:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise RLV2SyntheticReferenceError(f"{label} must be a non-negative integer")
        return count

    def snapshot(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible telemetry including zero-count actions."""
        pairs: dict[str, Any] = {}
        total_actions = {"target_flat": 0, "target_long": 0}
        total_do_predict = {"accepted": 0, "rejected": 0}
        total_signals = {"entry": 0, "exit": 0}

        for pair, counters in sorted(self._pairs.items()):
            pair_actions = dict(counters.action_counts)
            pair_do_predict = dict(counters.do_predict)
            pair_signals = dict(counters.pre_trade_signals)
            pairs[pair] = {
                "actions": pair_actions,
                "do_predict": pair_do_predict,
                "pre_trade_signals": pair_signals,
            }
            for key in total_actions:
                total_actions[key] += pair_actions[key]
            for key in total_do_predict:
                total_do_predict[key] += pair_do_predict[key]
            for key in total_signals:
                total_signals[key] += pair_signals[key]

        return {
            "pairs": pairs,
            "totals": {
                "actions": total_actions,
                "do_predict": total_do_predict,
                "pre_trade_signals": total_signals,
            },
            "raw_backtest_trades": self._raw_backtest_trades,
            "strict_oos": dict(self._strict_oos),
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "descriptor",
        nargs="?",
        type=Path,
        default=DESCRIPTOR_PATH,
        help="Path to the RL-v2 synthetic implementation descriptor",
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
        print(json.dumps(canonical_synthetic_descriptor(), indent=2, sort_keys=True))
        return 0

    try:
        descriptor = validate_synthetic_implementation(args.descriptor)
    except RLV2SyntheticReferenceError as exc:
        print(f"RL-v2 synthetic reference invalid: {exc}", file=sys.stderr)
        return 1

    print(descriptor["implementation_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
