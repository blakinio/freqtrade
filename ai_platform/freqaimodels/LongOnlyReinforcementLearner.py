from __future__ import annotations

from enum import IntEnum
from typing import Any

from gymnasium import spaces

from freqtrade.freqai.RL.BaseEnvironment import BaseEnvironment, Positions
from freqtrade.freqai.prediction_models.ReinforcementLearner import ReinforcementLearner


class LongOnlyActions(IntEnum):
    Neutral = 0
    Long_enter = 1
    Long_exit = 2


class LongOnlyEnvironment(BaseEnvironment):
    """Three-action long-only research environment with no future-derived reward inputs."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.actions = LongOnlyActions

    def set_action_space(self) -> None:
        self.action_space = spaces.Discrete(len(LongOnlyActions))

    def step(self, action: int):
        self._done = False
        self._current_tick += 1
        if self._current_tick >= self._end_tick:
            self._done = True

        self._update_unrealized_total_profit()
        step_reward = self.calculate_reward(action)
        self.total_reward += step_reward
        self.tensorboard_log(LongOnlyActions(action).name, category="actions")

        trade_type = None
        trade_profit = self.get_unrealized_profit()
        if self.is_tradesignal(action):
            if action == LongOnlyActions.Long_enter.value:
                self._position = Positions.Long
                self._last_trade_tick = self._current_tick
                trade_type = "enter_long"
            elif action == LongOnlyActions.Long_exit.value:
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

        if (
            self._total_profit < self.max_drawdown
            or self._total_unrealized_profit < self.max_drawdown
        ):
            self._done = True

        self._position_history.append(self._position)
        info = {
            "tick": self._current_tick,
            "action": action,
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
        return (
            action == LongOnlyActions.Long_enter.value and self._position == Positions.Neutral
        ) or (action == LongOnlyActions.Long_exit.value and self._position == Positions.Long)

    def _is_valid(self, action: int) -> bool:
        if action == LongOnlyActions.Long_enter.value:
            return self._position == Positions.Neutral
        if action == LongOnlyActions.Long_exit.value:
            return self._position == Positions.Long
        return action == LongOnlyActions.Neutral.value

    def calculate_reward(self, action: int) -> float:
        """Reward only valid long-only actions using realized state at the environment step."""
        if not self._is_valid(action):
            return -1.0
        if action == LongOnlyActions.Long_exit.value:
            return float(self.get_unrealized_profit() * 100.0)
        if action == LongOnlyActions.Neutral.value and self._position == Positions.Long:
            max_duration = max(int(self.rl_config.get("max_trade_duration_candles", 96)), 1)
            duration_ratio = min(self.get_trade_duration() / max_duration, 1.0)
            return float(-0.01 * duration_ratio)
        return 0.0


class LongOnlyReinforcementLearner(ReinforcementLearner):
    """Research-only PPO integration using a deterministic long-only environment contract."""

    MyRLEnv = LongOnlyEnvironment

    def pack_env_dict(self, pair: str) -> dict[str, Any]:
        env_info = super().pack_env_dict(pair)
        parameters = self.freqai_info.get("model_training_parameters", {})
        env_info["seed"] = int(parameters.get("seed", 42))
        env_info["fee"] = float(self.rl_config.get("training_fee", 0.002))
        return env_info
