from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

from ai_platform.freqaimodels.LongOnlyReinforcementLearner import (
    LongOnlyEnvironment,
    LongOnlyReinforcementLearner,
)
from ai_platform.freqaimodels.SeededPyTorchMLPRegressor import SeededPyTorchMLPRegressor


class _NoOpTensorboardLogger:
    def log_scalar(self, *_args, **_kwargs) -> None:
        return None


class _NoOpCallback(BaseCallback):
    def _on_step(self) -> bool:
        return True


def _synthetic_features(rows: int = 32) -> pd.DataFrame:
    values = np.linspace(-0.75, 0.75, rows * 3, dtype=np.float32).reshape(rows, 3)
    return pd.DataFrame(values, columns=["feature_a", "feature_b", "feature_c"])


def _run_pytorch_smoke() -> dict[str, object]:
    features = _synthetic_features()
    labels = pd.DataFrame(
        (features.sum(axis=1) * 0.01).to_numpy(dtype=np.float32),
        columns=["target"],
    )

    model = object.__new__(SeededPyTorchMLPRegressor)
    model.research_seed = 42
    model.freqai_info = {"model_training_parameters": {"research_seed": 42}}
    model.learning_rate = 3e-4
    model.model_kwargs = {"hidden_dim": 8, "dropout_percent": 0.0, "n_layer": 1}
    model.trainer_kwargs = {"n_epochs": 1, "batch_size": 8, "early_stopping_patience": 0}
    model.device = "cpu"
    model.splits = ["train"]
    model.tb_logger = _NoOpTensorboardLogger()
    model.get_init_model = lambda _pair: None

    trainer = model.fit(
        {
            "train_features": features,
            "train_labels": labels,
        },
        SimpleNamespace(pair="SYNTHETIC/USDT"),
    )

    with torch.no_grad():
        prediction = trainer.model(torch.tensor(features.to_numpy(), dtype=torch.float32))

    if prediction.shape != (len(features), 1):
        raise RuntimeError(f"Unexpected PyTorch prediction shape: {tuple(prediction.shape)}")
    if not torch.isfinite(prediction).all():
        raise RuntimeError("PyTorch smoke produced non-finite predictions")

    return {
        "model": "SeededPyTorchMLPRegressor",
        "rows": len(features),
        "epochs": 1,
        "device": "cpu",
        "prediction_shape": list(prediction.shape),
    }


def _run_rl_smoke() -> dict[str, object]:
    features = _synthetic_features()
    rows = len(features)
    prices = pd.DataFrame(
        {
            "open": np.linspace(100.0, 101.0, rows, dtype=np.float32),
            "high": np.linspace(100.1, 101.1, rows, dtype=np.float32),
            "low": np.linspace(99.9, 100.9, rows, dtype=np.float32),
            "close": np.linspace(100.0, 101.0, rows, dtype=np.float32),
        }
    )
    config = {
        "stake_amount": 100,
        "freqai": {
            "rl_config": {
                "add_state_info": False,
                "max_training_drawdown_pct": 0.2,
                "max_trade_duration_candles": 16,
                "randomize_starting_position": False,
            }
        },
    }
    environment = LongOnlyEnvironment(
        df=features,
        prices=prices,
        reward_kwargs={"rr": 1.0, "profit_aim": 0.01},
        window_size=4,
        starting_point=True,
        id="synthetic-smoke",
        seed=42,
        config=config,
        live=False,
        fee=0.002,
        can_short=False,
        pair="SYNTHETIC/USDT",
        df_raw=prices.copy(),
    )
    observation, _ = environment.reset(seed=42)

    if LongOnlyReinforcementLearner.MyRLEnv is not LongOnlyEnvironment:
        raise RuntimeError("Canonical RL learner is not bound to LongOnlyEnvironment")
    if environment.action_space.n != 3:
        raise RuntimeError(f"Unexpected RL action count: {environment.action_space.n}")
    if observation.shape != (4, features.shape[1]):
        raise RuntimeError(f"Unexpected RL observation shape: {observation.shape}")

    learner = object.__new__(LongOnlyReinforcementLearner)
    learner.freqai_info = {
        "rl_config": {"train_cycles": 1},
        "model_training_parameters": {"n_steps": 8, "batch_size": 4, "seed": 42},
    }
    learner.rl_config = {"progress_bar": False}
    learner.net_arch = [8, 8]
    learner.policy_type = "MlpPolicy"
    learner.train_env = environment
    learner.activate_tensorboard = False
    learner.dd = SimpleNamespace(model_dictionary={})
    learner.continual_learning = False
    learner.MODELCLASS = PPO
    learner.eval_callback = _NoOpCallback()
    learner.tensorboard_callback = _NoOpCallback()

    with tempfile.TemporaryDirectory(prefix="freqai-rl-smoke-") as temp_dir:
        temp_path = Path(temp_dir)
        trained_model = learner.fit(
            {"train_features": features},
            SimpleNamespace(
                full_path=temp_path,
                data_path=temp_path,
                pair="SYNTHETIC/USDT",
            ),
        )

    if not isinstance(trained_model, PPO):
        raise RuntimeError(f"Unexpected RL model type: {type(trained_model).__name__}")

    return {
        "model": "LongOnlyReinforcementLearner",
        "backend": "PPO",
        "rows": rows,
        "train_cycles": 1,
        "actions": environment.action_space.n,
    }


def main() -> int:
    result = {
        "schema_version": 1,
        "data_source": "synthetic_only",
        "historical_oos_scored": False,
        "protected_final_holdout_used": False,
        "performance_conclusion_allowed": False,
        "pytorch": _run_pytorch_smoke(),
        "reinforcement_learning": _run_rl_smoke(),
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
