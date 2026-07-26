#!/usr/bin/env python3
"""Validate and summarize the bounded residual PyTorch M1 development execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REPO_PATH = (
    "ai_platform/experimental_model_research/"
    "residual-pytorch-bounded-m1-execution-contract-v1.json"
)
CONTRACT_PATH = REPO_ROOT / CONTRACT_REPO_PATH
REQUEST_REPO_PATH = (
    "ai_platform/experimental_model_research/run-requests/"
    "residual-pytorch-bounded-m1-execution-v1.json"
)
TASK_REPO_PATH = (
    "docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md"
)
TARGET = "&-future_return"
TRAINING_START = "2025-12-01T00:00:00Z"
TRAINING_STOP_EXCLUSIVE = "2026-03-01T00:00:00Z"
DEVELOPMENT_START = "2026-03-01T00:00:00Z"
DEVELOPMENT_STOP_EXCLUSIVE = "2026-05-01T00:00:00Z"
CONSUMED_OOS_START = "2026-05-01T00:00:00Z"
PROTECTED_HOLDOUT = "20260801-20260930"
EXECUTION_TIMERANGE = "20260301-20260501"
DOWNLOAD_TIMERANGE = "20250801-20260501"
EXPECTED_PAIRS = ["BTC/USDT", "ETH/USDT"]
EXPECTED_TIMEFRAMES = ["15m", "1h", "4h"]
TIMEFRAME_SECONDS = {"15m": 15 * 60, "1h": 60 * 60, "4h": 4 * 60 * 60}
EXPECTED_FEE = 0.002
EXPECTED_HORIZON = 12
EXPECTED_FEATURE_PARAMETERS = {
    "include_timeframes": EXPECTED_TIMEFRAMES,
    "include_corr_pairlist": EXPECTED_PAIRS,
    "label_period_candles": EXPECTED_HORIZON,
    "include_shifted_candles": 2,
    "DI_threshold": 1.0,
    "weight_factor": 0.9,
    "principal_component_analysis": False,
    "use_SVM_to_remove_outliers": False,
    "use_DBSCAN_to_remove_outliers": False,
    "indicator_periods_candles": [14, 50],
    "plot_feature_importances": 0,
    "shuffle_after_split": False,
    "buffer_train_data_candles": 0,
}
EXPECTED_SPLIT_PARAMETERS = {
    "test_size": 0.2,
    "random_state": 42,
    "shuffle": False,
}
EXPECTED_TRACKS = {
    "residual-pytorch-m1-lightgbm-v1": {
        "config": "ai_platform/configs/freqai-residual-pytorch-m1-lightgbm.example.json",
        "manifest": "ai_platform/experiments/residual-pytorch-m1-lightgbm-v1.json",
        "freqai_model": "M1LightGBMRegressor",
        "model_file": "ai_platform/freqaimodels/M1LightGBMRegressor.py",
        "underlying_model_file": "freqtrade/freqai/prediction_models/LightGBMRegressor.py",
        "identifier": "ai-platform-residual-pytorch-m1-lightgbm-v1",
        "model_training_parameters": {
            "n_estimators": 400,
            "learning_rate": 0.03,
            "num_leaves": 31,
            "n_jobs": -1,
            "random_state": 42,
            "deterministic": True,
            "force_col_wise": True,
            "verbosity": -1,
        },
    },
    "residual-pytorch-m1-seeded-mlp-v1": {
        "config": "ai_platform/configs/freqai-residual-pytorch-m1-seeded-mlp.example.json",
        "manifest": "ai_platform/experiments/residual-pytorch-m1-seeded-mlp-v1.json",
        "freqai_model": "M1SeededPyTorchMLPRegressor",
        "model_file": "ai_platform/freqaimodels/M1SeededPyTorchMLPRegressor.py",
        "underlying_model_file": "ai_platform/freqaimodels/SeededPyTorchMLPRegressor.py",
        "identifier": "ai-platform-residual-pytorch-m1-seeded-mlp-v1",
        "model_training_parameters": {
            "research_seed": 42,
            "learning_rate": 0.0003,
            "trainer_kwargs": {
                "n_epochs": 3,
                "batch_size": 64,
                "early_stopping_patience": 0,
            },
            "model_kwargs": {
                "hidden_dim": 64,
                "dropout_percent": 0.0,
                "n_layer": 1,
            },
        },
    },
    "residual-pytorch-m1-residual-mlp-v1": {
        "config": "ai_platform/configs/freqai-residual-pytorch-m1-residual-mlp.example.json",
        "manifest": "ai_platform/experiments/residual-pytorch-m1-residual-mlp-v1.json",
        "freqai_model": "M1ResidualPyTorchRegressor",
        "model_file": "ai_platform/freqaimodels/M1ResidualPyTorchRegressor.py",
        "underlying_model_file": "ai_platform/freqaimodels/ResidualPyTorchRegressor.py",
        "identifier": "ai-platform-residual-pytorch-m1-residual-mlp-v1",
        "model_training_parameters": {
            "research_seed": 42,
            "learning_rate": 0.0003,
            "weight_decay": 0.0001,
            "loss_beta": 0.01,
            "trainer_kwargs": {
                "n_epochs": 8,
                "batch_size": 64,
                "early_stopping_patience": 2,
            },
            "model_kwargs": {
                "hidden_dim": 128,
                "n_blocks": 3,
                "expansion_factor": 2,
                "dropout_percent": 0.1,
                "residual_scale": 1.0,
            },
        },
    },
}
EXPECTED_AUDIT_TRACK = {
    "track_id": "residual-pytorch-m1-data-audit-v1",
    "config": "ai_platform/configs/freqai-residual-pytorch-m1-data-audit.example.json",
    "manifest": "ai_platform/experiments/residual-pytorch-m1-data-audit-v1.json",
    "freqai_model": "ResidualPyTorchM1DataAuditRegressor",
    "model_file": "ai_platform/freqaimodels/ResidualPyTorchM1DataAuditRegressor.py",
    "identifier": "ai-platform-residual-pytorch-m1-data-audit-v1",
}


class ResidualPyTorchBoundedM1Error(RuntimeError):
    """Raised when bounded M1 inputs or evidence drift from the frozen contract."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResidualPyTorchBoundedM1Error(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ResidualPyTorchBoundedM1Error(f"{label} must contain a JSON object")
    return payload


