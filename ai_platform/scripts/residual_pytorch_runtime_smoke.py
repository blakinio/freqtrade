"""Run the bounded synthetic-only lifecycle smoke for ResidualPyTorchRegressor."""

from __future__ import annotations

import argparse
import copy
import json
import platform
import tempfile
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
import torch

from ai_platform.freqaimodels.residual_mlp_components import ResidualMLPNetwork
from freqtrade.resolvers.freqaimodel_resolver import FreqaiModelResolver


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "ai_platform/configs/freqai-residual-pytorch-research.example.json"
MODEL_PATH = REPO_ROOT / "ai_platform/freqaimodels"
PAIR = "BTC/USDT"
TARGET = "&-future_return"
FEATURES = ["%feature_a", "%feature_b", "%feature_c", "%feature_d"]
SYNTHETIC_START = pd.Timestamp("2025-01-01T00:00:00Z")
HISTORICAL_OOS_START = pd.Timestamp("2026-05-01T00:00:00Z")
FINAL_HOLDOUT_START = pd.Timestamp("2026-08-01T00:00:00Z")
OUTCOMES = {"runtime_supported", "runtime_not_supported", "runtime_inconclusive"}


class RuntimeContractError(RuntimeError):
    """Raised when a required runtime property is demonstrably unsupported."""


class _NoopTensorboardLogger:
    def log_scalar(self, tag: str, scalar_value: float, step: int) -> None:
        del tag, scalar_value, step

    def close(self) -> None:
        return


class _IdentityFeaturePipeline:
    def transform(
        self,
        frame: pd.DataFrame,
        *args: Any,
        outlier_check: bool = False,
        **kwargs: Any,
    ) -> tuple[pd.DataFrame, np.ndarray, None]:
        del args, outlier_check, kwargs
        return frame.copy(), np.ones(len(frame), dtype=np.int_), None

    def __getitem__(self, key: str) -> None:
        if key != "di":
            raise KeyError(key)


class _IdentityLabelPipeline:
    def inverse_transform(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, None, None]:
        return frame.copy(), None, None


class _PredictionDataKitchen:
    def __init__(self) -> None:
        self.training_features_list = list(FEATURES)
        self.label_list = [TARGET]
        self.data_dictionary: dict[str, pd.DataFrame] = {}
        self.feature_pipeline = _IdentityFeaturePipeline()
        self.label_pipeline = _IdentityLabelPipeline()
        self.DI_values = np.array([], dtype=float)
        self.do_predict = np.array([], dtype=np.int_)

    def find_features(self, frame: pd.DataFrame) -> None:
        missing = [column for column in FEATURES if column not in frame.columns]
        if missing:
            raise RuntimeContractError(f"Prediction frame is missing features: {missing}")

    def filter_features(
        self,
        frame: pd.DataFrame,
        feature_list: list[str],
        training_filter: bool = False,
    ) -> tuple[pd.DataFrame, None]:
        del training_filter
        return frame.loc[:, feature_list].copy(), None


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeContractError(message)


def _load_config(user_data_dir: Path) -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    _require(config.get("dry_run") is True, "Runtime smoke requires dry_run=true")
    _require(
        config.get("freqai", {}).get("continual_learning") is False,
        "Runtime smoke requires continual_learning=false",
    )
    config["user_data_dir"] = user_data_dir
    config["freqaimodel"] = "ResidualPyTorchRegressor"
    config["freqaimodel_path"] = str(MODEL_PATH.resolve())
    config["freqai"]["activate_tensorboard"] = False
    return config


