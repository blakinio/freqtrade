from __future__ import annotations

from enum import IntEnum
from typing import Any

from gymnasium import spaces

from ai_platform.scripts.rl_v2_synthetic_reference import (
    DesiredPosition,
    PositionState,
    RLV2SyntheticReferenceError,
    Transition,
    desired_position_label,
    desired_position_transition,
    reference_reward,
)
from freqtrade.freqai.prediction_models.ReinforcementLearner import ReinforcementLearner
from freqtrade.freqai.RL.BaseEnvironment import BaseEnvironment, Positions


class DesiredPositionActions(IntEnum):
    """Two-action policy surface with position-independent desired-position semantics."""

    Target_flat = DesiredPosition.TARGET_FLAT.value
    Target_long = DesiredPosition.TARGET_LONG.value


class DesiredPositionEnvironment(BaseEnvironment):
    """Long-only RL-v2 environment adapter bound to the canonical synthetic reference."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.actions = DesiredPositionActions

    def set_action_space(self) -> None:
        self.action_space = spaces.Discrete(len(DesiredPositionActions))

    def _position_state(self) -> PositionState:
        if self._position == Positions.Neutral:
            return PositionState.FLAT
        if self._position == Positions.Long:
            return PositionState.LONG
        raise RLV2SyntheticReferenceError(
            f"Unsupported runtime position for long-only RL-v2 adapter: {self._position}",
        )

    def _transition(self, action: int) -> Transition:
        return desired_position_transition(self._position_state(), action)

    def _is_valid(self, action: int) -> bool:
        try:
            desired_position_label(action)
        except RLV2SyntheticReferenceError:
            return False
        return True

    def is_tradesignal(self, action: int) -> bool:
        if not self._is_valid(action):
            return False
        return self._transition(action) in (Transition.ENTER_LONG, Transition.EXIT_LONG)

    def calculate_reward(self, action: int) -> float:
        """Delegate reward geometry to the prospectively frozen pure reference."""
        return reference_reward(
            self._position_state(),
            action,
            unrealized_profit=float(self.get_unrealized_profit()),
            duration_steps=int(self.get_trade_duration()),
        )

    def step(self, action: int):
        """Apply canonical desired-position reward/transition semantics before advancing state."""
        self._done = False
        self._update_unrealized_total_profit()

        step_reward = self.calculate_reward(action)
        self.total_reward += step_reward

        if self._is_valid(action):
            action_label = desired_position_label(action)
            transition = self._transition(action)
        else:
            action_label = "invalid"
            transition = None
        self.tensorboard_log(action_label, category="actions")

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
            "action_label": action_label,
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


class DesiredPositionReinforcementLearner(ReinforcementLearner):
    """Research-only RL-v2 runtime adapter; no execution configuration is declared here."""

    MyRLEnv = DesiredPositionEnvironment

    def pack_env_dict(self, pair: str) -> dict[str, Any]:
        env_info = super().pack_env_dict(pair)
        parameters = self.freqai_info.get("model_training_parameters", {})
        env_info["seed"] = int(parameters.get("seed", 42))
        env_info["fee"] = float(self.rl_config.get("training_fee", 0.002))
        return env_info