def _repo_path(value: str) -> Path:
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ResidualPyTorchBoundedM1Error(
            f"Repository path escapes root: {value}"
        ) from exc
    return candidate


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ResidualPyTorchBoundedM1Error(f"Unable to hash {path}: {exc}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = _read_json(path, "bounded M1 execution contract")
    validate_contract(contract)
    return contract


def validate_contract(contract: dict[str, Any]) -> None:  # noqa: C901
    if contract.get("schema_version") != 1:
        raise ResidualPyTorchBoundedM1Error("Contract schema_version must be 1")
    if contract.get("contract_id") != "residual-pytorch-bounded-m1-execution-v1":
        raise ResidualPyTorchBoundedM1Error("Contract identity drifted")
    if contract.get("task") != TASK_REPO_PATH:
        raise ResidualPyTorchBoundedM1Error("Task path drifted")
    if contract.get("request_path") != REQUEST_REPO_PATH:
        raise ResidualPyTorchBoundedM1Error("Request path drifted")

    expected_trigger = {
        "event": "pull_request_opened",
        "base_branch": "develop",
        "exact_one_file": True,
    }
    if contract.get("trigger") != expected_trigger:
        raise ResidualPyTorchBoundedM1Error("One-shot trigger contract drifted")

    expected_geometry = {
        "training_window": "20251201-20260228",
        "training_start": TRAINING_START,
        "training_stop_exclusive": TRAINING_STOP_EXCLUSIVE,
        "development_window": "20260301-20260430",
        "development_start": DEVELOPMENT_START,
        "development_stop_exclusive": DEVELOPMENT_STOP_EXCLUSIVE,
        "timerange": EXECUTION_TIMERANGE,
        "download_timerange": DOWNLOAD_TIMERANGE,
        "train_period_days": 90,
        "backtest_period_days": 61,
        "executions_per_track": 1,
    }
    if contract.get("geometry") != expected_geometry:
        raise ResidualPyTorchBoundedM1Error("Temporal geometry drifted")

    expected_market = {
        "exchange": "kraken",
        "pairs": EXPECTED_PAIRS,
        "timeframes": EXPECTED_TIMEFRAMES,
        "fee": EXPECTED_FEE,
        "cache_namespace": "residual-pytorch-m1-pre-may-v1",
        "fallback_cache_restore_allowed": False,
    }
    if contract.get("market_data") != expected_market:
        raise ResidualPyTorchBoundedM1Error("Market-data contract drifted")

    expected_feature_target = {
        "strategy": "AiFrozenCandidateStrategy",
        "strategy_file": "ai_platform/strategies/AiFrozenCandidateStrategy.py",
        "target": TARGET,
        "target_horizon_candles": EXPECTED_HORIZON,
        "target_offsets": list(range(1, EXPECTED_HORIZON + 1)),
        "entry_prediction_threshold": 0.006,
        "exit_prediction_threshold": -0.009,
        "feature_parameters": EXPECTED_FEATURE_PARAMETERS,
        "data_split_parameters": EXPECTED_SPLIT_PARAMETERS,
        "liquidation_features_allowed": False,
    }
    if contract.get("feature_target_contract") != expected_feature_target:
        raise ResidualPyTorchBoundedM1Error("Feature/target contract drifted")

    if contract.get("audit_track") != EXPECTED_AUDIT_TRACK:
        raise ResidualPyTorchBoundedM1Error("Audit track drifted")

    tracks = contract.get("tracks")
    if not isinstance(tracks, list) or len(tracks) != len(EXPECTED_TRACKS):
        raise ResidualPyTorchBoundedM1Error("Contract must contain exactly three model tracks")
    actual_tracks = {track.get("track_id"): track for track in tracks if isinstance(track, dict)}
    expected_tracks = {
        track_id: {
            "track_id": track_id,
            "config": values["config"],
            "manifest": values["manifest"],
            "freqai_model": values["freqai_model"],
            "model_file": values["model_file"],
            "underlying_model_file": values["underlying_model_file"],
            "identifier": values["identifier"],
            "model_training_parameters": values["model_training_parameters"],
        }
        for track_id, values in EXPECTED_TRACKS.items()
    }
    if actual_tracks != expected_tracks:
        raise ResidualPyTorchBoundedM1Error("Model track set or parameters drifted")

    expected_audit = {
        "required_before_model_execution": True,
        "raw_expanded_feature_count_required": True,
        "per_column_nonfinite_counts_required": True,
        "iqr_outlier_diagnostics_required": True,
        "target_distribution_required": True,
        "target_trailing_null_rows": EXPECTED_HORIZON,
        "minimum_eligible_rows_per_pair": 1000,
        "cross_pair_feature_identity_required": True,
    }
    if contract.get("data_audit") != expected_audit:
        raise ResidualPyTorchBoundedM1Error("Data-audit contract drifted")

    expected_consumed = {
        "timerange": "20260501-20260630",
        "start": CONSUMED_OOS_START,
        "usage": "forbidden",
    }
    if contract.get("consumed_historical_oos") != expected_consumed:
        raise ResidualPyTorchBoundedM1Error("Consumed historical OOS boundary drifted")
    expected_holdout = {
        "timerange": PROTECTED_HOLDOUT,
        "used": False,
        "usage": "forbidden",
    }
    if contract.get("protected_final_holdout") != expected_holdout:
        raise ResidualPyTorchBoundedM1Error("Protected holdout boundary drifted")

    expected_phase6 = {
        "member": False,
        "may_change_candidates": False,
        "may_change_selection_policy": False,
        "may_consume_results": False,
        "selected_model_remains_null": True,
    }
    if contract.get("phase6_isolation") != expected_phase6:
        raise ResidualPyTorchBoundedM1Error("Phase 6 isolation drifted")

    expected_authorization = {
        "historical_development_data_access": True,
        "matrix_audit_allowed": True,
        "training_allowed": True,
        "backtesting_allowed": True,
        "historical_oos_used": False,
        "final_holdout_used": False,
        "hyperopt_allowed": False,
        "retuning_allowed": False,
        "feature_changes_allowed": False,
        "threshold_changes_allowed": False,
        "liquidation_features_allowed": False,
        "winner_selection_allowed": False,
        "promotion_allowed": False,
        "live_trading_allowed": False,
        "profitability_claim_allowed": False,
        "superiority_claim_allowed": False,
    }
    if contract.get("authorization") != expected_authorization:
        raise ResidualPyTorchBoundedM1Error("Authorization contract drifted")

    serialized = json.dumps(contract, sort_keys=True)
    if "20260701" in serialized:
        raise ResidualPyTorchBoundedM1Error(
            "Forbidden post-development execution boundary leaked: 20260701"
        )


def _load_and_validate_config(track: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
    config = _read_json(_repo_path(track["config"]), f"{track['track_id']} config")
    if config.get("dry_run") is not True:
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} must remain dry_run")
    if config.get("initial_state") != "stopped":
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} must start stopped")
    exchange = config.get("exchange", {})
    if exchange.get("name") != "kraken":
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} exchange drifted")
    if exchange.get("key") or exchange.get("secret"):
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} contains credentials")
    if exchange.get("pair_whitelist") != EXPECTED_PAIRS:
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} pair universe drifted")

    freqai = config.get("freqai", {})
    expected_common = {
        "enabled": True,
        "override_exchange_checks": True,
        "purge_old_models": 2,
        "train_period_days": 90,
        "backtest_period_days": 61,
        "save_backtest_models": True,
        "continual_learning": False,
        "activate_tensorboard": True,
        "identifier": track["identifier"],
        "feature_parameters": EXPECTED_FEATURE_PARAMETERS,
        "data_split_parameters": EXPECTED_SPLIT_PARAMETERS,
        "model_training_parameters": track.get("model_training_parameters", {"research_seed": 42}),
    }
    for field, expected in expected_common.items():
        if freqai.get(field) != expected:
            raise ResidualPyTorchBoundedM1Error(
                f"{track['track_id']} config field {field} drifted"
            )
    return config