def _synthetic_data(train_rows: int = 192, test_rows: int = 96) -> dict[str, pd.DataFrame]:
    total_rows = train_rows + test_rows
    index = pd.date_range(SYNTHETIC_START, periods=total_rows, freq="15min")
    _require(index.max() < HISTORICAL_OOS_START, "Synthetic data reached historical OOS")
    _require(index.max() < FINAL_HOLDOUT_START, "Synthetic data reached protected holdout")

    phase = np.linspace(-2.0, 2.0, total_rows, dtype=np.float32)
    features = pd.DataFrame(
        {
            FEATURES[0]: phase,
            FEATURES[1]: np.sin(phase * np.pi),
            FEATURES[2]: np.cos(phase * np.pi),
            FEATURES[3]: np.square(phase),
        },
        index=index,
    )
    target = (
        0.35 * features[FEATURES[0]] - 0.15 * features[FEATURES[1]] + 0.05 * features[FEATURES[2]]
    ).astype(np.float32)
    labels = pd.DataFrame({TARGET: target}, index=index)
    return {
        "train_features": features.iloc[:train_rows].copy(),
        "train_labels": labels.iloc[:train_rows].copy(),
        "test_features": features.iloc[train_rows:].copy(),
        "test_labels": labels.iloc[train_rows:].copy(),
    }


def _resolve_model(config: dict[str, Any], device: str) -> Any:
    model: Any = FreqaiModelResolver.load_freqaimodel(config)
    _require(
        model.__class__.__name__ == "ResidualPyTorchRegressor",
        "FreqaiModelResolver returned the wrong model class",
    )
    model.device = device
    model.tb_logger = _NoopTensorboardLogger()
    return model


def _standalone_forward(model: Any, data: dict[str, pd.DataFrame], device: str) -> dict[str, Any]:
    network = ResidualMLPNetwork(
        input_dim=len(FEATURES),
        output_dim=1,
        **model.model_kwargs,
    ).to(device)
    network.eval()
    sample = torch.as_tensor(
        data["train_features"].iloc[:8].to_numpy(copy=True),
        dtype=torch.float32,
        device=device,
    )
    with torch.no_grad():
        output = network(sample)
    _require(tuple(output.shape) == (8, 1), "Standalone forward shape drifted")
    _require(torch.isfinite(output).all().item(), "Standalone forward produced non-finite output")
    return {
        "input_shape": list(sample.shape),
        "output_shape": list(output.shape),
    }


def _predict(model: Any, features: pd.DataFrame) -> np.ndarray:
    prediction_frame, do_predict = model.predict(features.copy(), _PredictionDataKitchen())
    predictions = prediction_frame[TARGET].to_numpy(dtype=np.float64)
    _require(predictions.shape == (len(features),), "Prediction shape drifted")
    _require(np.isfinite(predictions).all(), "Predictions contain non-finite values")
    _require(
        np.array_equal(do_predict, np.ones(len(features), dtype=np.int_)), "do_predict drifted"
    )
    return predictions


def _load_checkpoint(path: Path) -> tuple[Any, dict[str, Any]]:
    checkpoint = torch.load(path, weights_only=False)
    required = {
        "model_state_dict",
        "optimizer_state_dict",
        "model_meta_data",
        "pytrainer",
    }
    _require(required.issubset(checkpoint), "Checkpoint is missing required fields")
    trainer = checkpoint["pytrainer"].load_from_checkpoint(checkpoint)
    return trainer, checkpoint


def _state_snapshot(trainer: Any) -> dict[str, torch.Tensor]:
    state = {
        name: tensor.detach().cpu().clone() for name, tensor in trainer.model.state_dict().items()
    }
    _require(bool(state), "Trained state_dict is empty")
    _require(
        all(torch.isfinite(tensor).all().item() for tensor in state.values()),
        "Trained state contains non-finite values",
    )
    return state


