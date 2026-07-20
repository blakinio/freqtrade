#!/usr/bin/env python3
"""Bind actual Phase 6 comparison artifacts into validated provenance evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_platform.scripts.model_comparison_result_provenance import (
    EXPECTED_MODELS,
    ModelComparisonResultProvenanceError,
    build_canonical_materialization_plan,
    canonical_provenance_basis,
    validate_model_comparison_result_provenance,
)
from ai_platform.scripts.model_comparison_selection_policy import (
    ModelComparisonSelectionPolicyError,
    evaluate_model_selection,
)


class ModelComparisonProvenanceBindingError(RuntimeError):
    """Raised when actual comparison artifacts cannot be bound safely."""


@dataclass(frozen=True)
class ModelArtifactFiles:
    """Actual artifact files required to bind one canonical model execution."""

    run_provenance: Path
    backtest_archive: Path
    extraction: Path


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ModelComparisonProvenanceBindingError(
            f"Unable to read {label} {path}: {exc}"
        ) from exc


def _read_json_artifact(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    payload_bytes = _read_bytes(path, label)
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise ModelComparisonProvenanceBindingError(
            f"Unable to parse {label} {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ModelComparisonProvenanceBindingError(f"{label} must contain a JSON object")
    return payload, payload_bytes


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_file_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _validate_model_artifact_keys(model_artifacts: dict[str, ModelArtifactFiles]) -> None:
    if set(model_artifacts) != set(EXPECTED_MODELS) or len(model_artifacts) != 2:
        raise ModelComparisonProvenanceBindingError(
            "Provenance binding requires exactly one artifact set per canonical model"
        )


def bind_model_comparison_provenance(
    materialization_path: Path,
    *,
    model_artifacts: dict[str, ModelArtifactFiles],
    selection_decision_path: Path,
) -> dict[str, Any]:
    """Verify actual artifact bytes and return bound result-provenance evidence."""
    _validate_model_artifact_keys(model_artifacts)

    basis = canonical_provenance_basis()
    canonical_plan = build_canonical_materialization_plan()
    materialization, materialization_bytes = _read_json_artifact(
        materialization_path.resolve(),
        "materialization plan",
    )
    if materialization != canonical_plan:
        raise ModelComparisonProvenanceBindingError(
            "Materialization plan content does not match the canonical Phase 6 plan"
        )

    materialization_sha256 = _sha256_bytes(materialization_bytes)
    if materialization_sha256 != basis["materialization_plan_sha256"]:
        raise ModelComparisonProvenanceBindingError(
            "Materialization plan bytes do not match canonical materialization.json bytes"
        )

    plan_by_model = {model["model_type"]: model for model in materialization["models"]}
    model_sources: list[dict[str, Any]] = []
    extractions: list[dict[str, Any]] = []

    for model_type in EXPECTED_MODELS:
        plan_model = plan_by_model[model_type]
        artifacts = model_artifacts[model_type]

        run_provenance, run_provenance_bytes = _read_json_artifact(
            artifacts.run_provenance.resolve(),
            f"{model_type} run provenance",
        )
        if run_provenance.get("experiment_id") != plan_model["experiment_identity"]:
            raise ModelComparisonProvenanceBindingError(
                f"Run provenance experiment identity drifted for {model_type}"
            )

        backtest_archive_bytes = _read_bytes(
            artifacts.backtest_archive.resolve(),
            f"{model_type} backtest archive",
        )
        backtest_archive_sha256 = _sha256_bytes(backtest_archive_bytes)

        extraction, extraction_bytes = _read_json_artifact(
            artifacts.extraction.resolve(),
            f"{model_type} OOS extraction",
        )
        if extraction.get("model_type") != model_type:
            raise ModelComparisonProvenanceBindingError(
                f"OOS extraction model identity drifted for {model_type}"
            )
        if extraction.get("experiment_identity") != plan_model["experiment_identity"]:
            raise ModelComparisonProvenanceBindingError(
                f"OOS extraction experiment identity drifted for {model_type}"
            )
        if extraction.get("source", {}).get("archive_sha256") != backtest_archive_sha256:
            raise ModelComparisonProvenanceBindingError(
                "OOS extraction archive hash does not match bound backtest archive "
                f"for {model_type}"
            )

        model_sources.append(
            {
                "model_type": model_type,
                "experiment_identity": plan_model["experiment_identity"],
                "materialized_manifest_sha256": plan_model["manifest_sha256"],
                "materialized_config_sha256": plan_model["config_sha256"],
                "run_provenance_sha256": _sha256_bytes(run_provenance_bytes),
                "run_provenance": run_provenance,
                "backtest_archive_sha256": backtest_archive_sha256,
                "extraction_sha256": _sha256_bytes(extraction_bytes),
            }
        )
        extractions.append(extraction)

    try:
        expected_selection_decision = evaluate_model_selection(extractions)
    except ModelComparisonSelectionPolicyError as exc:
        raise ModelComparisonProvenanceBindingError(
            f"Bound OOS extractions cannot produce a valid selection decision: {exc}"
        ) from exc

    selection_decision, selection_decision_bytes = _read_json_artifact(
        selection_decision_path.resolve(),
        "selection decision",
    )
    if selection_decision != expected_selection_decision:
        raise ModelComparisonProvenanceBindingError(
            "Selection decision does not match the decision recomputed from bound OOS extractions"
        )

    execution_git_commit = model_sources[0]["run_provenance"].get("git_commit")
    evidence = {
        "schema_version": 1,
        "provenance_contract_id": "freqai-model-comparison-result-provenance-v1",
        "comparison_id": basis["comparison_id"],
        "materialization_plan_sha256": materialization_sha256,
        "execution_git_commit": execution_git_commit,
        "selection_policy_sha256": basis["selection_policy_sha256"],
        "selection_decision_sha256": _sha256_bytes(selection_decision_bytes),
        "model_sources": model_sources,
    }

    try:
        return validate_model_comparison_result_provenance(evidence)
    except ModelComparisonResultProvenanceError as exc:
        raise ModelComparisonProvenanceBindingError(
            f"Bound provenance evidence is invalid: {exc}"
        ) from exc


def write_bound_provenance(path: Path, evidence: dict[str, Any]) -> None:
    """Write deterministic bound provenance evidence without altering source artifact hashes."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_json_file_bytes(evidence))
    except OSError as exc:
        raise ModelComparisonProvenanceBindingError(
            f"Unable to write bound provenance evidence {path}: {exc}"
        ) from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("materialization", type=Path, help="Canonical materialization.json path")
    parser.add_argument("--lightgbm-run-provenance", type=Path, required=True)
    parser.add_argument("--lightgbm-backtest", type=Path, required=True)
    parser.add_argument("--lightgbm-extraction", type=Path, required=True)
    parser.add_argument("--xgboost-run-provenance", type=Path, required=True)
    parser.add_argument("--xgboost-backtest", type=Path, required=True)
    parser.add_argument("--xgboost-extraction", type=Path, required=True)
    parser.add_argument("--selection-decision", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    model_artifacts = {
        "LightGBMRegressor": ModelArtifactFiles(
            run_provenance=args.lightgbm_run_provenance,
            backtest_archive=args.lightgbm_backtest,
            extraction=args.lightgbm_extraction,
        ),
        "XGBoostRegressor": ModelArtifactFiles(
            run_provenance=args.xgboost_run_provenance,
            backtest_archive=args.xgboost_backtest,
            extraction=args.xgboost_extraction,
        ),
    }
    try:
        evidence = bind_model_comparison_provenance(
            args.materialization,
            model_artifacts=model_artifacts,
            selection_decision_path=args.selection_decision,
        )
        write_bound_provenance(args.output, evidence)
    except ModelComparisonProvenanceBindingError as exc:
        print(f"Model comparison provenance binding failed: {exc}", file=sys.stderr)
        return 1
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