def _load_and_validate_manifest(track: dict[str, Any]) -> dict[str, Any]:
    manifest = _read_json(_repo_path(track["manifest"]), f"{track['track_id']} manifest")
    expected = {
        "schema_version": 1,
        "experiment_id": track["track_id"],
        "config": track["config"],
        "strategy": "AiFrozenCandidateStrategy",
        "strategy_path": "ai_platform/strategies",
        "freqai_model": track["freqai_model"],
        "timerange": EXECUTION_TIMERANGE,
        "download_timerange": DOWNLOAD_TIMERANGE,
        "pairs": EXPECTED_PAIRS,
        "timeframes": EXPECTED_TIMEFRAMES,
        "fee": EXPECTED_FEE,
    }
    for field, expected_value in expected.items():
        if manifest.get(field) != expected_value:
            raise ResidualPyTorchBoundedM1Error(
                f"{track['track_id']} manifest field {field} drifted"
            )
    output_root = manifest.get("output_root")
    if not isinstance(output_root, str) or not output_root.startswith(
        "ai_platform/artifacts/experimental-model-research/residual-pytorch-m1/"
    ):
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} output root drifted")
    return manifest


def canonical_inputs() -> dict[str, Any]:
    contract = load_contract()
    tracks = [contract["audit_track"], *contract["tracks"]]
    resolved: list[dict[str, Any]] = []
    for track in tracks:
        config = _load_and_validate_config(track)
        manifest = _load_and_validate_manifest(track)
        model_path = _repo_path(track["model_file"])
        if not model_path.is_file():
            raise ResidualPyTorchBoundedM1Error(f"Missing model file: {model_path}")
        resolved.append({"track": track, "config": config, "manifest": manifest})

    strategy_path = _repo_path("ai_platform/strategies/AiFrozenCandidateStrategy.py")
    instrumentation_path = _repo_path(
        "ai_platform/freqaimodels/residual_pytorch_m1_instrumentation.py"
    )
    for path in (strategy_path, instrumentation_path):
        if not path.is_file():
            raise ResidualPyTorchBoundedM1Error(f"Missing canonical input: {path}")

    return {
        "contract": contract,
        "tracks": resolved,
        "strategy_path": strategy_path,
        "instrumentation_path": instrumentation_path,
    }


