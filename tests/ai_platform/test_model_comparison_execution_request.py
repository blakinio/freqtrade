import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ai_platform.scripts.model_comparison_execution_request import (
    DEFAULT_REQUEST,
    EXPECTED_DOWNLOAD_TIMERANGE,
    EXPECTED_FINAL_HOLDOUT,
    EXPECTED_HISTORICAL_OOS,
    EXPECTED_MODELS,
    ModelComparisonExecutionRequestError,
    expected_execution_request,
    validate_execution_request,
)


ROOT = Path(__file__).resolve().parents[2]
REQUEST_SCHEMA = (
    ROOT / "ai_platform/model_comparison/historical-comparison-run-request-schema-v1.json"
)
WORKFLOW = ROOT / ".github/workflows/ai-platform-phase6-historical-comparison.yml"


def _write_request(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_expected_historical_comparison_request_matches_schema() -> None:
    request = expected_execution_request()
    schema = json.loads(REQUEST_SCHEMA.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(request)
    assert request["models"] == EXPECTED_MODELS
    assert request["historical_oos_timerange"] == EXPECTED_HISTORICAL_OOS
    assert request["historical_oos_status"] == "consumed_historical_oos"
    assert request["download_timerange"] == EXPECTED_DOWNLOAD_TIMERANGE
    assert request["protected_final_holdout"] == EXPECTED_FINAL_HOLDOUT
    assert request["execution_commit_policy"] == "pull_request_head_sha"
    assert request["trigger_change_policy"] == "request_file_only"
    assert request["final_holdout_used"] is False
    assert request["retuning_allowed"] is False
    assert request["model_parameter_tuning_allowed"] is False
    assert request["feature_changes_allowed"] is False
    assert request["promotion_allowed"] is False
    assert request["live_trading_allowed"] is False
    assert request["profitability_claim_allowed"] is False
    assert request["unseen_final_evidence_claim_allowed"] is False


def test_infrastructure_does_not_include_the_trigger_request() -> None:
    assert not DEFAULT_REQUEST.exists()


def test_exact_request_validates(tmp_path: Path) -> None:
    request_path = tmp_path / "historical-comparison-v1.json"
    request = expected_execution_request()
    _write_request(request_path, request)

    assert validate_execution_request(request_path) == request


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("comparison_contract_sha256", "0" * 64),
        ("selection_policy_sha256", "0" * 64),
        ("models", ["XGBoostRegressor", "LightGBMRegressor"]),
        ("historical_oos_timerange", "20260801-20260930"),
        ("download_timerange", "20250801-20260930"),
        ("final_holdout_used", True),
        ("retuning_allowed", True),
        ("model_parameter_tuning_allowed", True),
        ("feature_changes_allowed", True),
        ("promotion_allowed", True),
        ("live_trading_allowed", True),
        ("profitability_claim_allowed", True),
        ("unseen_final_evidence_claim_allowed", True),
    ],
)
def test_request_drift_fails_closed(tmp_path: Path, field: str, value: object) -> None:
    request = copy.deepcopy(expected_execution_request())
    request[field] = value
    request_path = tmp_path / "historical-comparison-v1.json"
    _write_request(request_path, request)

    with pytest.raises(ModelComparisonExecutionRequestError, match="request drifted"):
        validate_execution_request(request_path)


def test_workflow_is_request_only_and_orders_gate_before_data_access() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    request_path = "ai_platform/model_comparison/run-requests/historical-comparison-v1.json"

    assert request_path in workflow
    assert "types: [opened]" in workflow
    assert "workflow_dispatch" not in workflow
    assert 'git diff --name-only "$BASE_SHA" "$HEAD_SHA"' in workflow
    assert "model_comparison_execution_request" in workflow

    gate_index = workflow.index("Validate request-only trigger and frozen Phase 6 contract")
    install_index = workflow.index("Install uv and Python")
    cache_index = workflow.index("Restore dedicated Kraken historical data cache")
    download_index = workflow.index("Download exact declared Kraken history through 2026-06-30")
    assert gate_index < install_index < cache_index < download_index


def test_workflow_chains_complete_historical_comparison_pipeline() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count("python -m ai_platform.scripts.run_experiment") == 2
    assert workflow.count("model_comparison_oos_result_extractor") == 2
    assert "evaluate_model_selection" in workflow
    assert "model_comparison_provenance_binding" in workflow
    assert "model_comparison_result_assembler" in workflow
    assert "20250801-20260630" in workflow
    assert "20260501-20260630" in workflow
    assert "20260801-20260930" not in workflow
