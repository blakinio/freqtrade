import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from ai_platform.scripts.model_comparison_result_provenance import (
    DEFAULT_CONTRACT,
    DEFAULT_SCHEMA,
    ModelComparisonResultProvenanceError,
    canonical_provenance_basis,
    load_model_comparison_result_provenance_contract,
    result_binding_values,
    validate_model_comparison_result_provenance,
)


ROOT = Path(__file__).resolve().parents[2]
RESULT_SCHEMA = ROOT / "ai_platform/model_comparison/result-schema-v1.json"


def _evidence() -> dict[str, Any]:
    basis = canonical_provenance_basis()
    execution_commit = "c" * 40
    strategy_sha256 = "d" * 64
    sources = []
    for index, model_type in enumerate(("LightGBMRegressor", "XGBoostRegressor")):
        model = basis["models"][model_type]
        sources.append(
            {
                "model_type": model_type,
                "experiment_identity": model["experiment_identity"],
                "materialized_manifest_sha256": model["manifest_sha256"],
                "materialized_config_sha256": model["config_sha256"],
                "run_provenance_sha256": ("e" if index == 0 else "f") * 64,
                "run_provenance": {
                    "stage": "backtest",
                    "git_commit": execution_commit,
                    "manifest_sha256": model["manifest_sha256"],
                    "config_sha256": model["config_sha256"],
                    "strategy_sha256": strategy_sha256,
                    "experiment_id": model["experiment_identity"],
                },
                "backtest_archive_sha256": ("1" if index == 0 else "2") * 64,
                "extraction_sha256": ("3" if index == 0 else "4") * 64,
            }
        )
    return {
        "schema_version": 1,
        "provenance_contract_id": "freqai-model-comparison-result-provenance-v1",
        "comparison_id": basis["comparison_id"],
        "materialization_plan_sha256": basis["materialization_plan_sha256"],
        "execution_git_commit": execution_commit,
        "selection_policy_sha256": basis["selection_policy_sha256"],
        "selection_decision_sha256": "6" * 64,
        "model_sources": sources,
    }


def test_result_provenance_contract_and_evidence_are_valid() -> None:
    contract = load_model_comparison_result_provenance_contract(DEFAULT_CONTRACT)
    evidence = _evidence()
    schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(evidence)
    assert contract["execution"]["result_field"] == "git_commit"
    assert contract["execution"]["result_field_semantics"] == "shared_model_execution_commit"
    assert contract["execution"]["run_provenance_digest_scope"] == "exact_file_bytes"
    assert contract["materialization"]["result_field"] == "plan_sha256"
    assert contract["extraction"]["backtest_archive_digest_scope"] == "exact_file_bytes"
    assert contract["selection"]["selection_decision_digest_scope"] == "exact_file_bytes"
    assert validate_model_comparison_result_provenance(evidence) == evidence


def test_result_binding_maps_only_execution_commit_and_exact_plan_hash() -> None:
    evidence = _evidence()

    assert result_binding_values(evidence) == {
        "git_commit": evidence["execution_git_commit"],
        "plan_sha256": evidence["materialization_plan_sha256"],
    }


def test_result_provenance_rejects_materialization_plan_hash_drift() -> None:
    evidence = _evidence()
    evidence["materialization_plan_sha256"] = "0" * 64

    with pytest.raises(ModelComparisonResultProvenanceError, match="Materialization plan hash"):
        validate_model_comparison_result_provenance(evidence)


def test_result_provenance_rejects_selection_policy_hash_drift() -> None:
    evidence = _evidence()
    evidence["selection_policy_sha256"] = "0" * 64

    with pytest.raises(ModelComparisonResultProvenanceError, match="Selection policy hash"):
        validate_model_comparison_result_provenance(evidence)


def test_result_provenance_rejects_mixed_execution_commit() -> None:
    evidence = _evidence()
    evidence["model_sources"][1]["run_provenance"]["git_commit"] = "a" * 40

    with pytest.raises(ModelComparisonResultProvenanceError, match="shared execution git commit"):
        validate_model_comparison_result_provenance(evidence)


def test_result_provenance_rejects_run_manifest_hash_drift() -> None:
    evidence = _evidence()
    evidence["model_sources"][0]["run_provenance"]["manifest_sha256"] = "0" * 64

    with pytest.raises(ModelComparisonResultProvenanceError, match="Run manifest hash"):
        validate_model_comparison_result_provenance(evidence)


def test_result_provenance_rejects_run_config_hash_drift() -> None:
    evidence = _evidence()
    evidence["model_sources"][0]["run_provenance"]["config_sha256"] = "0" * 64

    with pytest.raises(ModelComparisonResultProvenanceError, match="Run config hash"):
        validate_model_comparison_result_provenance(evidence)


def test_result_provenance_rejects_noncanonical_experiment_identity() -> None:
    evidence = _evidence()
    evidence["model_sources"][1]["experiment_identity"] = "drifted-xgboost-identity"

    with pytest.raises(ModelComparisonResultProvenanceError, match="Experiment identity drifted"):
        validate_model_comparison_result_provenance(evidence)


def test_result_provenance_rejects_strategy_hash_mismatch() -> None:
    evidence = _evidence()
    evidence["model_sources"][1]["run_provenance"]["strategy_sha256"] = "9" * 64

    with pytest.raises(ModelComparisonResultProvenanceError, match="same strategy hash"):
        validate_model_comparison_result_provenance(evidence)


def test_result_provenance_rejects_duplicate_model_sources() -> None:
    evidence = _evidence()
    evidence["model_sources"][1] = copy.deepcopy(evidence["model_sources"][0])

    with pytest.raises(
        ModelComparisonResultProvenanceError,
        match="one source per canonical model",
    ):
        validate_model_comparison_result_provenance(evidence)


def test_provenance_bindings_fit_existing_result_schema() -> None:
    evidence = _evidence()
    bindings = result_binding_values(evidence)
    result = {
        "schema_version": 1,
        "comparison_id": "freqai-lightgbm-vs-xgboost-v1",
        "metric_semantics_id": "freqai-model-comparison-metrics-v1",
        "oos_trade_boundary_id": "freqai-model-comparison-oos-trade-boundary-v1",
        "status": "completed",
        **bindings,
        "model_results": [
            {
                "model_type": "LightGBMRegressor",
                "experiment_identity": evidence["model_sources"][0]["experiment_identity"],
                "metrics": {
                    "profit": 0.01,
                    "drawdown": 0.10,
                    "trades": 10,
                    "stability": 0.5,
                },
                "artifact_paths": ["lightgbm-extraction.json"],
            },
            {
                "model_type": "XGBoostRegressor",
                "experiment_identity": evidence["model_sources"][1]["experiment_identity"],
                "metrics": {
                    "profit": 0.02,
                    "drawdown": 0.09,
                    "trades": 10,
                    "stability": 1.0,
                },
                "artifact_paths": ["xgboost-extraction.json"],
            },
        ],
        "selection": {
            "selected_model": "XGBoostRegressor",
            "basis": "strict_pareto_dominance_among_eligible_models",
            "final_holdout_used": False,
            "promotion_allowed": False,
            "profitability_claim_allowed": False,
        },
    }
    schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(result)