def _train_lifecycle(root: Path, device: str) -> dict[str, Any]:
    config = _load_config(root / "user-data")
    data = _synthetic_data()
    wrapper = _resolve_model(config, device)
    forward = _standalone_forward(wrapper, data, device)
    trainer = wrapper.fit(data, SimpleNamespace(pair=PAIR))
    wrapper.model = trainer

    state = _state_snapshot(trainer)
    predictions_before = _predict(wrapper, data["test_features"])
    parameter_count = sum(parameter.numel() for parameter in trainer.model.parameters())
    _require(parameter_count > 0, "Parameter count is not positive")

    checkpoint_path = root / "residual-model.zip"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    trainer_logger = trainer.tb_logger
    trainer.tb_logger = None
    try:
        trainer.save(checkpoint_path)
    finally:
        trainer.tb_logger = trainer_logger
    _require(checkpoint_path.is_file(), "Checkpoint was not created")

    loaded_trainer, checkpoint = _load_checkpoint(checkpoint_path)
    metadata = checkpoint["model_meta_data"]
    _require(metadata.get("architecture") == "residual-mlp-v1", "Architecture metadata drifted")
    _require(metadata.get("input_dim") == len(FEATURES), "Input metadata drifted")
    _require(metadata.get("output_dim") == 1, "Output metadata drifted")
    _require(metadata.get("research_seed") == 42, "Seed metadata drifted")
    _require(metadata.get("parameter_count") == parameter_count, "Parameter metadata drifted")

    restored_wrapper = _resolve_model(copy.deepcopy(config), device)
    restored_wrapper.model = loaded_trainer
    predictions_after = _predict(restored_wrapper, data["test_features"])
    _require(
        np.array_equal(predictions_before, predictions_after),
        "Predictions changed after checkpoint restore",
    )

    return {
        "state": state,
        "predictions": predictions_before,
        "parameter_count": parameter_count,
        "forward": forward,
        "checkpoint_metadata": metadata,
        "checkpoint_size_bytes": checkpoint_path.stat().st_size,
    }


def _compare_repeated_runs(first: dict[str, Any], second: dict[str, Any]) -> None:
    first_state = first["state"]
    second_state = second["state"]
    _require(first_state.keys() == second_state.keys(), "Repeated state_dict keys drifted")
    _require(
        all(torch.equal(first_state[name], second_state[name]) for name in first_state),
        "Repeated training produced different parameters",
    )
    _require(
        np.array_equal(first["predictions"], second["predictions"]),
        "Repeated training produced different predictions",
    )


def _expect_failure(label: str, expected: tuple[type[BaseException], ...], action: Any) -> str:
    try:
        action()
    except expected as exc:
        return f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        raise RuntimeContractError(
            f"{label} failed with unexpected {type(exc).__name__}: {exc}"
        ) from exc
    raise RuntimeContractError(f"{label} did not fail closed")


def _fail_closed_checks(root: Path) -> dict[str, str]:
    config = _load_config(root / "fail-closed")
    data = _synthetic_data()

    def multiple_targets() -> None:
        model = _resolve_model(copy.deepcopy(config), "cpu")
        bad = copy.deepcopy(data)
        bad["train_labels"]["&-second-target"] = bad["train_labels"][TARGET]
        model.fit(bad, SimpleNamespace(pair=PAIR))

    def zero_features() -> None:
        model = _resolve_model(copy.deepcopy(config), "cpu")
        bad = copy.deepcopy(data)
        bad["train_features"] = bad["train_features"].iloc[:, :0]
        model.fit(bad, SimpleNamespace(pair=PAIR))

    def mismatched_rows() -> None:
        model = _resolve_model(copy.deepcopy(config), "cpu")
        bad = copy.deepcopy(data)
        bad["train_labels"] = bad["train_labels"].iloc[:-1]
        model.fit(bad, SimpleNamespace(pair=PAIR))

    def missing_checkpoint() -> None:
        _load_checkpoint(root / "missing-model.zip")

    def invalid_config() -> None:
        bad_config = copy.deepcopy(config)
        bad_config["freqai"]["model_training_parameters"]["learning_rate"] = 0
        _resolve_model(bad_config, "cpu")

    def continual_learning() -> None:
        bad_config = copy.deepcopy(config)
        bad_config["freqai"]["continual_learning"] = True
        _resolve_model(bad_config, "cpu")

    return {
        "multiple_targets": _expect_failure("multiple targets", (ValueError,), multiple_targets),
        "zero_features": _expect_failure("zero features", (ValueError,), zero_features),
        "mismatched_rows": _expect_failure("mismatched rows", (ValueError,), mismatched_rows),
        "missing_checkpoint": _expect_failure(
            "missing checkpoint", (FileNotFoundError,), missing_checkpoint
        ),
        "invalid_config": _expect_failure("invalid config", (ValueError,), invalid_config),
        "continual_learning": _expect_failure(
            "continual learning", (ValueError,), continual_learning
        ),
    }