def build_contract_report() -> dict[str, Any]:
    inputs = canonical_inputs()
    return {
        "schema_version": 1,
        "contract_id": inputs["contract"]["contract_id"],
        "status": "infrastructure_ready_execution_not_requested",
        "timerange": EXECUTION_TIMERANGE,
        "download_timerange": DOWNLOAD_TIMERANGE,
        "training_window": "20251201-20260228",
        "development_window": "20260301-20260430",
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
        "phase6_member": False,
        "tracks": [item["track"]["track_id"] for item in inputs["tracks"]],
        "run_request_present": _repo_path(REQUEST_REPO_PATH).exists(),
    }


def _finite_quantile(values: np.ndarray, q: float) -> float | None:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return None
    return float(np.quantile(finite, q))


def _series_stats(series: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    finite_mask = np.isfinite(numeric)
    finite = numeric[finite_mask]
    nan_count = int(np.isnan(numeric).sum())
    positive_infinity_count = int(np.isposinf(numeric).sum())
    negative_infinity_count = int(np.isneginf(numeric).sum())

    if finite.size:
        q1 = float(np.quantile(finite, 0.25))
        q3 = float(np.quantile(finite, 0.75))
        iqr = q3 - q1
        if iqr > 0:
            outlier_mask = (finite < q1 - 1.5 * iqr) | (finite > q3 + 1.5 * iqr)
            outlier_count = int(outlier_mask.sum())
        else:
            outlier_count = 0
        mean = float(np.mean(finite))
        standard_deviation = float(np.std(finite))
        minimum = float(np.min(finite))
        maximum = float(np.max(finite))
    else:
        iqr = 0.0
        outlier_count = 0
        mean = standard_deviation = minimum = maximum = None

    return {
        "rows": int(numeric.size),
        "finite_count": int(finite.size),
        "nan_count": nan_count,
        "positive_infinity_count": positive_infinity_count,
        "negative_infinity_count": negative_infinity_count,
        "minimum": minimum,
        "q01": _finite_quantile(numeric, 0.01),
        "q25": _finite_quantile(numeric, 0.25),
        "median": _finite_quantile(numeric, 0.5),
        "q75": _finite_quantile(numeric, 0.75),
        "q99": _finite_quantile(numeric, 0.99),
        "maximum": maximum,
        "mean": mean,
        "standard_deviation": standard_deviation,
        "iqr": iqr,
        "iqr_outlier_count": outlier_count,
        "iqr_outlier_ratio": float(outlier_count / finite.size) if finite.size else None,
    }


def _consecutive_nulls(mask: np.ndarray, *, from_end: bool) -> int:
    values = mask[::-1] if from_end else mask
    count = 0
    for value in values:
        if not bool(value):
            break
        count += 1
    return count


def build_raw_matrix_audit(
    dataframe: pd.DataFrame,
    feature_names: list[str],
    label_names: list[str],
    *,
    pair: str,
) -> dict[str, Any]:  # noqa: C901
    """Audit the exact expanded raw training matrix before FreqAI filtering and fitting."""
    if pair not in EXPECTED_PAIRS:
        raise ResidualPyTorchBoundedM1Error(f"Unexpected audit pair: {pair}")
    if label_names != [TARGET]:
        raise ResidualPyTorchBoundedM1Error("Audit requires exactly the frozen target")
    if not feature_names or len(feature_names) != len(set(feature_names)):
        raise ResidualPyTorchBoundedM1Error("Expanded feature list is empty or duplicated")
    if any("liquid" in feature.lower() for feature in feature_names):
        raise ResidualPyTorchBoundedM1Error("Liquidation-derived feature entered bounded M1")
    missing = [name for name in ["date", *feature_names, TARGET] if name not in dataframe]
    if missing:
        raise ResidualPyTorchBoundedM1Error(
            "Expanded matrix is missing columns: " + ", ".join(missing)
        )

    dates = pd.to_datetime(dataframe["date"], utc=True, errors="raise")
    start = pd.Timestamp(TRAINING_START)
    stop = pd.Timestamp(TRAINING_STOP_EXCLUSIVE)
    authorized_mask = (dates >= start) & (dates < stop)
    frame = dataframe.loc[authorized_mask, ["date", *feature_names, TARGET]].copy()
    frame_dates = pd.to_datetime(frame["date"], utc=True, errors="raise")
    if frame.empty:
        raise ResidualPyTorchBoundedM1Error("Authorized training matrix is empty")
    if not frame_dates.is_monotonic_increasing:
        raise ResidualPyTorchBoundedM1Error("Authorized training dates are not chronological")
    if frame_dates.min() != start:
        raise ResidualPyTorchBoundedM1Error(
            f"Training matrix starts at {frame_dates.min().isoformat()}, expected {TRAINING_START}"
        )
    if frame_dates.max() >= stop:
        raise ResidualPyTorchBoundedM1Error("Training matrix crossed the exclusive March boundary")

    feature_stats = {name: _series_stats(frame[name]) for name in feature_names}
    for name, stats in feature_stats.items():
        if stats["finite_count"] == 0:
            raise ResidualPyTorchBoundedM1Error(f"Expanded feature {name} has no finite values")
        if stats["positive_infinity_count"] or stats["negative_infinity_count"]:
            raise ResidualPyTorchBoundedM1Error(f"Expanded feature {name} contains infinity")

    target_stats = _series_stats(frame[TARGET])
    if target_stats["positive_infinity_count"] or target_stats["negative_infinity_count"]:
        raise ResidualPyTorchBoundedM1Error("Target contains infinity")
    target_null_mask = pd.isna(pd.to_numeric(frame[TARGET], errors="coerce")).to_numpy()
    leading_null_rows = _consecutive_nulls(target_null_mask, from_end=False)
    trailing_null_rows = _consecutive_nulls(target_null_mask, from_end=True)
    if trailing_null_rows != EXPECTED_HORIZON:
        raise ResidualPyTorchBoundedM1Error(
            f"Target trailing-null geometry drifted: {trailing_null_rows}"
        )

    feature_numeric = frame[feature_names].apply(pd.to_numeric, errors="coerce")
    feature_values = feature_numeric.to_numpy(dtype=float)
    label_values = pd.to_numeric(frame[TARGET], errors="coerce").to_numpy(dtype=float)
    finite_feature_rows = np.isfinite(feature_values).all(axis=1)
    finite_label_rows = np.isfinite(label_values)
    eligible_rows = int((finite_feature_rows & finite_label_rows).sum())
    if eligible_rows < 1000:
        raise ResidualPyTorchBoundedM1Error(
            f"Too few eligible training rows before split: {eligible_rows}"
        )

    feature_name_basis = "\n".join(feature_names).encode()
    return {
        "schema_version": 1,
        "audit_id": "residual-pytorch-m1-raw-expanded-matrix-v1",
        "pair": pair,
        "training_start": TRAINING_START,
        "training_stop_exclusive": TRAINING_STOP_EXCLUSIVE,
        "raw_rows": int(len(frame)),
        "expanded_feature_count": len(feature_names),
        "expanded_feature_names": feature_names,
        "expanded_feature_names_sha256": hashlib.sha256(feature_name_basis).hexdigest(),
        "rows_with_any_feature_nonfinite": int((~finite_feature_rows).sum()),
        "eligible_rows_before_split": eligible_rows,
        "feature_statistics": feature_stats,
        "target": {
            "name": TARGET,
            "statistics": target_stats,
            "leading_null_rows": leading_null_rows,
            "trailing_null_rows": trailing_null_rows,
        },
        "iqr_outlier_method": "outside_[Q1-1.5*IQR,Q3+1.5*IQR]",
        "liquidation_features_used": False,
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
        "outcome": "raw_matrix_supported",
    }


def finalize_matrix_audit(
    raw_audit: dict[str, Any],
    data_dictionary: dict[str, Any],
) -> dict[str, Any]:
    """Add post-filter, split and pipeline evidence immediately before the audit model returns."""
    result = dict(raw_audit)
    splits: dict[str, dict[str, Any]] = {}
    transformed_feature_count: int | None = None
    for split in ("train", "test"):
        features = np.asarray(data_dictionary[f"{split}_features"], dtype=float)
        labels = np.asarray(data_dictionary[f"{split}_labels"], dtype=float)
        if features.ndim != 2 or labels.ndim != 2 or labels.shape[1] != 1:
            raise ResidualPyTorchBoundedM1Error(f"{split} transformed matrix shape drifted")
        if features.shape[0] < 1 or features.shape[1] < 1:
            raise ResidualPyTorchBoundedM1Error(f"{split} transformed matrix is empty")
        if features.shape[0] != labels.shape[0]:
            raise ResidualPyTorchBoundedM1Error(f"{split} feature/label row counts differ")
        if not np.isfinite(features).all() or not np.isfinite(labels).all():
            raise ResidualPyTorchBoundedM1Error(f"{split} transformed matrix is non-finite")
        if transformed_feature_count is None:
            transformed_feature_count = int(features.shape[1])
        elif transformed_feature_count != int(features.shape[1]):
            raise ResidualPyTorchBoundedM1Error("Train/test transformed feature counts differ")
        splits[split] = {
            "rows": int(features.shape[0]),
            "feature_count": int(features.shape[1]),
            "label_count": int(labels.shape[1]),
            "features_finite": True,
            "labels_finite": True,
        }

    result["post_pipeline"] = {
        "transformed_feature_count": transformed_feature_count,
        "splits": splits,
    }
    result["outcome"] = "audit_supported_for_bounded_m1"
    return result


def validate_audit_directory(path: Path) -> dict[str, Any]:
    reports = []
    for file_path in sorted(path.glob("*.json")):
        report = _read_json(file_path, "matrix audit evidence")
        if report.get("outcome") == "audit_supported_for_bounded_m1":
            reports.append(report)
    if len(reports) != len(EXPECTED_PAIRS):
        raise ResidualPyTorchBoundedM1Error(
            f"Expected {len(EXPECTED_PAIRS)} pair audits, found {len(reports)}"
        )
    by_pair = {report.get("pair"): report for report in reports}
    if set(by_pair) != set(EXPECTED_PAIRS):
        raise ResidualPyTorchBoundedM1Error("Audit pair set drifted")

    feature_counts = {report["expanded_feature_count"] for report in reports}
    feature_hashes = {report["expanded_feature_names_sha256"] for report in reports}
    transformed_counts = {
        report["post_pipeline"]["transformed_feature_count"] for report in reports
    }
    if len(feature_counts) != 1 or len(feature_hashes) != 1 or len(transformed_counts) != 1:
        raise ResidualPyTorchBoundedM1Error("Cross-pair feature identity drifted")
    if any(report["target"]["trailing_null_rows"] != EXPECTED_HORIZON for report in reports):
        raise ResidualPyTorchBoundedM1Error("Cross-pair target edge geometry drifted")
    if any(report["liquidation_features_used"] for report in reports):
        raise ResidualPyTorchBoundedM1Error("Liquidation feature entered audit evidence")

    return {
        "schema_version": 1,
        "audit_id": "residual-pytorch-bounded-m1-cross-pair-audit-v1",
        "outcome": "audit_supported_for_bounded_m1",
        "pairs": EXPECTED_PAIRS,
        "expanded_feature_count": next(iter(feature_counts)),
        "expanded_feature_names_sha256": next(iter(feature_hashes)),
        "transformed_feature_count": next(iter(transformed_counts)),
        "pair_reports": {pair: by_pair[pair] for pair in EXPECTED_PAIRS},
        "historical_development_only": True,
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
    }


def verify_downloaded_data(datadir: Path, *, pairs: list[str] | None = None) -> dict[str, Any]:
    """Verify the exact pre-May Kraken history used by the one-shot execution."""
    from freqtrade.configuration import TimeRange
    from freqtrade.data.history.history_utils import load_pair_history

    selected_pairs = pairs or EXPECTED_PAIRS
    if not selected_pairs or any(pair not in EXPECTED_PAIRS for pair in selected_pairs):
        raise ResidualPyTorchBoundedM1Error("Data verification requested an unknown pair")
    timerange = TimeRange.parse_timerange(DOWNLOAD_TIMERANGE)
    if timerange.startdt is None or timerange.stopdt is None:
        raise ResidualPyTorchBoundedM1Error("Expected a bounded download timerange")
    expected_stop = datetime(2026, 5, 1, tzinfo=UTC)
    if timerange.stopdt != expected_stop:
        raise ResidualPyTorchBoundedM1Error("Exclusive pre-May data boundary drifted")

    coverage: dict[str, dict[str, str | int]] = {}
    for pair in selected_pairs:
        for timeframe in EXPECTED_TIMEFRAMES:
            frame = load_pair_history(
                pair=pair,
                timeframe=timeframe,
                datadir=datadir,
                timerange=timerange,
                fill_up_missing=False,
                drop_incomplete=False,
            )
            if frame.empty:
                raise ResidualPyTorchBoundedM1Error(f"No data for {pair} {timeframe}")
            first_date = frame["date"].min().to_pydatetime()
            last_date = frame["date"].max().to_pydatetime()
            if first_date > timerange.startdt:
                raise ResidualPyTorchBoundedM1Error(
                    f"Data starts too late for {pair} {timeframe}: {first_date.isoformat()}"
                )
            minimum_last = timerange.stopts - TIMEFRAME_SECONDS[timeframe]
            if int(last_date.timestamp()) < minimum_last:
                raise ResidualPyTorchBoundedM1Error(
                    f"Data ends too early for {pair} {timeframe}: {last_date.isoformat()}"
                )
            if last_date >= expected_stop:
                raise ResidualPyTorchBoundedM1Error(
                    f"Post-development candle was loaded for {pair} {timeframe}"
                )
            coverage[f"{pair}:{timeframe}"] = {
                "rows": int(len(frame)),
                "first": first_date.isoformat(),
                "last": last_date.isoformat(),
            }

    return {
        "schema_version": 1,
        "verification_id": "residual-pytorch-m1-pre-may-data-v1",
        "status": "ready",
        "datadir": str(datadir),
        "download_timerange": DOWNLOAD_TIMERANGE,
        "exclusive_stop": DEVELOPMENT_STOP_EXCLUSIVE,
        "verified_pairs": selected_pairs,
        "timeframes": EXPECTED_TIMEFRAMES,
        "coverage": coverage,
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
    }


def _rank_correlation(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    if actual.size < 2 or np.all(actual == actual[0]) or np.all(predicted == predicted[0]):
        return None
    actual_rank = pd.Series(actual).rank(method="average").to_numpy(dtype=float)
    predicted_rank = pd.Series(predicted).rank(method="average").to_numpy(dtype=float)
    value = float(np.corrcoef(actual_rank, predicted_rank)[0, 1])
    return value if math.isfinite(value) else None


def _prediction_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    actual = frame["actual_target"].to_numpy(dtype=float)
    predicted = frame["prediction"].to_numpy(dtype=float)
    error = predicted - actual
    absolute_error = np.abs(error)
    beta = 0.01
    smooth_l1 = np.where(
        absolute_error < beta,
        0.5 * np.square(absolute_error) / beta,
        absolute_error - 0.5 * beta,
    )
    directional = np.sign(actual) == np.sign(predicted)
    return {
        "rows": int(len(frame)),
        "mae": float(np.mean(absolute_error)),
        "smooth_l1_beta": beta,
        "smooth_l1": float(np.mean(smooth_l1)),
        "directional_accuracy": float(np.mean(directional)),
        "spearman_rank_ic": _rank_correlation(actual, predicted),
        "prediction_distribution": _series_stats(pd.Series(predicted)),
        "target_distribution": _series_stats(pd.Series(actual)),
        "prediction_sign_counts": {
            "negative": int((predicted < 0).sum()),
            "zero": int((predicted == 0).sum()),
            "positive": int((predicted > 0).sum()),
        },
        "prediction_threshold_counts": {
            "entry_or_higher": int((predicted >= 0.006).sum()),
            "exit_or_lower": int((predicted <= -0.009).sum()),
        },
    }


def build_prediction_diagnostics(path: Path, *, track_id: str) -> dict[str, Any]:  # noqa: C901
    if track_id not in EXPECTED_TRACKS:
        raise ResidualPyTorchBoundedM1Error(f"Unknown model track: {track_id}")
    files = sorted(path.glob("*.csv"))
    if len(files) != len(EXPECTED_PAIRS):
        raise ResidualPyTorchBoundedM1Error(
            f"Expected {len(EXPECTED_PAIRS)} prediction files, found {len(files)}"
        )
    frames: list[pd.DataFrame] = []
    for file_path in files:
        frame = pd.read_csv(file_path)
        expected_columns = {"date", "pair", "actual_target", "prediction", "do_predict"}
        if not expected_columns.issubset(frame.columns):
            raise ResidualPyTorchBoundedM1Error(
                f"Prediction evidence columns are incomplete in {file_path}"
            )
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], utc=True, errors="raise")
    pair_set = set(combined["pair"].unique())
    if pair_set != set(EXPECTED_PAIRS):
        raise ResidualPyTorchBoundedM1Error("Prediction pair set drifted")
    start = pd.Timestamp(DEVELOPMENT_START)
    stop = pd.Timestamp(DEVELOPMENT_STOP_EXCLUSIVE)
    if (combined["date"] < start).any() or (combined["date"] >= stop).any():
        raise ResidualPyTorchBoundedM1Error("Prediction evidence crossed development boundaries")

    for column in ("actual_target", "prediction", "do_predict"):
        combined[column] = pd.to_numeric(combined[column], errors="coerce")
    valid = combined[
        np.isfinite(combined["actual_target"])
        & np.isfinite(combined["prediction"])
        & (combined["do_predict"] == 1)
    ].copy()
    if valid.empty:
        raise ResidualPyTorchBoundedM1Error("No valid predictions remain for diagnostics")

    per_pair = {
        pair: _prediction_metrics(valid.loc[valid["pair"] == pair]) for pair in EXPECTED_PAIRS
    }
    if any(metrics["rows"] == 0 for metrics in per_pair.values()):
        raise ResidualPyTorchBoundedM1Error("A pair has zero valid diagnostic predictions")

    return {
        "schema_version": 1,
        "diagnostics_id": "residual-pytorch-bounded-m1-prediction-diagnostics-v1",
        "track_id": track_id,
        "development_start": DEVELOPMENT_START,
        "development_stop_exclusive": DEVELOPMENT_STOP_EXCLUSIVE,
        "raw_prediction_rows": int(len(combined)),
        "valid_prediction_rows": int(len(valid)),
        "invalid_or_rejected_rows": int(len(combined) - len(valid)),
        "combined": _prediction_metrics(valid),
        "per_pair": per_pair,
        "historical_development_only": True,
        "winner_selection_allowed": False,
        "profitability_claim_allowed": False,
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
    }


