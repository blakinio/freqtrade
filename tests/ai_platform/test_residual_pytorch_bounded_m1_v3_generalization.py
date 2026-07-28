from __future__ import annotations

import json
from pathlib import Path

from ai_platform.scripts import residual_pytorch_bounded_m1_v3_generalization as v3
from ai_platform.scripts import residual_pytorch_bounded_m1_v3_run_request as request


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github/workflows/residual-pytorch-bounded-m1-v3-generalization.yml"


def _load(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def test_v3_contract_is_pair_only_generalization() -> None:
    contract = v3.load_contract()

    assert contract["market_data"]["pairs"] == ["SOL/USDT", "XRP/USDT"]
    assert contract["feature_target_contract"]["feature_parameters"][
        "include_corr_pairlist"
    ] == ["SOL/USDT", "XRP/USDT"]
    assert contract["geometry"]["development_stop_exclusive"] == "2026-05-01T00:00:00Z"
    assert contract["authorization"]["feature_changes_allowed"] is False
    assert contract["authorization"]["historical_oos_used"] is False
    assert contract["authorization"]["final_holdout_used"] is False
    assert contract["authorization"]["winner_selection_allowed"] is False
    assert contract["generalization"]["pair_cohort_only_change"] is True
    assert contract["generalization"]["expected_expanded_feature_count"] == 272
    assert (
        contract["generalization"]["source_role_normalized_feature_names_sha256"]
        == v3.SOURCE_ROLE_NORMALIZED_FEATURE_HASH
    )


def test_v3_model_parameters_and_non_pair_feature_geometry_match_v2() -> None:
    source = _load(
        "ai_platform/experimental_model_research/"
        "residual-pytorch-bounded-m1-execution-contract-v2.json"
    )
    target = v3.load_contract()

    source_features = dict(source["feature_target_contract"]["feature_parameters"])
    target_features = dict(target["feature_target_contract"]["feature_parameters"])
    source_features.pop("include_corr_pairlist")
    target_features.pop("include_corr_pairlist")
    assert target_features == source_features
    assert target["feature_target_contract"]["data_split_parameters"] == source[
        "feature_target_contract"
    ]["data_split_parameters"]
    assert target["feature_target_contract"]["entry_prediction_threshold"] == 0.006
    assert target["feature_target_contract"]["exit_prediction_threshold"] == -0.009

    source_parameters = {
        item["freqai_model"]: item["model_training_parameters"]
        for item in source["tracks"]
    }
    target_parameters = {
        item["freqai_model"]: item["model_training_parameters"]
        for item in target["tracks"]
    }
    assert target_parameters == source_parameters


def test_role_normalization_is_pair_symbol_independent() -> None:
    sol = {
        "pair": "SOL/USDT",
        "expanded_feature_names": [
            "%-rsi_SOL/USDT_15m",
            "%-rsi_XRP/USDT_15m",
            "%-day-of-week",
        ],
    }
    xrp = {
        "pair": "XRP/USDT",
        "expanded_feature_names": [
            "%-rsi_XRP/USDT_15m",
            "%-rsi_SOL/USDT_15m",
            "%-day-of-week",
        ],
    }
    assert v3._normalized_feature_identity(sol) == v3._normalized_feature_identity(xrp)


def test_canonical_request_binds_v3_inputs_without_request_presence() -> None:
    payload = request.canonical_run_request()

    assert payload["request_id"] == "residual-pytorch-bounded-m1-generalization-v3"
    assert payload["market_data"]["pairs"] == ["SOL/USDT", "XRP/USDT"]
    assert payload["authorization"]["historical_oos_used"] is False
    assert payload["authorization"]["final_holdout_used"] is False
    assert payload["generalization"]["source_run"] == 30340242201


def test_v3_workflow_is_exact_one_file_and_fail_closed() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    request_path = (
        "ai_platform/experimental_model_research/run-requests/"
        "residual-pytorch-bounded-m1-generalization-v3.json"
    )
    assert request_path in workflow
    assert "expected=$'A\\t" + request_path + "'" in workflow
    assert "SOL/USDT" in workflow
    assert "XRP/USDT" in workflow
    assert "BTC/USDT" not in workflow
    assert "ETH/USDT" not in workflow
    assert "--timerange 1754006400-1777593599" in workflow
    assert "validate-audit" in workflow
    assert "fail-on-cache-miss: true" in workflow
    assert "20260701" not in workflow
    assert "20260801-20260930" not in workflow
