from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from gymnasium import spaces

from ai_platform.scripts.rl_v2_synthetic_reference import (
    DesiredPosition,
    PositionState,
    RLV2ObservabilityAccumulator,
    RLV2SyntheticReferenceError,
    Transition,
    desired_position_label,
    desired_position_transition,
    reference_reward,
)
from freqtrade.freqai.prediction_models.ReinforcementLearner import ReinforcementLearner
from freqtrade.freqai.RL.BaseEnvironment import BaseEnvironment, Positions


class DesiredPositionEnvironment(BaseEnvironment):
    """Two-action long-only environment bound to the frozen RL-v2 synthetic semantics."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.actions = DesiredPosition

    def set_action_space(self) -> None:
        self.action_space = spaces.Discrete(len(DesiredPosition))

    def _position_state(self) -> PositionState:
        if self._position == Positions.Neutral:
            return PositionState.FLAT
        if self._position == Positions.Long:
            return PositionState.LONG
        raise RLV2SyntheticReferenceError(
            f"Unsupported runtime position for long-only RL-v2 environment: {self._position}"
        )

    def _transition(self, action: int) -> Transition:
        return desired_position_transition(self._position_state(), action)

    def step(self, action: int):
        """Apply canonical desired-position reward and transition before advancing market state."""
        self._done = False
        self._update_unrealized_total_profit()

        step_reward = self.calculate_reward(action)
        self.total_reward += step_reward
        self.tensorboard_log(desired_position_label(action), category="actions")

        transition = self._transition(action)
        trade_type = None
        trade_profit = self.get_unrealized_profit()
        if transition is Transition.ENTER_LONG:
            self._position = Positions.Long
            self._last_trade_tick = self._current_tick
            trade_type = "enter_long"
        elif transition is Transition.EXIT_LONG:
            self._update_total_profit()
            self._position = Positions.Neutral
            self._last_trade_tick = None
            trade_type = "exit_long"

        if trade_type is not None:
            self.trade_history.append(
                {
                    "price": self.current_price(),
                    "index": self._current_tick,
                    "type": trade_type,
                    "profit": trade_profit,
                }
            )

        self._current_tick += 1
        if self._current_tick >= self._end_tick:
            self._done = True

        self._update_unrealized_total_profit()
        if (
            self._total_profit < self.max_drawdown
            or self._total_unrealized_profit < self.max_drawdown
        ):
            self._done = True

        self._position_history.append(self._position)
        info = {
            "tick": self._current_tick,
            "action": action,
            "action_label": desired_position_label(action),
            "total_reward": self.total_reward,
            "total_profit": self._total_profit,
            "position": self._position.value,
            "trade_duration": self.get_trade_duration(),
            "current_profit_pct": self.get_unrealized_profit(),
        }
        observation = self._get_observation()
        truncated = False
        self._update_history(info)
        return observation, step_reward, self._done, truncated, info

    def is_tradesignal(self, action: int) -> bool:
        try:
            transition = self._transition(action)
        except RLV2SyntheticReferenceError:
            return False
        return transition in {Transition.ENTER_LONG, Transition.EXIT_LONG}

    def _is_valid(self, action: int) -> bool:
        """Both desired-position actions are valid regardless of current position state."""
        try:
            desired_position_label(action)
        except RLV2SyntheticReferenceError:
            return False
        return True

    def calculate_reward(self, action: int) -> float:
        """Delegate reward calculation to the prospectively frozen synthetic reference."""
        return reference_reward(
            self._position_state(),
            action,
            unrealized_profit=float(self.get_unrealized_profit()),
            duration_steps=int(self.get_trade_duration()),
        )


class DesiredPositionReinforcementLearner(ReinforcementLearner):
    """Research-only PPO-compatible FreqAI adapter for RL-v2 desired-position semantics."""

    MyRLEnv = DesiredPositionEnvironment

    def pack_env_dict(self, pair: str) -> dict[str, Any]:
        env_info = super().pack_env_dict(pair)
        parameters = self.freqai_info.get("model_training_parameters", {})
        env_info["seed"] = int(parameters.get("seed", 42))
        env_info["fee"] = float(self.rl_config.get("training_fee", 0.002))
        return env_info

    @staticmethod
    def create_observability_accumulator(pairs: Iterable[str]) -> RLV2ObservabilityAccumulator:
        """Create the canonical observability accumulator without fabricating counts."""
        return RLV2ObservabilityAccumulator(pairs)
