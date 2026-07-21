import hashlib
import json
from pathlib import Path

import pytest

from ai_platform.scripts.experimental_model_historical_backtest_run_request import (
    CONTRACT_PATH,
    EXPECTED_ACTION,
    EXPECTED_AUTHORIZATION,
    EXPECTED_FROZEN_PARAMETERS,
    EXPECTED_PROTECTED_FINAL_HOLDOUT,
    EXPECTED_REQUEST_ID,
    EXPECTED_TRACKS,
    REQUEST_REPO_PATH,
    ExperimentalModelHistoricalBacktestRunRequestError,
    canonical_experimental_model_historical_backtest_run_request,
    load_experimental_model_historical_backtest_run_request,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/experimental-model-historical-backtest-execution.yml"


def _write_request(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_canonical_request_pins_exact_two_isolated_tracks_and_boundaries() -> None:
    request = canonical_experimental_model_historical_backtest_run_request()

    assert request["schema_version"] == 1
    assert request["request_id"] == EXPECTED_REQUEST_ID
    assert request["action"] == EXPECTED_ACTION
    assert request["contract_sha256"] == hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()
    assert [track["track_id"] for track in request["tracks"]] == list(EXPECTED_TRACKS)
    assert request["semantic_prediction_window"] == "20260301-20260630"
    assert request["execution_timerange"] == "20260301-20260701"
    assert request["download_timerange"] == "20250801-20260701"
    assert request["strict_oos_scoring_window"] == "20260501-20260630"
    assert request["protected_final_holdout"] == EXPECTED_PROTECTED_FINAL_HOLDOUT["timerange"]
    assert request["frozen_parameters"] == EXPECTED_FROZEN_PARAMETERS
    assert request["authorization"] == EXPECTED_AUTHORIZATION

    for track in request["tracks"]:
        for field in (
            "manifest_sha256",
            "config_sha256",
            "strategy_sha256",
            "freqai_model_sha256",
        ):
            assert len(track[field]) == 64


def test_exact_canonical_request_is_accepted(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    expected = canonical_experimental_model_historical_backtest_run_request()
    _write_request(request_path, expected)

    assert load_experimental_model_historical_backtest_run_request(request_path) == expected


def test_request_rejects_contract_hash_drift(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    request = canonical_experimental_model_historical_backtest_run_request()
    request["contract_sha256"] = "0" * 64
    _write_request(request_path, request)

    with pytest.raises(
        ExperimentalModelHistoricalBacktestRunRequestError,
        match="contract_sha256",
    ):
        load_experimental_model_historical_backtest_run_request(request_path)


def test_request_rejects_track_input_hash_drift(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    request = canonical_experimental_model_historical_backtest_run_request()
    request["tracks"][0]["freqai_model_sha256"] = "0" * 64
    _write_request(request_path, request)

    with pytest.raises(ExperimentalModelHistoricalBacktestRunRequestError, match="tracks"):
        load_experimental_model_historical_backtest_run_request(request_path)


def test_request_rejects_final_holdout_authorization(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    request = canonical_experimental_model_historical_backtest_run_request()
    request["authorization"]["final_holdout_used"] = True
    _write_request(request_path, request)

    with pytest.raises(ExperimentalModelHistoricalBacktestRunRequestError, match="authorization"):
        load_experimental_model_historical_backtest_run_request(request_path)


def test_request_rejects_cross_track_selection_authorization(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    request = canonical_experimental_model_historical_backtest_run_request()
    request["authorization"]["cross_track_selection_allowed"] = True
    _write_request(request_path, request)

    with pytest.raises(ExperimentalModelHistoricalBacktestRunRequestError, match="authorization"):
        load_experimental_model_historical_backtest_run_request(request_path)


def test_request_rejects_extra_fields(tmp_path: Path) -> None:
    request_path = tmp_path / "run-request.json"
    request = canonical_experimental_model_historical_backtest_run_request()
    request["notes"] = "unexpected"
    _write_request(request_path, request)

    with pytest.raises(ExperimentalModelHistoricalBacktestRunRequestError, match="extra=notes"):
        load_experimental_model_historical_backtest_run_request(request_path)


def test_workflow_is_one_shot_request_only_and_has_no_selection_stage() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "types: [opened]" in workflow
    assert REQUEST_REPO_PATH in workflow
    assert "workflow_dispatch" not in workflow
    assert "evaluate_model_selection" not in workflow
    assert "model_comparison_selection_policy" not in workflow
    assert "20260801-20260930" not in workflow
