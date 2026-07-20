import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ai_platform.scripts.model_comparison_contract import (
    ModelComparisonContractError,
    load_model_comparison_contract,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "ai_platform" / "model_comparison" / "lightgbm-vs-xgboost-v1.json"
SCHEMA_PATH = ROOT / "ai_platform" / "model_comparison" / "schema-v1.json"
RESULT_SCHEMA_PATH = ROOT / "ai_platform" / "model_comparison" / "result-schema-v1.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _write_contract(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "comparison.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_model_comparison_contract_matches_schema() -> None:
    contract = _contract()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(contract)


def test_model_comparison_contract_pins_fair_first_comparison() -> None:
    contract = load_model_comparison_contract(CONTRACT_PATH)

    assert contract["models"] == ["LightGBMRegressor", "XGBoostRegressor"]
    assert contract["variable_under_test"] == "freqai_model"
    assert contract["shared_experiment"]["feature_set_id"] == (
        "baseline-price-trend-momentum-volume-v1"
    )
    assert contract["shared_experiment"]["target_id"] == "future-average-return-v1"
    assert contract["shared_experiment"]["pairs"] == ["BTC/USDT", "ETH/USDT"]
    assert contract["shared_experiment"]["timeframes"] == ["15m", "1h", "4h"]
    assert contract["shared_experiment"]["fee"] == 0.002
    assert contract["selection_policy"]["final_holdout_metrics_allowed"] is False
    assert contract["selection_policy"]["promotion_allowed"] is False


def test_model_comparison_rejects_protected_holdout_in_training(tmp_path: Path) -> None:
    contract = _contract()
    contract["shared_experiment"]["training_window"] = "20260815-20260915"

    with pytest.raises(ModelComparisonContractError, match="overlaps protected final holdout"):
        load_model_comparison_contract(_write_contract(tmp_path, contract))


def test_model_comparison_rejects_protected_holdout_in_historical_oos(tmp_path: Path) -> None:
    contract = _contract()
    contract["shared_experiment"]["historical_oos_windows"][0]["timerange"] = "20260901-20261031"

    with pytest.raises(ModelComparisonContractError, match="overlaps protected final holdout"):
        load_model_comparison_contract(_write_contract(tmp_path, contract))


def test_model_comparison_rejects_model_set_drift(tmp_path: Path) -> None:
    contract = _contract()
    contract["models"] = ["LightGBMRegressor", "PyTorchMLPRegressor"]

    with pytest.raises(ModelComparisonContractError, match="LightGBMRegressor vs XGBoostRegressor"):
        load_model_comparison_contract(_write_contract(tmp_path, contract))


def test_model_comparison_rejects_frozen_threshold_drift(tmp_path: Path) -> None:
    contract = _contract()
    contract["shared_experiment"]["risk_assumptions"]["exit_prediction_threshold"] = -0.008

    with pytest.raises(ModelComparisonContractError, match="drifted from the frozen candidate"):
        load_model_comparison_contract(_write_contract(tmp_path, contract))


def test_result_contract_forbids_final_holdout_promotion_and_profitability_claims() -> None:
    schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    result: dict[str, Any] = {
        "schema_version": 1,
        "comparison_id": "freqai-lightgbm-vs-xgboost-v1",
        "status": "completed",
        "git_commit": "a" * 40,
        "plan_sha256": "b" * 64,
        "model_results": [
            {
                "model_type": "LightGBMRegressor",
                "experiment_identity": "exp-lightgbm",
                "metrics": {
                    "profit": 0.01,
                    "drawdown": 0.10,
                    "trades": 20,
                    "stability": 0.5,
                },
                "artifact_paths": ["ai_platform/artifacts/model-comparison/lightgbm.json"],
            },
            {
                "model_type": "XGBoostRegressor",
                "experiment_identity": "exp-xgboost",
                "metrics": {
                    "profit": 0.02,
                    "drawdown": 0.11,
                    "trades": 21,
                    "stability": 0.6,
                },
                "artifact_paths": ["ai_platform/artifacts/model-comparison/xgboost.json"],
            },
        ],
        "selection": {
            "selected_model": "XGBoostRegressor",
            "basis": "historical OOS comparison only",
            "final_holdout_used": False,
            "promotion_allowed": False,
            "profitability_claim_allowed": False,
        },
    }

    Draft202012Validator(schema).validate(result)

    contaminated = copy.deepcopy(result)
    contaminated["selection"]["final_holdout_used"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(contaminated)