def validate_training_directory(path: Path, *, track_id: str) -> dict[str, Any]:
    if track_id not in EXPECTED_TRACKS:
        raise ResidualPyTorchBoundedM1Error(f"Unknown training-evidence track: {track_id}")
    files = sorted(path.glob("*.json"))
    if len(files) != len(EXPECTED_PAIRS):
        raise ResidualPyTorchBoundedM1Error(
            f"Expected {len(EXPECTED_PAIRS)} training evidence files, found {len(files)}"
        )
    reports = [_read_json(file_path, "training evidence") for file_path in files]
    by_pair = {report.get("pair"): report for report in reports}
    if set(by_pair) != set(EXPECTED_PAIRS):
        raise ResidualPyTorchBoundedM1Error("Training-evidence pair set drifted")
    expected_wrapper = EXPECTED_TRACKS[track_id]["freqai_model"]
    for pair, report in by_pair.items():
        if report.get("wrapper_model") != expected_wrapper:
            raise ResidualPyTorchBoundedM1Error(f"{pair} wrapper model identity drifted")
        if report.get("identifier") != EXPECTED_TRACKS[track_id]["identifier"]:
            raise ResidualPyTorchBoundedM1Error(f"{pair} FreqAI identifier drifted")
        if report.get("train_rows", 0) < 1 or report.get("test_rows", 0) < 1:
            raise ResidualPyTorchBoundedM1Error(f"{pair} training split is empty")
        if report.get("feature_count", 0) < 1:
            raise ResidualPyTorchBoundedM1Error(f"{pair} training feature count is empty")
        if report.get("training_start") != TRAINING_START.replace("Z", "+00:00"):
            raise ResidualPyTorchBoundedM1Error(f"{pair} training start drifted")
        if report.get("training_stop_exclusive") != TRAINING_STOP_EXCLUSIVE.replace(
            "Z", "+00:00"
        ):
            raise ResidualPyTorchBoundedM1Error(f"{pair} training stop drifted")
        scalar_events = report.get("recorded_scalar_events", {})
        if track_id == "residual-pytorch-m1-lightgbm-v1":
            if not report.get("lightgbm_evals_result"):
                raise ResidualPyTorchBoundedM1Error(
                    f"{pair} LightGBM evaluation history is absent"
                )
        else:
            if not scalar_events.get("train_loss") or not scalar_events.get("test_loss"):
                raise ResidualPyTorchBoundedM1Error(
                    f"{pair} PyTorch train/test loss history is absent"
                )
    feature_counts = {report["feature_count"] for report in reports}
    if len(feature_counts) != 1:
        raise ResidualPyTorchBoundedM1Error("Cross-pair training feature counts differ")
    return {
        "schema_version": 1,
        "evidence_id": "residual-pytorch-bounded-m1-training-evidence-index-v1",
        "track_id": track_id,
        "pairs": EXPECTED_PAIRS,
        "feature_count": next(iter(feature_counts)),
        "pair_evidence": {pair: by_pair[pair] for pair in EXPECTED_PAIRS},
        "historical_development_only": True,
        "winner_selection_allowed": False,
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
    }


