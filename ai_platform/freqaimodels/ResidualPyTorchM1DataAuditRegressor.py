from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import numpy as np
from pandas import DataFrame

from ai_platform.scripts.residual_pytorch_bounded_m1_execution import (
    ResidualPyTorchBoundedM1Error,
    build_raw_matrix_audit,
    finalize_matrix_audit,
    write_json,
)
from freqtrade.freqai.base_models.BaseRegressionModel import BaseRegressionModel
from freqtrade.freqai.data_kitchen import FreqaiDataKitchen


AUDIT_ENV = "RESIDUAL_PYTORCH_M1_AUDIT_DIR"


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-").lower()


class _ZeroRegressor:
    def predict(self, features: Any) -> np.ndarray:
        return np.zeros(len(features), dtype=float)


class ResidualPyTorchM1DataAuditRegressor(BaseRegressionModel):
    """Audit the real expanded matrix before any bounded M1 comparator is fitted."""

    def train(
        self,
        unfiltered_df: DataFrame,
        pair: str,
        dk: FreqaiDataKitchen,
        **kwargs,
    ) -> Any:
        try:
            self._raw_matrix_audit = build_raw_matrix_audit(
                unfiltered_df,
                list(dk.training_features_list),
                list(dk.label_list),
                pair=pair,
            )
        except ResidualPyTorchBoundedM1Error as exc:
            raise ValueError(str(exc)) from exc
        return super().train(unfiltered_df, pair, dk, **kwargs)

    def fit(self, data_dictionary: dict[str, Any], dk: FreqaiDataKitchen, **kwargs) -> Any:
        raw_audit = getattr(self, "_raw_matrix_audit", None)
        if not isinstance(raw_audit, dict):
            raise ValueError("Raw expanded matrix audit did not run before fit")
        try:
            report = finalize_matrix_audit(raw_audit, data_dictionary)
        except ResidualPyTorchBoundedM1Error as exc:
            raise ValueError(str(exc)) from exc

        audit_root_value = os.environ.get(AUDIT_ENV)
        if not audit_root_value:
            raise ValueError(f"{AUDIT_ENV} is required for bounded M1 matrix audit")
        output = Path(audit_root_value) / f"{_slug(dk.pair)}.json"
        if output.exists():
            raise ValueError(f"Duplicate bounded M1 audit path: {output}")
        write_json(output, report)
        return _ZeroRegressor()
