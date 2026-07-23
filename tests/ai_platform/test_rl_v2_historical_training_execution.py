from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ai_platform.scripts.rl_v2_historical_training_execution_run_request import (
    BASE_CONFIG_REPO_PATH,
    CONTRACT_PATH,
    EXPECTED_EXECUTION,
    EXPECTED_REQUEST_ID,
    REQUEST_REPO_PATH,
    RLV2HistoricalTrainingExecutionError,
    canonical_rl_v2_historical_training_execution_request,
    load_rl_v2_historical_training_execution_request,
    materialize_runtime_config,
)


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github/workflows/ai-platform-rl-v2-historical-training-execution.yml"
BASE_CONFIG_PATH = ROOT / BASE_CONFIG_REPO_PATH


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_contract_freezes_pre_consumed_oos_geometry() -> None:
    contract = _load_json(CONTRACT_PATH)
    geometry = contract["execution_geometry"]
    evidence = contract["evidence"]
    isolation = contract["isolation"]

    assert contract["contract_id"] == EXPECTED_REQUEST_ID
    assert geometry == EXPECTED_EXECUTION
    assert geometry["download_timerange"] == "20250801-20260501"
    assert geometry["execution_timerange"] == "20260301-20260501"
    assert geometry["semantic_evidence_window"] == "20260301-20260430"
    assert geometry["train_period_days"] == 90
    assert geometry["backtest_period_days"] == 61
    assert evidence["classification"] == "historical_development_evidence"
    assert evidence["strict_oos"] is False
    assert evidence["protected_final_validation"] is False
    assert isolation["consumed_historical_oos"]["usage"] == "forbidden"
    assert isolation["protected_final_holdout"]["usage"] == "forbidden"


def test_contract_keeps_execution_one_shot_and_non_promotional() -> None:
    contract = _load_json(CONTRACT_PATH)
    trigger = contract["trigger"]
    authorization = contract["authorization"]

    assert contract["request_path"] == REQUEST_REPO_PATH
    assert trigger == {
        "event": "pull_request_opened",
        "base_branch": "develop",
        "exact_one_file": True,
    }
    assert authorization["infrastructure_merge_executes_model"] is False
    assert authorization["canonical_request_required"] is True
    assert authorization["strict_oos_scoring_allowed"] is False
    assert authorization["consumed_historical_oos_access_allowed"] is False
    assert authorization["protected_final_holdout_access_allowed"] is False
    assert authorization["retuning_allowed"] is False
    assert authorization["cross_track_selection_allowed"] is False
    assert authorization["promotion_allowed"] is False
    assert authorization["live_trading_allowed"] is False
    assert authorization["profitability_claim_allowed"] is False
    assert authorization["superiority_claim_allowed"] is False


def test_canonical_request_binds_exact_repository_inputs() -> None:
    request = canonical_rl_v2_historical_training_execution_request()

    assert request["request_id"] == EXPECTED_REQUEST_ID
    assert request["action"] == "execute_rl_v2_historical_training_backtest"
    assert request["download_timerange"] == "20250801-20260501"
    assert request["execution_timerange"] == "20260301-20260501"
    assert request["semantic_evidence_window"] == "20260301-20260430"
    assert request["train_period_days"] == 90
    assert request["backtest_period_days"] == 61
    assert request["strict_oos"] is False
    assert request["evidence_classification"] == "historical_development_evidence"
    assert request["consumed_historical_oos"] == "20260501-20260630"
    assert request["protected_final_holdout"] == "20260801-20260930"
    for field in (
        "contract_sha256",
        "training_configuration_descriptor_sha256",
        "config_sha256",
        "freqai_model_sha256",
        "strategy_sha256",
        "validator_sha256",
        "workflow_sha256",
    ):
        assert len(request[field]) == 64


def test_request_loader_rejects_any_payload_drift(tmp_path: Path) -> None:
    canonical = canonical_rl_v2_historical_training_execution_request()
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(canonical), encoding="utf-8")
    assert load_rl_v2_historical_training_execution_request(request_path) == canonical

    mutated = deepcopy(canonical)
    mutated["strict_oos"] = True
    request_path.write_text(json.dumps(mutated), encoding="utf-8")
    with pytest.raises(
        RLV2HistoricalTrainingExecutionError,
        match="strict_oos",
    ):
        load_rl_v2_historical_training_execution_request(request_path)


def test_runtime_materialization_adds_only_frozen_freqai_geometry(tmp_path: Path) -> None:
    before = _load_json(BASE_CONFIG_PATH)
    output = tmp_path / "runtime-config.json"
    materialize_runtime_config(output)
    after = _load_json(output)

    expected = deepcopy(before)
    expected["freqai"]["train_period_days"] = 90
    expected["freqai"]["backtest_period_days"] = 61
    assert after == expected
    assert "timerange" not in after
    assert "live_retrain_hours" not in after["freqai"]
    assert _load_json(BASE_CONFIG_PATH) == before


def test_runtime_materialization_refuses_base_config_overwrite() -> None:
    with pytest.raises(
        RLV2HistoricalTrainingExecutionError,
        match="immutable base config",
    ):
        materialize_runtime_config(BASE_CONFIG_PATH)


def test_workflow_is_request_triggered_and_has_no_strict_oos_extractor() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "types: [opened]" in source
    assert REQUEST_REPO_PATH in source
    assert "workflow_dispatch" not in source
    assert "experimental_model_oos_result_extractor" not in source
    assert "20260501-20260630" not in source
    assert "20260801-20260930" not in source
    assert "historical_development_evidence" not in source
    assert "strict_oos" in source
    assert '"strict_oos": False' in source


def test_workflow_uses_dedicated_pre_oos_cache_without_restore_fallbacks() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "rl-v2-historical-training-pre-oos-v1" in source
    assert "restore-keys:" not in source
    assert "DOWNLOAD_TIMERANGE: 20250801-20260501" in source
    assert "EXECUTION_TIMERANGE: 20260301-20260501" in source
    assert "--verify-data" in source
    assert "--materialize-config" in source
    assert "--cache none" in source


def test_workflow_uses_runner_temp_only_inside_shell_steps() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    runtime_config = "$RUNNER_TEMP/rl-v2-historical-training-execution.json"

    assert "RUN_CONFIG: ${{ runner.temp }}" not in source
    assert source.count(runtime_config) == 3


def test_workflow_exposes_repository_package_to_freqtrade_resolver() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    backtest_step = source.split(
        "- name: Run exactly one frozen historical training/backtest",
        maxsplit=1,
    )[1]
    pythonpath_export = 'export PYTHONPATH="$GITHUB_WORKSPACE"'

    assert source.count(pythonpath_export) == 1
    assert backtest_step.index(pythonpath_export) < backtest_step.index("freqtrade backtesting")


def test_workflow_runs_exactly_one_rl_v2_backtest_surface() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert source.count("freqtrade backtesting") == 1
    assert "DesiredPositionReinforcementLearner.py" in source
    assert "AiDesiredPositionRLResearchStrategy.py" in source
    assert "Expected exactly one Freqtrade backtest archive" in source
    assert "automatic_ranking" in source
    assert "automatic_promotion" in source
    assert "executed_freqtrade_commands" in source
