#!/usr/bin/env python3
"""Validate the versioned finite-volume residual PyTorch M1 remediation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from ai_platform.scripts import residual_pytorch_bounded_m1_execution as base

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REPO_PATH = (
    "ai_platform/experimental_model_research/"
    "residual-pytorch-bounded-m1-execution-contract-v2.json"
)
CONTRACT_PATH = REPO_ROOT / CONTRACT_REPO_PATH
REQUEST_REPO_PATH = (
    "ai_platform/experimental_model_research/run-requests/"
    "residual-pytorch-bounded-m1-execution-v2.json"
)
TASK_REPO_PATH = "docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md"
STRATEGY_NAME = "AiFrozenCandidateStrategyV2"
STRATEGY_REPO_PATH = "ai_platform/strategies/AiFrozenCandidateStrategyV2.py"
EXPECTED_TRACKS = {
    track_id: dict(values, manifest=values["manifest"].replace("-v1.json", "-v2.json"))
    for track_id, values in base.EXPECTED_TRACKS.items()
}
EXPECTED_AUDIT_TRACK = dict(
    base.EXPECTED_AUDIT_TRACK,
    manifest=base.EXPECTED_AUDIT_TRACK["manifest"].replace("-v1.json", "-v2.json"),
)
ResidualPyTorchBoundedM1Error = base.ResidualPyTorchBoundedM1Error

EXPECTED_PAIRS = base.EXPECTED_PAIRS
EXPECTED_TIMEFRAMES = base.EXPECTED_TIMEFRAMES
EXECUTION_TIMERANGE = base.EXECUTION_TIMERANGE
DOWNLOAD_TIMERANGE = base.DOWNLOAD_TIMERANGE
TARGET = base.TARGET
write_json = base.write_json
build_raw_matrix_audit = base.build_raw_matrix_audit
finalize_matrix_audit = base.finalize_matrix_audit
validate_audit_directory = base.validate_audit_directory
verify_downloaded_data = base.verify_downloaded_data
build_prediction_diagnostics = base.build_prediction_diagnostics
validate_training_directory = base.validate_training_directory
validate_run_summary = base.validate_run_summary


def _read_json(path: Path, label: str) -> dict[str, Any]:
    return base._read_json(path, label)


def _repo_path(value: str) -> Path:
    return base._repo_path(value)


def validate_contract(contract: dict[str, Any]) -> None:  # noqa: C901
    if contract.get("schema_version") != 1:
        raise ResidualPyTorchBoundedM1Error("Contract schema_version must be 1")
    if contract.get("contract_id") != "residual-pytorch-bounded-m1-execution-v2":
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
        REPO_ROOT
        / "ai_platform/experimental_model_research/"
        "residual-pytorch-bounded-m1-execution-contract-v1.json"
    )
    source = json.loads(source_path.read_text(encoding="utf-8"))
    for field in (
        "geometry",
        "market_data",
        "data_audit",
        "consumed_historical_oos",
        "protected_final_holdout",
        "phase6_isolation",
    ):
        if contract.get(field) != source.get(field):
            raise ResidualPyTorchBoundedM1Error(f"{field} drifted from v1")

    feature_target = dict(source["feature_target_contract"])
    feature_target["strategy"] = STRATEGY_NAME
    feature_target["strategy_file"] = STRATEGY_REPO_PATH
    feature_target["volume_change_semantics"] = {
        "feature": "%-volume-change",
        "formula": "2*(current-previous)/(abs(current)+abs(previous))",
        "zero_denominator_value": 0.0,
        "nonfinite_fallback_value": 0.0,
        "bounds": [-2.0, 2.0],
    }
    if contract.get("feature_target_contract") != feature_target:
        raise ResidualPyTorchBoundedM1Error("Feature/target remediation drifted")

    expected_audit = dict(source["audit_track"])
    expected_audit["manifest"] = EXPECTED_AUDIT_TRACK["manifest"]
    if contract.get("audit_track") != expected_audit:
        raise ResidualPyTorchBoundedM1Error("Audit track drifted")
    expected_tracks = []
    for source_track in source["tracks"]:
        changed = dict(source_track)
        changed["manifest"] = EXPECTED_TRACKS[source_track["track_id"]]["manifest"]
        expected_tracks.append(changed)
    if contract.get("tracks") != expected_tracks:
        raise ResidualPyTorchBoundedM1Error("Model tracks drifted")

    authorization = dict(source["authorization"])
    authorization["feature_changes_allowed"] = True
    if contract.get("authorization") != authorization:
        raise ResidualPyTorchBoundedM1Error("Authorization contract drifted")
    if contract.get("remediation") != {
        "source_contract": "residual-pytorch-bounded-m1-execution-v1",
        "source_run": 30299203871,
        "source_failure": "EXPANDED_VOLUME_CHANGE_INFINITY",
        "authorized_feature_changes": ["%-volume-change"],
        "all_other_features_unchanged": True,
        "targets_thresholds_models_and_geometry_unchanged": True,
    }:
        raise ResidualPyTorchBoundedM1Error("Remediation scope drifted")
    if "20260701" in json.dumps(contract, sort_keys=True):
        raise ResidualPyTorchBoundedM1Error("Forbidden post-development boundary leaked")


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = _read_json(path, "bounded M1 v2 execution contract")
    validate_contract(contract)
    return contract


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
        "fee": base.EXPECTED_FEE,
    }
    for field, expected_value in expected.items():
        if manifest.get(field) != expected_value:
            raise ResidualPyTorchBoundedM1Error(
                f"{track['track_id']} manifest field {field} drifted"
            )
    output_root = manifest.get("output_root")
    if not isinstance(output_root, str) or not output_root.startswith(
        "ai_platform/artifacts/experimental-model-research/residual-pytorch-m1-v2/"
    ):
        raise ResidualPyTorchBoundedM1Error(f"{track['track_id']} output root drifted")
    return manifest


def canonical_inputs() -> dict[str, Any]:
    contract = load_contract()
    tracks = [contract["audit_track"], *contract["tracks"]]
    resolved = []
    for track in tracks:
        config = base._load_and_validate_config(track)
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
        "consumed_historical_oos_used": False,
        "protected_final_holdout_used": False,
        "phase6_member": False,
        "tracks": [item["track"]["track_id"] for item in inputs["tracks"]],
        "run_request_present": _repo_path(REQUEST_REPO_PATH).exists(),
        "remediation": "finite_bounded_symmetric_volume_change",
    }


def main(argv: list[str] | None = None) -> int:
    args = base.parse_args(sys.argv[1:] if argv is None else argv)
    mode = args.mode or "contract"
    try:
        if mode == "contract":
            payload = build_contract_report()
            base._emit(payload, getattr(args, "output", None))
        elif mode == "verify-data":
            base._emit(verify_downloaded_data(args.datadir, pairs=args.pairs), args.output)
        elif mode == "validate-audit":
            base._emit(validate_audit_directory(args.audit_dir), args.output)
        elif mode == "diagnostics":
            payload = build_prediction_diagnostics(
                args.prediction_dir, track_id=args.track_id
            )
            base._emit(payload, args.output)
        elif mode == "validate-training":
            payload = validate_training_directory(
                args.training_dir, track_id=args.track_id
            )
            base._emit(payload, args.output)
        elif mode == "validate-summary":
            payload = validate_run_summary(
                args.summary, track_id=args.track_id, expected_head=args.expected_head
            )
            print(payload["experiment_id"])
        else:
            raise ResidualPyTorchBoundedM1Error(f"Unsupported mode: {mode}")
    except ResidualPyTorchBoundedM1Error as exc:
        print(f"Bounded M1 v2 validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
