import copy
import json
from pathlib import Path

import pytest

from ai_platform.scripts import model_comparison_harness as harness
from ai_platform.scripts.run_experiment import ExperimentError, load_manifest


OUTPUT_ROOT = "ai_platform/artifacts/model-comparison/materialized"
PROTECTED_FINAL_HOLDOUT = "20260801-20260930"


def _materialization() -> dict:
    return harness.build_materialization(harness.DEFAULT_CONTRACT, output_root=OUTPUT_ROOT)


def test_harness_materializes_exactly_two_models_without_execution() -> None:
    materialization = _materialization()

    assert materialization["status"] == "materialized_only"
    assert materialization["execution_performed"] is False
    assert materialization["final_holdout_used"] is False
    assert materialization["promotion_allowed"] is False
    assert materialization["profitability_claim_allowed"] is False
    assert [model["model_type"] for model in materialization["models"]] == [
        "LightGBMRegressor",
        "XGBoostRegressor",
    ]


def test_harness_pins_model_specific_training_parameters() -> None:
    materialization = _materialization()
    by_model = {model["model_type"]: model for model in materialization["models"]}

    lightgbm_parameters = by_model["LightGBMRegressor"]["config"]["freqai"][
        "model_training_parameters"
    ]
    xgboost_parameters = by_model["XGBoostRegressor"]["config"]["freqai"][
        "model_training_parameters"
    ]

    assert lightgbm_parameters == {
        "n_estimators": 400,
        "learning_rate": 0.03,
        "num_leaves": 31,
        "n_jobs": -1,
    }
    assert xgboost_parameters == {
        "n_estimators": 400,
        "learning_rate": 0.03,
        "n_jobs": -1,
    }
    assert "num_leaves" not in xgboost_parameters


def test_harness_freezes_single_training_window_before_tuning_and_oos() -> None:
    materialization = _materialization()

    assert materialization["training_mode"] == "single_frozen_training_window"
    assert materialization["backtest_retraining_allowed"] is False
    assert materialization["training_window"] == "20251201-20260228"
    assert materialization["tuning_window"] == "20260301-20260430"
    assert materialization["scoring_window"] == "20260501-20260630"
    assert materialization["prediction_window"] == "20260301-20260630"
    assert materialization["train_period_days"] == 90
    assert materialization["backtest_period_days"] == 122

    for model in materialization["models"]:
        freqai = model["config"]["freqai"]
        assert freqai["train_period_days"] == 90
        assert freqai["backtest_period_days"] == 122
        assert model["manifest"]["timerange"] == "20260301-20260630"


def test_harness_configs_differ_only_by_identifier_and_model_parameters() -> None:
    materialization = _materialization()
    configs = [copy.deepcopy(model["config"]) for model in materialization["models"]]

    for config in configs:
        config["freqai"].pop("identifier")
        config["freqai"].pop("model_training_parameters")

    assert configs[0] == configs[1]


def test_harness_manifests_share_prediction_and_historical_scoring_assumptions() -> None:
    materialization = _materialization()
    manifests = [copy.deepcopy(model["manifest"]) for model in materialization["models"]]

    assert materialization["scoring_window"] == "20260501-20260630"
    for manifest in manifests:
        assert manifest["timerange"] == "20260301-20260630"
        assert manifest["download_timerange"] == "20250801-20260630"
        for model_specific_field in (
            "experiment_id",
            "config",
            "freqai_model",
            "output_root",
            "description",
        ):
            manifest.pop(model_specific_field)

    assert manifests[0] == manifests[1]


def test_harness_materialization_is_deterministic() -> None:
    first = _materialization()
    second = _materialization()

    assert first == second
    assert first["models"][0]["experiment_identity"] != first["models"][1]["experiment_identity"]


def test_materialized_manifests_pass_central_holdout_guard(tmp_path: Path) -> None:
    materialization = _materialization()

    for index, model in enumerate(materialization["models"]):
        manifest_path = tmp_path / f"manifest-{index}.json"
        manifest_path.write_text(json.dumps(model["manifest"]), encoding="utf-8")
        loaded = load_manifest(manifest_path)
        assert loaded["timerange"] == "20260301-20260630"
        assert loaded["download_timerange"] == "20250801-20260630"


def test_central_guard_rejects_protected_window_in_materialized_manifest(
    tmp_path: Path,
) -> None:
    materialization = _materialization()
    manifest = copy.deepcopy(materialization["models"][0]["manifest"])
    manifest["timerange"] = PROTECTED_FINAL_HOLDOUT
    manifest_path = tmp_path / "contaminated-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ExperimentError, match="overlaps protected final holdout"):
        load_manifest(manifest_path)


def test_harness_requires_single_consumed_historical_window(monkeypatch) -> None:
    original_loader = harness.load_model_comparison_contract

    def load_with_extra_window(path: Path) -> dict:
        contract = copy.deepcopy(original_loader(path))
        contract["shared_experiment"]["historical_oos_windows"].append(
            {
                "name": "extra-consumed-window",
                "timerange": "20260701-20260731",
                "unseen_status": "consumed_historical_oos",
            }
        )
        return contract

    monkeypatch.setattr(harness, "load_model_comparison_contract", load_with_extra_window)

    with pytest.raises(
        harness.ModelComparisonHarnessError,
        match="exactly one consumed historical OOS",
    ):
        harness.build_materialization(harness.DEFAULT_CONTRACT, output_root=OUTPUT_ROOT)


def test_harness_rejects_non_contiguous_training_and_tuning(monkeypatch) -> None:
    original_loader = harness.load_model_comparison_contract

    def load_with_gap(path: Path) -> dict:
        contract = copy.deepcopy(original_loader(path))
        contract["shared_experiment"]["tuning_window"] = "20260302-20260430"
        return contract

    monkeypatch.setattr(harness, "load_model_comparison_contract", load_with_gap)

    with pytest.raises(
        harness.ModelComparisonHarnessError,
        match="Training and tuning windows must be contiguous",
    ):
        harness.build_materialization(harness.DEFAULT_CONTRACT, output_root=OUTPUT_ROOT)
