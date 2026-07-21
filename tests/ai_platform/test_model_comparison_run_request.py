import hashlib
import json
from pathlib import Path

import pytest

from ai_platform.scripts.model_comparison_run_request import (
    CONTRACT_PATH,
    EXPECTED_AUTHORIZATION,
    EXPECTED_FROZEN_PARAMETERS,
    EXPECTED_PROTECTED_FINAL_HOLDOUT,
    EXPECTED_WINDOWS,
    ModelComparisonRunRequestError,
    canonical_model_comparison_run_request,
    load_model_comparison_run_request,
)


def _write_request(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_canonical_run_request_pins_historical_only_execution_boundary() -> None:
    request = canonical_model_comparison_run_request()

    assert request["schema_version"] == 1
    assert request["action"] == "execute_historical_model_comparison"
    assert request["comparison_id"] == "freqai-lightgbm-vs-xgboost-v1"
    assert {field: request[field] for field in EXPECTED_WINDOWS} == EXPECTED_WINDOWS
    assert request["protected_final_holdout"] == EXPECTED_PROTECTED_FINAL_HOLDOUT
    assert request["frozen_parameters"] == EXPECTED_FROZEN_PARAMETERS
    assert request["authorization"] == EXPECTED_AUTHORIZATION
    assert (
        request["contract_sha256"]
        == hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()
    )


def test_exact_canonical_run_request_is_accepted(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    expected = canonical_model_comparison_run_request()
    _write_request(request_path, expected)

    assert load_model_comparison_run_request(request_path) == expected


def test_run_request_rejects_contract_hash_drift(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    request = canonical_model_comparison_run_request()
    request["contract_sha256"] = "0" * 64
    _write_request(request_path, request)

    with pytest.raises(ModelComparisonRunRequestError, match="contract_sha256"):
        load_model_comparison_run_request(request_path)


def test_run_request_rejects_final_holdout_authorization(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    request = canonical_model_comparison_run_request()
    request["authorization"]["final_holdout_used"] = True
    _write_request(request_path, request)

    with pytest.raises(ModelComparisonRunRequestError, match="authorization"):
        load_model_comparison_run_request(request_path)


def test_run_request_rejects_frozen_threshold_drift(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    request = canonical_model_comparison_run_request()
    request["frozen_parameters"]["entry_prediction_threshold"] = 0.007
    _write_request(request_path, request)

    with pytest.raises(ModelComparisonRunRequestError, match="frozen_parameters"):
        load_model_comparison_run_request(request_path)


def test_run_request_rejects_extra_fields(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    request = canonical_model_comparison_run_request()
    request["notes"] = "unexpected"
    _write_request(request_path, request)

    with pytest.raises(ModelComparisonRunRequestError, match="extra=notes"):
        load_model_comparison_run_request(request_path)
