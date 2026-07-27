from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ai_platform.freqaimodels.ResidualPyTorchM1DataAuditRegressor import (
    build_raw_matrix_audit_with_freqai_filter_policy,
)
from ai_platform.scripts.residual_pytorch_bounded_m1_execution import (
    ResidualPyTorchBoundedM1Error,
    finalize_matrix_audit,
)


def _raw_frame() -> pd.DataFrame:
    rows = 2200
    target = np.linspace(-0.01, 0.01, rows)
    target[-12:] = np.nan
    feature = np.linspace(1.0, 2.0, rows)
    feature[100] = np.inf
    feature[101] = -np.inf
    feature[102] = np.nan
    return pd.DataFrame(
        {
            "date": pd.date_range("2025-12-01", periods=rows, freq="15min", tz="UTC"),
            "%volume-change": feature,
            "&-future_return": target,
        }
    )


def test_raw_infinity_is_recorded_and_filtered_before_fit() -> None:
    report = build_raw_matrix_audit_with_freqai_filter_policy(
        _raw_frame(),
        ["%volume-change"],
        ["&-future_return"],
        pair="BTC/USDT",
    )

    stats = report["feature_statistics"]["%volume-change"]
    assert stats["nan_count"] == 1
    assert stats["positive_infinity_count"] == 1
    assert stats["negative_infinity_count"] == 1
    assert stats["finite_count"] == 2197
    assert report["rows_with_any_feature_nonfinite"] == 3
    assert report["eligible_rows_before_split"] == 2185

    finalized = finalize_matrix_audit(
        report,
        {
            "train_features": np.ones((1700, 1)),
            "train_labels": np.ones((1700, 1)),
            "test_features": np.ones((400, 1)),
            "test_labels": np.ones((400, 1)),
        },
    )
    assert finalized["outcome"] == "audit_supported_for_bounded_m1"
    assert finalized["post_pipeline"]["splits"]["train"]["features_finite"] is True


def test_post_pipeline_infinity_still_fails_closed() -> None:
    report = build_raw_matrix_audit_with_freqai_filter_policy(
        _raw_frame(),
        ["%volume-change"],
        ["&-future_return"],
        pair="ETH/USDT",
    )
    train_features = np.ones((1700, 1))
    train_features[0, 0] = np.inf

    with pytest.raises(ResidualPyTorchBoundedM1Error, match="train transformed matrix is non-finite"):
        finalize_matrix_audit(
            report,
            {
                "train_features": train_features,
                "train_labels": np.ones((1700, 1)),
                "test_features": np.ones((400, 1)),
                "test_labels": np.ones((400, 1)),
            },
        )
