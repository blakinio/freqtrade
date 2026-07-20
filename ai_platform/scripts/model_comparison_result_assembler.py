#!/usr/bin/env python3
"""Assemble the final Phase 6 comparison result from already-bound evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ai_platform.scripts.model_comparison_result_provenance import (
    EXPECTED_MODELS,
    ModelComparisonResultProvenanceError,
    result_binding_values,
    validate_model_comparison_result_provenance,
)
from ai_platform.scripts.model_comparison_selection_policy import (
    ModelComparisonSelectionPolicyError,
    evaluate_model_selection,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULT_SCHEMA = ROOT / "ai_platform" / "model_comparison" / "result-schema-v1.json"


class ModelComparisonResultAssemblerError(RuntimeError):
    """Raised when bound Phase 6 evidence cannot be assembled safely."""


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ModelComparisonResultAssemblerError(f"Unable to read {label} {path}: {exc}") from exc


def _read_json_artifact(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    payload_bytes = _read_bytes(path, label)
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise ModelComparisonResultAssemblerError(f"Unable to parse {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ModelComparisonResultAssemblerError(f"{label} must contain a JSON object")
    return payload, payload_bytes


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_file_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _validate_extraction_paths(extraction_paths: dict[str, Path]) -> None:
    if set(extraction_paths) != set(EXPECTED_MODELS) or len(extraction_paths) != 2:
        raise ModelComparisonResultAssemblerError(
            "Final result assembly requires exactly one extraction path per canonical model"
        )


def _load_result_schema(path: Path = DEFAULT_RESULT_SCHEMA) -> dict[str, Any]:
    schema, _ = _read_json_artifact(path.resolve(), "model comparison result schema")
    return schema


def validate_model_comparison_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate a completed model-comparison result against the tracked result schema."""
    schema = _load_result_schema()
    try:
        Draft202012Validator(schema).validate(result)
    except ValidationError as exc:
        raise ModelComparisonResultAssemblerError(
            f"Model comparison result does not match schema: {exc.message}"
        ) from exc
    return result


def assemble_model_comparison_result(
    provenance_path: Path,
    *,
    extraction_paths: dict[str, Path],
    selection_decision_path: Path,
) -> dict[str, Any]:
    """Assemble a completed result from bound provenance and existing comparison artifacts."""
    _validate_extraction_paths(extraction_paths)

    provenance, _ = _read_json_artifact(provenance_path.resolve(), "result provenance evidence")
    try:
        validated_provenance = validate_model_comparison_result_provenance(provenance)
        bindings = result_binding_values(validated_provenance)
    except ModelComparisonResultProvenanceError as exc:
        raise ModelComparisonResultAssemblerError(
            f"Result provenance evidence is invalid: {exc}"
        ) from exc

    source_by_model = {
        source["model_type"]: source for source in validated_provenance["model_sources"]
    }
    extractions: list[dict[str, Any]] = []
    model_results: list[dict[str, Any]] = []

    for model_type in EXPECTED_MODELS:
        source = source_by_model[model_type]
        extraction_path = extraction_paths[model_type]
        extraction, extraction_bytes = _read_json_artifact(
            extraction_path.resolve(),
            f"{model_type} OOS extraction",
        )
        if _sha256_bytes(extraction_bytes) != source["extraction_sha256"]:
            raise ModelComparisonResultAssemblerError(
                f"OOS extraction exact-byte hash does not match bound provenance for {model_type}"
            )
        if extraction.get("model_type") != model_type:
            raise ModelComparisonResultAssemblerError(
                f"OOS extraction model identity drifted for {model_type}"
            )
        if extraction.get("experiment_identity") != source["experiment_identity"]:
            raise ModelComparisonResultAssemblerError(
                f"OOS extraction experiment identity drifted for {model_type}"
            )

        metrics = extraction.get("metrics")
        if not isinstance(metrics, dict):
            raise ModelComparisonResultAssemblerError(
                f"OOS extraction metrics missing for {model_type}"
            )
        model_results.append(
            {
                "model_type": model_type,
                "experiment_identity": source["experiment_identity"],
                "metrics": {
                    "profit": metrics.get("profit"),
                    "drawdown": metrics.get("drawdown"),
                    "trades": metrics.get("trades"),
                    "stability": metrics.get("stability"),
                },
                "artifact_paths": [extraction_path.as_posix()],
            }
        )
        extractions.append(extraction)

    try:
        expected_selection_decision = evaluate_model_selection(extractions)
    except ModelComparisonSelectionPolicyError as exc:
        raise ModelComparisonResultAssemblerError(
            f"Bound OOS extractions cannot produce a valid selection decision: {exc}"
        ) from exc

    selection_decision, selection_decision_bytes = _read_json_artifact(
        selection_decision_path.resolve(),
        "selection decision",
    )
    selection_decision_sha256 = validated_provenance["selection_decision_sha256"]
    if _sha256_bytes(selection_decision_bytes) != selection_decision_sha256:
        raise ModelComparisonResultAssemblerError(
            "Selection decision exact-byte hash does not match bound provenance"
        )
    if selection_decision != expected_selection_decision:
        raise ModelComparisonResultAssemblerError(
            "Selection decision does not match the decision recomputed from bound OOS extractions"
        )

    first_extraction = extractions[0]
    result = {
        "schema_version": 1,
        "comparison_id": validated_provenance["comparison_id"],
        "metric_semantics_id": first_extraction["metric_semantics_id"],
        "oos_trade_boundary_id": first_extraction["oos_trade_boundary_id"],
        "status": "completed",
        "git_commit": bindings["git_commit"],
        "plan_sha256": bindings["plan_sha256"],
        "model_results": model_results,
        "selection": selection_decision["selection"],
    }
    return validate_model_comparison_result(result)


def write_model_comparison_result(path: Path, result: dict[str, Any]) -> None:
    """Write a deterministic completed comparison result after validation."""
    validate_model_comparison_result(result)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_json_file_bytes(result))
    except OSError as exc:
        raise ModelComparisonResultAssemblerError(
            f"Unable to write model comparison result {path}: {exc}"
        ) from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provenance", type=Path, help="Bound result-provenance evidence JSON")
    parser.add_argument("--lightgbm-extraction", type=Path, required=True)
    parser.add_argument("--xgboost-extraction", type=Path, required=True)
    parser.add_argument("--selection-decision", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    extraction_paths = {
        "LightGBMRegressor": args.lightgbm_extraction,
        "XGBoostRegressor": args.xgboost_extraction,
    }
    try:
        result = assemble_model_comparison_result(
            args.provenance,
            extraction_paths=extraction_paths,
            selection_decision_path=args.selection_decision,
        )
        write_model_comparison_result(args.output, result)
    except ModelComparisonResultAssemblerError as exc:
        print(f"Model comparison result assembly failed: {exc}", file=sys.stderr)
        return 1
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