def validate_run_summary(path: Path, *, track_id: str, expected_head: str) -> dict[str, Any]:
    summary = _read_json(path, "run summary")
    if track_id not in EXPECTED_TRACKS and track_id != EXPECTED_AUDIT_TRACK["track_id"]:
        raise ResidualPyTorchBoundedM1Error(f"Unknown run-summary track: {track_id}")
    expected = {
        "status": "success",
        "experiment_id": track_id,
        "git_commit": expected_head,
        "timerange": EXECUTION_TIMERANGE,
        "download_timerange": DOWNLOAD_TIMERANGE,
    }
    for field, expected_value in expected.items():
        if summary.get(field) != expected_value:
            raise ResidualPyTorchBoundedM1Error(f"Run summary field {field} drifted")
    commands = summary.get("commands")
    if not isinstance(commands, list) or len(commands) != 1:
        raise ResidualPyTorchBoundedM1Error("Expected exactly one Freqtrade command")
    if len(commands[0]) < 2 or commands[0][1] != "backtesting":
        raise ResidualPyTorchBoundedM1Error("Execution command was not backtesting")
    serialized = json.dumps(summary, sort_keys=True)
    if "20260701" in serialized or PROTECTED_HOLDOUT in serialized:
        raise ResidualPyTorchBoundedM1Error("Forbidden temporal boundary entered run summary")
    return summary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode")

    contract_parser = subparsers.add_parser("contract")
    contract_parser.add_argument("--output", type=Path)

    data_parser = subparsers.add_parser("verify-data")
    data_parser.add_argument("--datadir", type=Path, required=True)
    data_parser.add_argument("--pair", action="append", choices=EXPECTED_PAIRS, dest="pairs")
    data_parser.add_argument("--output", type=Path)

    audit_parser = subparsers.add_parser("validate-audit")
    audit_parser.add_argument("--audit-dir", type=Path, required=True)
    audit_parser.add_argument("--output", type=Path)

    diagnostics_parser = subparsers.add_parser("diagnostics")
    diagnostics_parser.add_argument("--prediction-dir", type=Path, required=True)
    diagnostics_parser.add_argument("--track-id", choices=sorted(EXPECTED_TRACKS), required=True)
    diagnostics_parser.add_argument("--output", type=Path, required=True)

    training_parser = subparsers.add_parser("validate-training")
    training_parser.add_argument("--training-dir", type=Path, required=True)
    training_parser.add_argument("--track-id", choices=sorted(EXPECTED_TRACKS), required=True)
    training_parser.add_argument("--output", type=Path, required=True)

    summary_parser = subparsers.add_parser("validate-summary")
    summary_parser.add_argument("summary", type=Path)
    summary_parser.add_argument(
        "--track-id",
        choices=sorted([*EXPECTED_TRACKS, EXPECTED_AUDIT_TRACK["track_id"]]),
        required=True,
    )
    summary_parser.add_argument("--expected-head", required=True)

    return parser.parse_args(argv)


def _emit(payload: dict[str, Any], output: Path | None) -> None:
    if output is None:
        print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    else:
        write_json(output, payload)
        print(output)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    mode = args.mode or "contract"
    try:
        if mode == "contract":
            payload = build_contract_report()
            _emit(payload, getattr(args, "output", None))
        elif mode == "verify-data":
            payload = verify_downloaded_data(args.datadir, pairs=args.pairs)
            _emit(payload, args.output)
        elif mode == "validate-audit":
            payload = validate_audit_directory(args.audit_dir)
            _emit(payload, args.output)
        elif mode == "diagnostics":
            payload = build_prediction_diagnostics(args.prediction_dir, track_id=args.track_id)
            _emit(payload, args.output)
        elif mode == "validate-training":
            payload = validate_training_directory(args.training_dir, track_id=args.track_id)
            _emit(payload, args.output)
        elif mode == "validate-summary":
            payload = validate_run_summary(
                args.summary,
                track_id=args.track_id,
                expected_head=args.expected_head,
            )
            print(payload["experiment_id"])
        else:
            raise ResidualPyTorchBoundedM1Error(f"Unsupported mode: {mode}")
    except ResidualPyTorchBoundedM1Error as exc:
        print(f"Bounded M1 validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