def _device_lifecycle(root: Path, device: str) -> dict[str, Any]:
    first = _train_lifecycle(root / "first", device)
    second = _train_lifecycle(root / "second", device)
    _compare_repeated_runs(first, second)
    return {
        "status": "executed",
        "device": device,
        "same_seed_same_runtime_identical_parameters": True,
        "same_seed_same_runtime_identical_predictions": True,
        "save_load_prediction_identity": True,
        "parameter_count": first["parameter_count"],
        "forward": first["forward"],
        "checkpoint_metadata": first["checkpoint_metadata"],
        "checkpoint_size_bytes": first["checkpoint_size_bytes"],
    }


def _runtime_provenance() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }


def run_smoke() -> dict[str, Any]:
    previous_deterministic = torch.are_deterministic_algorithms_enabled()
    torch.use_deterministic_algorithms(True)
    try:
        with tempfile.TemporaryDirectory(prefix="residual-pytorch-runtime-smoke-") as tmp:
            root = Path(tmp)
            cpu = _device_lifecycle(root / "cpu", "cpu")
            cuda: dict[str, Any]
            if torch.cuda.is_available():
                cuda = _device_lifecycle(root / "cuda", "cuda")
            else:
                cuda = {
                    "status": "skipped",
                    "reason": "torch.cuda.is_available() returned false",
                }
            fail_closed = _fail_closed_checks(root)
    finally:
        torch.use_deterministic_algorithms(previous_deterministic)

    return {
        "schema_version": 1,
        "smoke_id": "residual-pytorch-runtime-smoke-v1",
        "outcome": "runtime_supported",
        "data_scope": "deterministic_synthetic_pre_oos_only",
        "synthetic_start": SYNTHETIC_START.isoformat(),
        "synthetic_end_before_historical_oos": True,
        "synthetic_end_before_protected_holdout": True,
        "market_data_used": False,
        "market_training_performed": False,
        "backtest_performed": False,
        "historical_oos_used": False,
        "protected_holdout_used": False,
        "profitability_scored": False,
        "model_parameters_changed": False,
        "resolver": "FreqaiModelResolver.load_freqaimodel",
        "runtime": _runtime_provenance(),
        "cpu": cpu,
        "cuda": cuda,
        "fail_closed": fail_closed,
    }


def _write_report(report: dict[str, Any], output: Path | None) -> None:
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        report = run_smoke()
        exit_code = 0
    except RuntimeContractError as exc:
        report = {
            "schema_version": 1,
            "smoke_id": "residual-pytorch-runtime-smoke-v1",
            "outcome": "runtime_not_supported",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "market_data_used": False,
            "backtest_performed": False,
            "historical_oos_used": False,
            "protected_holdout_used": False,
        }
        exit_code = 2
    except Exception as exc:
        report = {
            "schema_version": 1,
            "smoke_id": "residual-pytorch-runtime-smoke-v1",
            "outcome": "runtime_inconclusive",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "market_data_used": False,
            "backtest_performed": False,
            "historical_oos_used": False,
            "protected_holdout_used": False,
        }
        exit_code = 3

    _require(report["outcome"] in OUTCOMES, "Invalid runtime outcome")
    _write_report(report, args.output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
