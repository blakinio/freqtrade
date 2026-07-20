#!/usr/bin/env python3
"""Validate Phase 6 model-comparison provenance before final result assembly."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ai_platform.scripts.model_comparison_contract import load_model_comparison_contract
from ai_platform.scripts.model_comparison_harness import build_materialization
from ai_platform.scripts.model_comparison_selection_policy import (
    load_model_comparison_selection_policy,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = REPO_ROOT / "ai_platform/model_comparison/result-provenance-v1.json"
DEFAULT_SCHEMA = REPO_ROOT / "ai_platform/model_comparison/result-provenance-schema-v1.json"
DEFAULT_COMPARISON = REPO_ROOT / "ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json"
CANONICAL_MATERIALIZATION_ROOT = "ai_platform/artifacts/model-comparison/materialized"
EXPECTED_CONTRACT_ID = "freqai-model-comparison-result-provenance-v1"
EXPECTED_MODELS = ["LightGBMRegressor", "XGBoostRegressor"]
EXPECTED_AUTHORIZATION = {
    "final_holdout_used": False,
    "retuning_allowed": False,
    "promotion_allowed": False,
    "profitability_claim_allowed": False,
}


class ModelComparisonResultProvenanceError(RuntimeError):
    """Raised when model-comparison provenance is incomplete or inconsistent."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelComparisonResultProvenanceError(
            f"Unable to read {label} {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ModelComparisonResultProvenanceError(f"{label} must contain a JSON object")
    return payload


def _resolve_repo_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ModelComparisonResultProvenanceError(
            f"{label} must be a repository-relative path"
        )
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ModelComparisonResultProvenanceError(f"{label} escapes repository root") from exc
    return candidate


def _json_file_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_canonical_materialization_plan() -> dict[str, Any]:
    """Rebuild the exact materialization.json payload produced by the Phase 6 harness."""
    materialization = build_materialization(
        DEFAULT_COMPARISON,
        output_root=CANONICAL_MATERIALIZATION_ROOT,
    )
    plan_models = [
        {key: value for key, value in model.items() if key not in {"config", "manifest"}}
        for model in materialization["models"]
    ]
    plan = {key: value for key, value in materialization.items() if key != "models"}
    plan["models"] = plan_models
    return plan


def canonical_provenance_basis() -> dict[str, Any]:
    """Return deterministic plan and per-model hashes required by provenance validation."""
    plan = build_canonical_materialization_plan()
    models = {
        model["model_type"]: {
            "experiment_identity": model["experiment_identity"],
            "manifest_sha256": model["manifest_sha256"],
            "config_sha256": model["config_sha256"],
        }
        for model in plan["models"]
    }
    return {
        "comparison_id": plan["comparison_id"],
        "materialization_plan_sha256": _sha256_bytes(_json_file_bytes(plan)),
        "models": models,
    }


