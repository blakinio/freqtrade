#!/usr/bin/env python3
"""Materialize deterministic Phase 6 model-comparison inputs without executing research."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from ai_platform.scripts.model_comparison_contract import load_model_comparison_contract
from ai_platform.scripts.run_experiment import load_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_MANIFEST = REPO_ROOT / "ai_platform/experiments/baseline-v1.json"
DEFAULT_CONTRACT = REPO_ROOT / "ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "ai_platform/artifacts/model-comparison/materialized"
MODEL_SLUGS = {
    "LightGBMRegressor": "lightgbm",
    "XGBoostRegressor": "xgboost",
}


class ModelComparisonHarnessError(RuntimeError):
    """Raised when materialization cannot preserve the Phase 6 comparison contract."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelComparisonHarnessError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ModelComparisonHarnessError(f"{label} must contain a JSON object")
    return payload


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError as exc:
        raise ModelComparisonHarnessError(
            f"Materialized output must remain inside repository root: {path}"
        ) from exc


def _materialized_config(
    baseline_config: dict[str, Any],
    model_type: str,
    experiment_identity: str,
    model_identity: dict[str, Any],
) -> dict[str, Any]:
    config = copy.deepcopy(baseline_config)
    freqai = config.get("freqai")
    if not isinstance(freqai, dict):
        raise ModelComparisonHarnessError("Baseline config is missing freqai settings")
    parameters = model_identity.get("model_training_parameters")
    if not isinstance(parameters, dict):
        raise ModelComparisonHarnessError(
            f"Model identity for {model_type} is missing model_training_parameters"
        )
    freqai["identifier"] = experiment_identity
    freqai["model_training_parameters"] = copy.deepcopy(parameters)
    return config


def _materialized_manifest(
    *,
    comparison_id: str,
    model_type: str,
    experiment_identity: str,
    config_path: str,
    output_root: str,
    shared: dict[str, Any],
    historical_window: dict[str, Any],
    download_timerange: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "experiment_id": experiment_identity,
        "description": (
            f"Materialized historical-only {model_type} input for {comparison_id}; "
            "no execution is performed by the harness."
        ),
        "config": config_path,
        "strategy": shared["strategy"],
        "strategy_path": "ai_platform/strategies",
        "freqai_model": model_type,
        "timerange": historical_window["timerange"],
        "download_timerange": download_timerange,
        "pairs": copy.deepcopy(shared["pairs"]),
        "timeframes": copy.deepcopy(shared["timeframes"]),
        "fee": shared["fee"],
        "output_root": output_root,
    }


def build_materialization(
    contract_path: Path = DEFAULT_CONTRACT,
    *,
    output_root: str,
) -> dict[str, Any]:
    """Build deterministic configs/manifests in memory without writing or executing anything."""
    contract_path = contract_path.resolve()
    contract = load_model_comparison_contract(contract_path)
    baseline_manifest = _read_json(BASELINE_MANIFEST, "baseline experiment manifest")

    config_path_value = contract["shared_experiment"]["config"]
    baseline_config_path = (REPO_ROOT / config_path_value).resolve()
    baseline_config = _read_json(baseline_config_path, "baseline research config")

    historical_windows = contract["shared_experiment"]["historical_oos_windows"]
    if len(historical_windows) != 1:
        raise ModelComparisonHarnessError(
            "Model Comparison Harness v1 requires exactly one consumed historical OOS window"
        )
    historical_window = historical_windows[0]
    if historical_window.get("unseen_status") != "consumed_historical_oos":
        raise ModelComparisonHarnessError("Harness may materialize only consumed historical OOS")

    comparison_id = contract["comparison_id"]
    shared = contract["shared_experiment"]
    contract_sha256 = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    models: list[dict[str, Any]] = []

    for model_type in contract["models"]:
        slug = MODEL_SLUGS.get(model_type)
        if slug is None:
            raise ModelComparisonHarnessError(f"Unsupported model type: {model_type}")
        model_identity = contract["model_identities"][model_type]
        identity_sha256 = _sha256_payload(model_identity)
        experiment_identity = f"{comparison_id}-{slug}-{identity_sha256[:12]}"
        model_root = f"{output_root}/{comparison_id}/{slug}"
        config_path = f"{model_root}/config.json"
        manifest_path = f"{model_root}/manifest.json"
        run_output_root = f"{model_root}/runs"

        config = _materialized_config(
            baseline_config,
            model_type,
            experiment_identity,
            model_identity,
        )
        manifest = _materialized_manifest(
            comparison_id=comparison_id,
            model_type=model_type,
            experiment_identity=experiment_identity,
            config_path=config_path,
            output_root=run_output_root,
            shared=shared,
            historical_window=historical_window,
            download_timerange=baseline_manifest["download_timerange"],
        )
        models.append(
            {
                "model_type": model_type,
                "experiment_identity": experiment_identity,
                "identity_sha256": identity_sha256,
                "config_path": config_path,
                "manifest_path": manifest_path,
                "config_sha256": _sha256_payload(config),
                "manifest_sha256": _sha256_payload(manifest),
                "config": config,
                "manifest": manifest,
            }
        )

    return {
        "schema_version": 1,
        "comparison_id": comparison_id,
        "status": "materialized_only",
        "contract_path": contract_path.relative_to(REPO_ROOT).as_posix(),
        "contract_sha256": contract_sha256,
        "historical_oos_status": "consumed_historical_oos",
        "final_holdout_used": False,
        "execution_performed": False,
        "promotion_allowed": False,
        "profitability_claim_allowed": False,
        "models": models,
    }


def materialize_model_comparison(
    contract_path: Path = DEFAULT_CONTRACT,
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    """Write deterministic materialized inputs inside the repo and validate their holdout isolation."""
    output_dir = output_dir.resolve()
    output_root = _repo_relative(output_dir)
    materialization = build_materialization(contract_path, output_root=output_root)
    comparison_root = output_dir / materialization["comparison_id"]

    plan_models: list[dict[str, Any]] = []
    for model in materialization["models"]:
        config_path = REPO_ROOT / model["config_path"]
        manifest_path = REPO_ROOT / model["manifest_path"]
        _write_json(config_path, model["config"])
        _write_json(manifest_path, model["manifest"])
        load_manifest(manifest_path)
        plan_models.append(
            {key: value for key, value in model.items() if key not in {"config", "manifest"}}
        )

    plan = {
        key: value
        for key, value in materialization.items()
        if key != "models"
    }
    plan["models"] = plan_models
    plan_path = comparison_root / "materialization.json"
    _write_json(plan_path, plan)
    return plan_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "contract",
        nargs="?",
        type=Path,
        default=DEFAULT_CONTRACT,
        help="Path to the validated model-comparison contract",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Repository-local directory for materialized configs and manifests",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plan_path = materialize_model_comparison(
            args.contract,
            output_dir=args.output_dir,
        )
    except (ModelComparisonHarnessError, RuntimeError) as exc:
        print(f"Model comparison materialization failed: {exc}", file=sys.stderr)
        return 1
    print(plan_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
