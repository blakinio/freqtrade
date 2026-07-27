from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import numpy as np
from pandas import DataFrame, to_numeric

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


def build_raw_matrix_audit_with_freqai_filter_policy(
    dataframe: DataFrame,
    feature_names: list[str],
    label_names: list[str],
    *,
    pair: str,
) -> dict[str, Any]:
    """Preserve raw non-finite counts while mirroring FreqAI's training filter."""
    raw_counts: dict[str, dict[str, int]] = {}
    normalized = dataframe.copy()
    for name in feature_names:
        numeric = to_numeric(dataframe[name], errors="coerce").to_numpy(dtype=float)
        raw_counts[name] = {
            "nan_count": int(np.isnan(numeric).sum()),
            "positive_infinity_count": int(np.isposinf(numeric).sum()),
            "negative_infinity_count": int(np.isneginf(numeric).sum()),
        }

    # FreqaiDataKitchen.filter_features() applies this exact normalization before
    # dropping non-finite training rows. The audit records the original counts,
    # while eligible-row and post-pipeline checks operate on the effective matrix.
    normalized[feature_names] = normalized[feature_names].replace(
        [np.inf, -np.inf],
        np.nan,
    )
    report = build_raw_matrix_audit(
        normalized,
        feature_names,
        label_names,
        pair=pair,
    )
    for name, counts in raw_counts.items():
        report["feature_statistics"][name].update(counts)
    return report


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
            self._raw_matrix_audit = build_raw_matrix_audit_with_freqai_filter_policy(
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
