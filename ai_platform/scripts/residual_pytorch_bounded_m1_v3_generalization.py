#!/usr/bin/env python3
"""Validate and summarize the bounded residual PyTorch M1 v3 pair generalization."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ai_platform.scripts import residual_pytorch_bounded_m1_execution as base


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REPO_PATH = (
    "ai_platform/experimental_model_research/"
    "residual-pytorch-bounded-m1-generalization-contract-v3.json"
)
CONTRACT_PATH = REPO_ROOT / CONTRACT_REPO_PATH
REQUEST_REPO_PATH = (
    "ai_platform/experimental_model_research/run-requests/"
    "residual-pytorch-bounded-m1-generalization-v3.json"
)
TASK_REPO_PATH = "docs/agents/tasks/FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization.md"
STRATEGY_NAME = "AiFrozenCandidateStrategyV2"
STRATEGY_REPO_PATH = "ai_platform/strategies/AiFrozenCandidateStrategyV2.py"
EXPECTED_PAIRS = ["SOL/USDT", "XRP/USDT"]
SOURCE_PAIRS = ["BTC/USDT", "ETH/USDT"]
EXPECTED_TIMEFRAMES = ["15m", "1h", "4h"]
EXPECTED_FEE = 0.002
EXPECTED_HORIZON = 12
EXPECTED_EXPANDED_FEATURE_COUNT = 272
SOURCE_ROLE_NORMALIZED_FEATURE_HASH = (
    "c65ec5f29963f1bb541f1c5416b52a4be8bfe2a1328a04577c17eea197d2945c"
)
EXECUTION_TIMERANGE = "1772323200-1777593599"
DOWNLOAD_TIMERANGE = "1754006400-1777593599"
TARGET = "&-future_return"
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
    "residual-pytorch-m1-lightgbm-generalization-v3": {
        "config": (
            "ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-lightgbm.example.json"
        ),
        "manifest": ("ai_platform/experiments/residual-pytorch-m1-generalization-v3-lightgbm.json"),
        "freqai_model": "M1LightGBMRegressor",
        "model_file": "ai_platform/freqaimodels/M1LightGBMRegressor.py",
        "underlying_model_file": "freqtrade/freqai/prediction_models/LightGBMRegressor.py",
        "identifier": "ai-platform-residual-pytorch-m1-lightgbm-generalization-v3",
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
    "residual-pytorch-m1-seeded-mlp-generalization-v3": {
        "config": (
            "ai_platform/configs/"
            "freqai-residual-pytorch-m1-generalization-v3-seeded-mlp.example.json"
        ),
        "manifest": (
            "ai_platform/experiments/residual-pytorch-m1-generalization-v3-seeded-mlp.json"
        ),
        "freqai_model": "M1SeededPyTorchMLPRegressor",
        "model_file": "ai_platform/freqaimodels/M1SeededPyTorchMLPRegressor.py",
        "underlying_model_file": "ai_platform/freqaimodels/SeededPyTorchMLPRegressor.py",
        "identifier": "ai-platform-residual-pytorch-m1-seeded-mlp-generalization-v3",
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
    "residual-pytorch-m1-residual-mlp-generalization-v3": {
        "config": (
            "ai_platform/configs/"
            "freqai-residual-pytorch-m1-generalization-v3-residual-mlp.example.json"
        ),
        "manifest": (
            "ai_platform/experiments/residual-pytorch-m1-generalization-v3-residual-mlp.json"
        ),
        "freqai_model": "M1ResidualPyTorchRegressor",
        "model_file": "ai_platform/freqaimodels/M1ResidualPyTorchRegressor.py",
        "underlying_model_file": "ai_platform/freqaimodels/ResidualPyTorchRegressor.py",
        "identifier": "ai-platform-residual-pytorch-m1-residual-mlp-generalization-v3",
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
    "track_id": "residual-pytorch-m1-data-audit-generalization-v3",
    "config": (
        "ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-data-audit.example.json"
    ),
    "manifest": ("ai_platform/experiments/residual-pytorch-m1-generalization-v3-data-audit.json"),
    "freqai_model": "ResidualPyTorchM1V3DataAuditRegressor",
    "model_file": "ai_platform/freqaimodels/ResidualPyTorchM1V3DataAuditRegressor.py",
    "identifier": "ai-platform-residual-pytorch-m1-data-audit-generalization-v3",
}
ResidualPyTorchBoundedM1Error = base.ResidualPyTorchBoundedM1Error
write_json = base.write_json


def _read_json(path: Path, label: str) -> dict[str, Any]:
    return base._read_json(path, label)


def _repo_path(value: str) -> Path:
    return base._repo_path(value)


@contextmanager
def _patched_base_contract() -> Iterator[None]:
    names = (
        "EXPECTED_PAIRS",
        "EXPECTED_FEATURE_PARAMETERS",
        "EXPECTED_TRACKS",
        "EXPECTED_AUDIT_TRACK",
    )
    previous = {name: getattr(base, name) for name in names}
    base.EXPECTED_PAIRS = EXPECTED_PAIRS
    base.EXPECTED_FEATURE_PARAMETERS = EXPECTED_FEATURE_PARAMETERS
    base.EXPECTED_TRACKS = EXPECTED_TRACKS
    base.EXPECTED_AUDIT_TRACK = EXPECTED_AUDIT_TRACK
    try:
        yield
    finally:
        for name, value in previous.items():
            setattr(base, name, value)


def validate_contract(contract: dict[str, Any]) -> None:  # noqa: C901
    if contract.get("schema_version") != 1:
        raise ResidualPyTorchBoundedM1Error("Contract schema_version must be 1")
    if contract.get("contract_id") != "residual-pytorch-bounded-m1-generalization-v3":
        raise ResidualPyTorchBoundedM1Error("Contract identity drifted")
    if contract.get("task") != TASK_REPO_PATH or contract.get("request_path") != REQUEST_REPO_PATH:
        raise ResidualPyTorchBoundedM1Error("Task or request path drifted")
    if contract.get("trigger") != {
        "event": "pull_request_opened",
        "base_branch": "develop",
        "exact_one_file": True,
    }:
        raise ResidualPyTorchBoundedM1Error("One-shot trigger contract drifted")

    source_path = (
        REPO_ROOT / "ai_platform/experimental_model_research/"
        "residual-pytorch-bounded-m1-execution-contract-v2.json"
    )
    source = _read_json(source_path, "bounded M1 v2 source contract")
    for field in (
        "geometry",
        "consumed_historical_oos",
        "protected_final_holdout",
        "phase6_isolation",
        "remediation",
    ):
        if contract.get(field) != source.get(field):
            raise ResidualPyTorchBoundedM1Error(f"{field} drifted from v2")

    expected_market = dict(source["market_data"])
    expected_market["pairs"] = EXPECTED_PAIRS
    expected_market["cache_namespace"] = "residual-pytorch-m1-generalization-pre-may-v3"
    if contract.get("market_data") != expected_market:
        raise ResidualPyTorchBoundedM1Error("Only the bounded pair cohort may change")

    expected_feature_target = dict(source["feature_target_contract"])
    expected_feature_parameters = dict(expected_feature_target["feature_parameters"])
    expected_feature_parameters["include_corr_pairlist"] = EXPECTED_PAIRS
    expected_feature_target["feature_parameters"] = expected_feature_parameters
    if contract.get("feature_target_contract") != expected_feature_target:
        raise ResidualPyTorchBoundedM1Error("Feature/target geometry drifted")

    expected_authorization = dict(source["authorization"])
    expected_authorization["feature_changes_allowed"] = False
    if contract.get("authorization") != expected_authorization:
        raise ResidualPyTorchBoundedM1Error("Authorization contract drifted")

    expected_audit_track = dict(EXPECTED_AUDIT_TRACK)
    if contract.get("audit_track") != expected_audit_track:
        raise ResidualPyTorchBoundedM1Error("Audit track drifted")

    expected_tracks = [
        {"track_id": track_id, **values} for track_id, values in EXPECTED_TRACKS.items()
    ]
    if contract.get("tracks") != expected_tracks:
        raise ResidualPyTorchBoundedM1Error("Frozen model tracks or parameters drifted")

    expected_audit = dict(source["data_audit"])
    expected_audit["expected_expanded_feature_count"] = EXPECTED_EXPANDED_FEATURE_COUNT
    expected_audit["source_role_normalized_feature_hash_required"] = True
    if contract.get("data_audit") != expected_audit:
        raise ResidualPyTorchBoundedM1Error("Data-audit contract drifted")

    if contract.get("generalization") != {
        "source_contract": "residual-pytorch-bounded-m1-execution-v2",
        "source_run": 30340242201,
        "source_pairs": SOURCE_PAIRS,
        "target_pairs": EXPECTED_PAIRS,
        "pair_cohort_only_change": True,
        "expected_expanded_feature_count": EXPECTED_EXPANDED_FEATURE_COUNT,
        "source_role_normalized_feature_names_sha256": SOURCE_ROLE_NORMALIZED_FEATURE_HASH,
        "features_targets_thresholds_models_and_temporal_geometry_unchanged": True,
        "comparison_to_source_is_descriptive_only": True,
    }:
        raise ResidualPyTorchBoundedM1Error("Generalization scope drifted")

    serialized = json.dumps(contract, sort_keys=True)
    if "20260701" in serialized:
        raise ResidualPyTorchBoundedM1Error("Forbidden post-development boundary leaked")


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = _read_json(path, "bounded M1 v3 generalization contract")
    validate_contract(contract)
    return contract


def _load_and_validate_config(track: dict[str, Any]) -> dict[str, Any]:
    config = _read_json(_repo_path(track["config"]), f"{track['track_id']} config")
    if config.get("dry_run") is not True or config.get("initial_state") != "stopped":
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} safety defaults drifted")
    exchange = config.get("exchange", {})
    if exchange.get("name") != "kraken" or exchange.get("key") or exchange.get("secret"):
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} exchange safety drifted")
    if exchange.get("pair_whitelist") != EXPECTED_PAIRS:
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} pair cohort drifted")

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
            raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} config field {field} drifted")
    return config


def _load_and_validate_manifest(track: dict[str, Any]) -> dict[str, Any]:
    manifest = _read_json(_repo_path(track["manifest"]), f"{track['track_id']} manifest")
    expected = {
        "schema_version": 1,
        "experiment_id": track["track_id"],
        "config": track["config"],
        "strategy": STRATEGY_NAME,
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
        "ai_platform/artifacts/experimental-model-research/residual-pytorch-m1-generalization-v3/"
    ):
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} output root drifted")
    return manifest


def canonical_inputs() -> dict[str, Any]:
    contract = load_contract()
    resolved = []
    for track in [contract["audit_track"], *contract["tracks"]]:
        config = _load_and_validate_config(track)
        manifest = _load_and_validate_manifest(track)
        model_path = _repo_path(track["model_file"])
        if not model_path.is_file():
            raise ResidualPyTorchBoundedM1Error(f"Missing model file: {model_path}")
        resolved.append({"track": track, "config": config, "manifest": manifest})
    strategy_path = _repo_path(STRATEGY_REPO_PATH)
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
        "source_pairs": SOURCE_PAIRS,
        "generalization_pairs": EXPECTED_PAIRS,
        "expected_expanded_feature_count": EXPECTED_EXPANDED_FEATURE_COUNT,
        "source_role_normalized_feature_names_sha256": SOURCE_ROLE_NORMALIZED_FEATURE_HASH,
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
        "phase6_member": False,
        "tracks": [item["track"]["track_id"] for item in inputs["tracks"]],
        "run_request_present": _repo_path(REQUEST_REPO_PATH).exists(),
    }


def build_raw_matrix_audit(
    dataframe: Any,
    feature_names: list[str],
    label_names: list[str],
    *,
    pair: str,
) -> dict[str, Any]:
    with _patched_base_contract():
        report = base.build_raw_matrix_audit(dataframe, feature_names, label_names, pair=pair)
    report["generalization_cohort"] = "sol_xrp_v3"
    return report


def finalize_matrix_audit(
    raw_audit: dict[str, Any], data_dictionary: dict[str, Any]
) -> dict[str, Any]:
    return base.finalize_matrix_audit(raw_audit, data_dictionary)


def verify_downloaded_data(datadir: Path, *, pairs: list[str] | None = None) -> dict[str, Any]:
    with _patched_base_contract():
        payload = base.verify_downloaded_data(datadir, pairs=pairs)
    payload["verification_id"] = "residual-pytorch-m1-generalization-pre-may-data-v3"
    return payload


def build_prediction_diagnostics(path: Path, *, track_id: str) -> dict[str, Any]:
    with _patched_base_contract():
        payload = base.build_prediction_diagnostics(path, track_id=track_id)
    payload["diagnostics_id"] = (
        "residual-pytorch-bounded-m1-generalization-prediction-diagnostics-v3"
    )
    return payload


def validate_training_directory(  # noqa: C901
    path: Path, *, track_id: str
) -> dict[str, Any]:
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

    expected_track = EXPECTED_TRACKS[track_id]
    expected_wrapper = expected_track["freqai_model"]
    expected_training_start = base.TRAINING_START.replace("Z", "+00:00")
    expected_training_stop = base.TRAINING_STOP_EXCLUSIVE.replace("Z", "+00:00")
    for pair, report in by_pair.items():
        if report.get("wrapper_model") != expected_wrapper:
            raise ResidualPyTorchBoundedM1Error(f"{pair} wrapper model identity drifted")
        if report.get("identifier") != expected_track["identifier"]:
            raise ResidualPyTorchBoundedM1Error(f"{pair} FreqAI identifier drifted")
        if report.get("train_rows", 0) < 1 or report.get("test_rows", 0) < 1:
            raise ResidualPyTorchBoundedM1Error(f"{pair} training split is empty")
        if report.get("feature_count", 0) < 1:
            raise ResidualPyTorchBoundedM1Error(f"{pair} training feature count is empty")
        if report.get("training_start") != expected_training_start:
            raise ResidualPyTorchBoundedM1Error(f"{pair} training start drifted")
        if report.get("training_stop_exclusive") != expected_training_stop:
            raise ResidualPyTorchBoundedM1Error(f"{pair} training stop drifted")

        scalar_events = report.get("recorded_scalar_events", {})
        if expected_wrapper == "M1LightGBMRegressor":
            if not report.get("lightgbm_evals_result"):
                raise ResidualPyTorchBoundedM1Error(
                    f"{pair} LightGBM evaluation history is absent"
                )
        elif not scalar_events.get("train_loss") or not scalar_events.get("test_loss"):
            raise ResidualPyTorchBoundedM1Error(
                f"{pair} PyTorch train/test loss history is absent"
            )

    feature_counts = {report["feature_count"] for report in reports}
    if len(feature_counts) != 1:
        raise ResidualPyTorchBoundedM1Error("Cross-pair training feature counts differ")
    return {
        "schema_version": 1,
        "evidence_id": "residual-pytorch-bounded-m1-generalization-training-evidence-index-v3",
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
    with _patched_base_contract():
        return base.validate_run_summary(path, track_id=track_id, expected_head=expected_head)


def _normalized_feature_identity(report: dict[str, Any]) -> str:
    pair = report.get("pair")
    names = report.get("expanded_feature_names")
    if pair not in EXPECTED_PAIRS:
        raise ResidualPyTorchBoundedM1Error("Audit pair set drifted")
    if not isinstance(names, list) or not names or not all(isinstance(name, str) for name in names):
        raise ResidualPyTorchBoundedM1Error("Audit feature-name evidence is missing")

    normalized = []
    for name in names:
        value = name
        for expected_pair in EXPECTED_PAIRS:
            role = "{PRIMARY_PAIR}" if expected_pair == pair else "{CORRELATED_PAIR}"
            value = value.replace(expected_pair, role)
        normalized.append(value)
    return hashlib.sha256("\n".join(normalized).encode()).hexdigest()


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
    normalized_hashes = {_normalized_feature_identity(report) for report in reports}
    transformed_counts = {
        report["post_pipeline"]["transformed_feature_count"] for report in reports
    }
    if feature_counts != {EXPECTED_EXPANDED_FEATURE_COUNT}:
        raise ResidualPyTorchBoundedM1Error("Expanded feature count drifted from v2")
    if transformed_counts != {EXPECTED_EXPANDED_FEATURE_COUNT}:
        raise ResidualPyTorchBoundedM1Error("Transformed feature count drifted from v2")
    if normalized_hashes != {SOURCE_ROLE_NORMALIZED_FEATURE_HASH}:
        raise ResidualPyTorchBoundedM1Error(
            "Role-normalized feature identity differs from the terminal v2 source audit"
        )
    if any(report["target"]["trailing_null_rows"] != EXPECTED_HORIZON for report in reports):
        raise ResidualPyTorchBoundedM1Error("Cross-pair target edge geometry drifted")
    if any(report["liquidation_features_used"] for report in reports):
        raise ResidualPyTorchBoundedM1Error("Liquidation feature entered audit evidence")

    return {
        "schema_version": 1,
        "audit_id": "residual-pytorch-bounded-m1-generalization-cross-pair-audit-v3",
        "outcome": "audit_supported_for_bounded_m1_generalization",
        "source_run": 30340242201,
        "source_pairs": SOURCE_PAIRS,
        "pairs": EXPECTED_PAIRS,
        "expanded_feature_count": EXPECTED_EXPANDED_FEATURE_COUNT,
        "expanded_feature_names_sha256": SOURCE_ROLE_NORMALIZED_FEATURE_HASH,
        "feature_identity_normalization": "primary_and_correlated_pair_roles",
        "pair_qualified_feature_names_sha256": {
            pair: by_pair[pair]["expanded_feature_names_sha256"] for pair in EXPECTED_PAIRS
        },
        "transformed_feature_count": EXPECTED_EXPANDED_FEATURE_COUNT,
        "pair_reports": {pair: by_pair[pair] for pair in EXPECTED_PAIRS},
        "historical_development_only": True,
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
        "winner_selection_allowed": False,
    }


def parse_args(argv: list[str]) -> Any:
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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    mode = args.mode or "contract"
    try:
        if mode == "contract":
            base._emit(build_contract_report(), getattr(args, "output", None))
        elif mode == "verify-data":
            base._emit(verify_downloaded_data(args.datadir, pairs=args.pairs), args.output)
        elif mode == "validate-audit":
            base._emit(validate_audit_directory(args.audit_dir), args.output)
        elif mode == "diagnostics":
            base._emit(
                build_prediction_diagnostics(args.prediction_dir, track_id=args.track_id),
                args.output,
            )
        elif mode == "validate-training":
            base._emit(
                validate_training_directory(args.training_dir, track_id=args.track_id),
                args.output,
            )
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
        print(f"Bounded M1 v3 generalization validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