def _validate_contract_semantics(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != 1:
        raise ModelComparisonResultProvenanceError(
            "Only result provenance contract schema_version 1 is supported"
        )
    if contract.get("provenance_contract_id") != EXPECTED_CONTRACT_ID:
        raise ModelComparisonResultProvenanceError("Unexpected provenance_contract_id")
    if contract.get("authorization") != EXPECTED_AUTHORIZATION:
        raise ModelComparisonResultProvenanceError(
            "Result provenance cannot authorize holdout use, retuning, promotion, or claims"
        )

    materialization = contract.get("materialization")
    if materialization != {
        "filename": "materialization.json",
        "digest_algorithm": "sha256",
        "digest_scope": "exact_file_bytes",
        "result_field": "plan_sha256",
        "required_model_bindings": [
            "model_type",
            "experiment_identity",
            "manifest_sha256",
            "config_sha256",
        ],
    }:
        raise ModelComparisonResultProvenanceError("Materialization provenance semantics drifted")

    execution = contract.get("execution")
    if execution != {
        "run_provenance_filename": "provenance.json",
        "required_stage": "backtest",
        "result_field": "git_commit",
        "result_field_semantics": "shared_model_execution_commit",
        "same_execution_git_commit_required": True,
        "required_run_provenance_fields": [
            "stage",
            "git_commit",
            "manifest_sha256",
            "config_sha256",
            "strategy_sha256",
        ],
        "manifest_sha256_must_match_materialization": True,
        "config_sha256_must_match_materialization": True,
        "strategy_sha256_must_match_between_models": True,
    }:
        raise ModelComparisonResultProvenanceError("Execution provenance semantics drifted")


def load_model_comparison_result_provenance_contract(
    path: Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = _read_json(path.resolve(), "model comparison result provenance contract")
    _validate_contract_semantics(contract)
    load_model_comparison_contract(
        _resolve_repo_path(contract.get("comparison_contract"), "comparison_contract")
    )
    load_model_comparison_selection_policy(
        _resolve_repo_path(contract.get("selection_policy"), "selection_policy")
    )
    _read_json(
        _resolve_repo_path(
            contract.get("selection_decision_schema"),
            "selection_decision_schema",
        ),
        "selection decision schema",
    )
    _read_json(
        _resolve_repo_path(contract.get("extraction_schema"), "extraction_schema"),
        "OOS extraction schema",
    )
    return contract


def _validate_model_sources(
    evidence: dict[str, Any],
    basis: dict[str, Any],
) -> None:
    model_sources = evidence["model_sources"]
    by_model = {source["model_type"]: source for source in model_sources}
    if set(by_model) != set(EXPECTED_MODELS) or len(by_model) != 2:
        raise ModelComparisonResultProvenanceError(
            "Result provenance requires exactly one source per canonical model"
        )

    strategy_hashes: set[str] = set()
    for model_type in EXPECTED_MODELS:
        source = by_model[model_type]
        expected = basis["models"][model_type]
        if source["experiment_identity"] != expected["experiment_identity"]:
            raise ModelComparisonResultProvenanceError(
                f"Experiment identity drifted for {model_type}"
            )
        if source["materialized_manifest_sha256"] != expected["manifest_sha256"]:
            raise ModelComparisonResultProvenanceError(
                f"Materialized manifest hash drifted for {model_type}"
            )
        if source["materialized_config_sha256"] != expected["config_sha256"]:
            raise ModelComparisonResultProvenanceError(
                f"Materialized config hash drifted for {model_type}"
            )

        run_provenance = source["run_provenance"]
        if run_provenance["git_commit"] != evidence["execution_git_commit"]:
            raise ModelComparisonResultProvenanceError(
                "All run provenance records must use the shared execution git commit"
            )
        if run_provenance["manifest_sha256"] != source["materialized_manifest_sha256"]:
            raise ModelComparisonResultProvenanceError(
                f"Run manifest hash does not match materialization for {model_type}"
            )
        if run_provenance["config_sha256"] != source["materialized_config_sha256"]:
            raise ModelComparisonResultProvenanceError(
                f"Run config hash does not match materialization for {model_type}"
            )
        strategy_hashes.add(run_provenance["strategy_sha256"])

    if len(strategy_hashes) != 1:
        raise ModelComparisonResultProvenanceError(
            "Both model executions must use the same strategy hash"
        )


def validate_model_comparison_result_provenance(
    evidence: dict[str, Any],
    contract_path: Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    """Validate a provenance evidence object against canonical Phase 6 bindings."""
    load_model_comparison_result_provenance_contract(contract_path)
    schema = _read_json(DEFAULT_SCHEMA, "result provenance schema")
    try:
        Draft202012Validator(schema).validate(evidence)
    except ValidationError as exc:
        raise ModelComparisonResultProvenanceError(
            f"Result provenance evidence does not match schema: {exc.message}"
        ) from exc

    basis = canonical_provenance_basis()
    if evidence["comparison_id"] != basis["comparison_id"]:
        raise ModelComparisonResultProvenanceError("Comparison id drifted from materialization plan")
    if evidence["materialization_plan_sha256"] != basis["materialization_plan_sha256"]:
        raise ModelComparisonResultProvenanceError(
            "Materialization plan hash does not match canonical exact-file bytes"
        )
    _validate_model_sources(evidence, basis)
    return evidence


def result_binding_values(evidence: dict[str, Any]) -> dict[str, str]:
    """Return the only valid mapping into result-schema-v1 provenance fields."""
    validated = validate_model_comparison_result_provenance(evidence)
    return {
        "git_commit": validated["execution_git_commit"],
        "plan_sha256": validated["materialization_plan_sha256"],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="Path to result provenance evidence JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        evidence = _read_json(args.evidence.resolve(), "result provenance evidence")
        validate_model_comparison_result_provenance(evidence)
    except ModelComparisonResultProvenanceError as exc:
        print(f"Model comparison result provenance invalid: {exc}", file=sys.stderr)
        return 1
    print(evidence["provenance_contract_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
