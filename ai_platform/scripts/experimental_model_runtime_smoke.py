#!/usr/bin/env python3
"""Run bounded heavy-runtime integration smokes for canonical PyTorch and RL research models."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
import torch

from ai_platform.freqaimodels.LongOnlyReinforcementLearner import (
    LongOnlyActions,
    LongOnlyReinforcementLearner,
)
from ai_platform.freqaimodels.SeededPyTorchMLPRegressor import SeededPyTorchMLPRegressor


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTORCH_CONFIG = REPO_ROOT / "ai_platform/configs/freqai-pytorch-research.example.json"
RL_CONFIG = REPO_ROOT / "ai_platform/configs/freqai-rl-research.example.json"
TRAINING_WINDOW_START = pd.Timestamp("2025-12-01T00:00:00Z")
TRAINING_WINDOW_END_EXCLUSIVE = pd.Timestamp("2026-03-01T00:00:00Z")
HISTORICAL_OOS_START = pd.Timestamp("2026-05-01T00:00:00Z")
FINAL_HOLDOUT_START = pd.Timestamp("2026-08-01T00:00:00Z")


class _NoopTensorboardLogger:
    def log_scalar(self, tag: str, scalar_value: float, step: int) -> None:
        del tag, scalar_value, step

    def close(self) -> None:
        return


def _load_runtime_config(path: Path, user_data_dir: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("dry_run") is not True:
        raise RuntimeError(f"Heavy-runtime smoke requires dry_run=true: {path}")
    config["user_data_dir"] = user_data_dir
    config["freqai"]["activate_tensorboard"] = False
    return config


def _synthetic_index(rows: int) -> pd.DatetimeIndex:
    index = pd.date_range("2026-01-01T00:00:00Z", periods=rows, freq="15min")
    if index.min() < TRAINING_WINDOW_START or index.max() >= TRAINING_WINDOW_END_EXCLUSIVE:
        raise RuntimeError("Synthetic smoke data escaped the declared pre-OOS training window")
    if index.max() >= HISTORICAL_OOS_START or index.max() >= FINAL_HOLDOUT_START:
        raise RuntimeError("Synthetic smoke data reached a protected evaluation boundary")
    return index


def _pytorch_data(rows: int = 128) -> dict[str, pd.DataFrame]:
    index = _synthetic_index(rows * 2)
    x = np.linspace(-1.0, 1.0, rows * 2, dtype=np.float32)
    features = pd.DataFrame(
        {
            "%feature_a": x,
            "%feature_b": np.sin(x * np.pi),
            "%feature_c": np.cos(x * np.pi),
        },
        index=index,
    )
    labels = pd.DataFrame({"&target": 0.5 * x + 0.1}, index=index)
    return {
        "train_features": features.iloc[:rows].copy(),
        "train_labels": labels.iloc[:rows].copy(),
        "test_features": features.iloc[rows:].copy(),
        "test_labels": labels.iloc[rows:].copy(),
    }


def _train_pytorch_once(user_data_dir: Path) -> dict[str, torch.Tensor]:
    config = _load_runtime_config(PYTORCH_CONFIG, user_data_dir)
    model = SeededPyTorchMLPRegressor(config=config)
    model.tb_logger = _NoopTensorboardLogger()
    if model.research_seed != 42:
        raise RuntimeError("Canonical PyTorch research seed drifted")

    trainer = model.fit(_pytorch_data(), SimpleNamespace(pair="BTC/USDT"))
    state = {
        name: tensor.detach().cpu().clone()
        for name, tensor in trainer.model.state_dict().items()
    }
    if not state or not all(torch.isfinite(tensor).all().item() for tensor in state.values()):
        raise RuntimeError("PyTorch smoke produced missing or non-finite model parameters")
    return state


def _smoke_pytorch(root: Path) -> dict[str, Any]:
    first = _train_pytorch_once(root / "pytorch-first")
    second = _train_pytorch_once(root / "pytorch-second")
    if first.keys() != second.keys() or not all(
        torch.equal(first[name], second[name]) for name in first
    ):
        raise RuntimeError("Seeded PyTorch smoke was not reproducible within the same CPU runtime")
    return {
        "status": "pass",
        "seed": 42,
        "same_runtime_reproducible": True,
        "performance_scored": False,
    }


def _rl_frames(train_rows: int = 128, test_rows: int = 64) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    total_rows = train_rows + test_rows
    index = _synthetic_index(total_rows)
    phase = np.linspace(0.0, 4.0 * np.pi, total_rows, dtype=np.float32)
    features = pd.DataFrame(
        {
            "%feature_a": np.sin(phase),
            "%feature_b": np.cos(phase),
        },
        index=index,
    )
    base_price = 100.0 + np.linspace(0.0, 1.0, total_rows)
    raw = pd.DataFrame(
        {
            "open": base_price,
            "high": base_price + 0.2,
            "low": base_price - 0.2,
            "close": base_price + 0.05,
        },
        index=index,
    )
    data_dictionary = {
        "train_features": features.iloc[:train_rows].copy(),
        "test_features": features.iloc[train_rows:].copy(),
    }
    return (
        data_dictionary,
        raw.iloc[:train_rows].copy(),
        raw.iloc[train_rows:].copy(),
        raw.copy(),
    )


def _smoke_rl(root: Path) -> dict[str, Any]:
    config = _load_runtime_config(RL_CONFIG, root / "rl")
    learner = LongOnlyReinforcementLearner(config=config)
    learner.live = False
    learner.can_short = False

    if learner.MODELCLASS.__name__ != "PPO":
        raise RuntimeError("Canonical RL backend did not resolve Stable-Baselines3 PPO")

    data_dictionary, prices_train, prices_test, raw = _rl_frames()
    learner.df_raw = raw
    data_path = root / "rl-fit"
    data_path.mkdir(parents=True, exist_ok=True)
    dk = SimpleNamespace(pair="BTC/USDT", data_path=data_path, full_path=data_path)

    env_info = learner.pack_env_dict(dk.pair)
    if env_info.get("seed") != 42 or env_info.get("fee") != 0.002:
        raise RuntimeError("Canonical RL environment seed or fee drifted")

    probe_env = learner.MyRLEnv(
        df=data_dictionary["train_features"],
        prices=prices_train,
        **copy.deepcopy(env_info),
    )
    observation, _ = probe_env.reset()
    if probe_env.action_space.n != 3 or tuple(observation.shape) != (1, 2):
        raise RuntimeError("Canonical long-only RL action or observation contract drifted")
    probe_env.step(LongOnlyActions.Long_enter.value)
    probe_env.step(LongOnlyActions.Neutral.value)
    probe_env.step(LongOnlyActions.Long_exit.value)

    learner.set_train_and_eval_environments(
        data_dictionary,
        prices_train,
        prices_test,
        dk,
    )
    model = learner.fit(data_dictionary, dk)
    if model.__class__.__name__ != "PPO" or int(model.num_timesteps) < len(
        data_dictionary["train_features"]
    ):
        raise RuntimeError("Canonical RL fit did not complete the bounded PPO integration smoke")

    return {
        "status": "pass",
        "backend": "stable_baselines3",
        "algorithm": "PPO",
        "actions": 3,
        "seed": 42,
        "performance_scored": False,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ai-platform-heavy-runtime-") as tmp:
        root = Path(tmp)
        result = {
            "smoke_id": "experimental-model-heavy-runtime-smoke-v1",
            "data_scope": "synthetic_pre_oos_training_window_only",
            "data_end_before": TRAINING_WINDOW_END_EXCLUSIVE.isoformat(),
            "historical_oos_scored": False,
            "final_holdout_used": False,
            "phase6_member": False,
            "retuning_performed": False,
            "promotion_allowed": False,
            "profitability_claim_allowed": False,
            "pytorch": _smoke_pytorch(root),
            "rl": _smoke_rl(root),
        }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
