from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.freqai.data_kitchen import FreqaiDataKitchen


TARGET = "&-future_return"
PREDICTION_ENV = "RESIDUAL_PYTORCH_M1_PREDICTION_DIR"
TRAINING_ENV = "RESIDUAL_PYTORCH_M1_TRAINING_DIR"


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-").lower()


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


class _RecordingLogger:
    def __init__(self, delegate: Any) -> None:
        self.delegate = delegate
        self.events: dict[str, list[dict[str, float | int]]] = {}

    def log_scalar(self, tag: str, scalar_value: float, step: int) -> None:
        self.events.setdefault(str(tag), []).append(
            {"step": int(step), "value": float(scalar_value)}
        )
        if self.delegate is not None:
            self.delegate.log_scalar(tag, scalar_value, step)

    def close(self) -> None:
        if self.delegate is not None:
            self.delegate.close()

    def __getattr__(self, name: str) -> Any:
        if self.delegate is None:
            raise AttributeError(name)
        return getattr(self.delegate, name)


class ResidualPyTorchM1EvidenceMixin:
    """Capture training and prediction evidence without changing model algorithms."""

    def fit(self, data_dictionary: dict[str, Any], dk: FreqaiDataKitchen, **kwargs) -> Any:
        training_root_value = os.environ.get(TRAINING_ENV)
        original_logger = getattr(self, "tb_logger", None)
        recorder = _RecordingLogger(original_logger)
        self.tb_logger = recorder

        model = super().fit(data_dictionary, dk, **kwargs)

        if not training_root_value:
            raise RuntimeError(f"{TRAINING_ENV} is required for bounded M1 model execution")
        training_root = Path(training_root_value)
        training_timerange = getattr(self, "training_timerange", None)
        payload: dict[str, Any] = {
            "schema_version": 1,
            "evidence_id": "residual-pytorch-m1-training-evidence-v1",
            "pair": dk.pair,
            "wrapper_model": self.__class__.__name__,
            "identifier": self.identifier,
            "training_start": (
                training_timerange.startdt.isoformat() if training_timerange is not None else None
            ),
            "training_stop_exclusive": (
                training_timerange.stopdt.isoformat() if training_timerange is not None else None
            ),
            "train_rows": len(data_dictionary["train_features"]),
            "test_rows": len(data_dictionary["test_features"]),
            "feature_count": int(data_dictionary["train_features"].shape[1]),
            "recorded_scalar_events": recorder.events,
            "model_training_parameters": self.freqai_info.get("model_training_parameters", {}),
            "historical_development_only": True,
            "winner_selection_allowed": False,
            "consumed_historical_oos_used": False,
            "protected_final_holdout_used": False,
        }
        if hasattr(model, "evals_result_"):
            payload["lightgbm_evals_result"] = model.evals_result_
        if hasattr(model, "best_score_"):
            payload["lightgbm_best_score"] = model.best_score_
        if hasattr(model, "model_meta_data"):
            payload["pytorch_model_meta_data"] = model.model_meta_data
        if hasattr(model, "best_val_loss"):
            best_val_loss = float(model.best_val_loss)
            payload["pytorch_best_val_loss"] = best_val_loss if np.isfinite(best_val_loss) else None
        if hasattr(model, "n_epochs"):
            payload["pytorch_declared_epochs"] = model.n_epochs

        output = training_root / f"{_slug(dk.pair)}.json"
        if output.exists():
            raise RuntimeError(f"Duplicate bounded M1 training evidence path: {output}")
        _write_json(output, payload)
        return model

    def predict(
        self,
        unfiltered_df: DataFrame,
        dk: FreqaiDataKitchen,
        **kwargs,
    ) -> tuple[DataFrame, np.ndarray]:
        pred_df, do_predict = super().predict(unfiltered_df, dk, **kwargs)
        prediction_root_value = os.environ.get(PREDICTION_ENV)
        if not prediction_root_value:
            raise RuntimeError(f"{PREDICTION_ENV} is required for bounded M1 model execution")
        if TARGET not in unfiltered_df or TARGET not in pred_df:
            raise RuntimeError("Bounded M1 prediction evidence requires the frozen target column")
        if len(pred_df) != len(unfiltered_df) or len(do_predict) != len(unfiltered_df):
            raise RuntimeError("Bounded M1 prediction evidence row counts differ")

        prediction_root = Path(prediction_root_value)
        evidence = pd.DataFrame(
            {
                "date": pd.to_datetime(unfiltered_df["date"], utc=True),
                "pair": dk.pair,
                "actual_target": pd.to_numeric(unfiltered_df[TARGET], errors="coerce").to_numpy(),
                "prediction": pd.to_numeric(pred_df[TARGET], errors="coerce").to_numpy(),
                "do_predict": np.asarray(do_predict, dtype=int),
            }
        )
        di_values = np.asarray(getattr(dk, "DI_values", np.zeros(len(evidence))), dtype=float)
        if di_values.shape[0] == len(evidence):
            evidence["di_value"] = di_values

        training_timerange = getattr(self, "training_timerange", None)
        suffix = "window"
        if training_timerange is not None:
            suffix = (
                f"{training_timerange.startdt.strftime('%Y%m%d')}-"
                f"{training_timerange.stopdt.strftime('%Y%m%d')}"
            )
        output = prediction_root / f"{_slug(dk.pair)}-{suffix}.csv"
        if output.exists():
            raise RuntimeError(f"Duplicate bounded M1 prediction evidence path: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(".csv.tmp")
        evidence.to_csv(temporary, index=False)
        temporary.replace(output)
        return pred_df, do_predict
