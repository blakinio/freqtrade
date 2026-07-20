import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from ai_platform.scripts.model_comparison_result_assembler import (
    ModelComparisonResultAssemblerError,
    assemble_model_comparison_result,
    validate_model_comparison_result,
    write_model_comparison_result,
)
from ai_platform.scripts.model_comparison_result_provenance import (
    EXPECTED_MODELS,
    build_canonical_materialization_plan,
    canonical_provenance_basis,
)
from ai_platform.scripts.model_comparison_selection_policy import evaluate_model_selection


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_bytes(_json_bytes(payload))


def _extraction(
    model_type: str,
    *,
    experiment_identity: str,
    profit: float,
    drawdown: float,
    stability: float,
) -> dict[str, Any]:
    trades = 10
    profitable_folds = 2 if stability == 1.0 else 1
    fold_profits = (
        {"2026-05": profit / 2, "2026-06": profit / 2}
        if stability == 1.0
        else {"2026-05": profit, "2026-06": 0.0}
    )
    return {
        "schema_version": 1,
        "extractor_id": "freqai-model-comparison-oos-extractor-v1",
        "metric_semantics_id": "freqai-model-comparison-metrics-v1",
        "oos_trade_boundary_id": "freqai-model-comparison-oos-trade-boundary-v1",
        "model_type": model_type,
        "experiment_identity": experiment_identity,
        "strategy": "AiPhase52ExitStrategy",
        "source": {
            "archive_sha256": "a" * 64,
            "stats_member": f"{model_type}.json",
        },
        "scoring_window": {
            "timerange": "20260501-20260630",
            "start_inclusive": "2026-05-01T00:00:00Z",
            "end_exclusive": "2026-07-01T00:00:00Z",
            "timezone": "UTC",
            "source_status": "consumed_historical_oos",
        },
        "starting_balance": 1000.0,
        "counts": {
            "input_trades": trades,
            "included_trades": trades,
            "excluded_trades": 0,
            "excluded_pre_window_open_trades": 0,
            "excluded_post_window_close_trades": 0,
            "included_force_exit_trades": 0,
        },
        "metrics": {
            "profit": profit,
            "drawdown": drawdown,
            "trades": trades,
            "stability": stability,
        },
        "stability_evidence": {
            "evaluated_folds": 2,
            "profitable_folds": profitable_folds,
            "fold_trade_counts": {"2026-05": 5, "2026-06": 5},
            "fold_profits": fold_profits,
        },
        "included_trade_evidence": [
            {
                "source_index": index,
                "open_date": "2026-05-01T00:00:00Z",
                "close_date": "2026-05-02T00:00:00Z",
                "profit_abs": 0.0,
                "exit_reason": "roi",
            }
            for index in range(trades)
        ],
        "excluded_trade_evidence": [],
        "authorization": {
            "final_holdout_used": False,
            "retuning_allowed": False,
            "promotion_allowed": False,
            "profitability_claim_allowed": False,
        },
    }


def _artifact_set(
    tmp_path: Path,
) -> tuple[Path, dict[str, Path], Path, dict[str, Any]]:
    basis = canonical_provenance_basis()
    plan = build_canonical_materialization_plan()
    plan_by_model = {model["model_type"]: model for model in plan["models"]}

    extraction_paths: dict[str, Path] = {}
    extractions: list[dict[str, Any]] = []
    model_sources: list[dict[str, Any]] = []
    execution_commit = "c" * 40
    strategy_sha256 = "d" * 64

    for index, model_type in enumerate(EXPECTED_MODELS):
        plan_model = plan_by_model[model_type]
        extraction = _extraction(
            model_type,
            experiment_identity=plan_model["experiment_identity"],
            profit=0.08 if index == 0 else 0.10,
            drawdown=0.12 if index == 0 else 0.10,
            stability=0.5 if index == 0 else 1.0,
        )
        extraction_path = tmp_path / f"{model_type}-oos-extraction.json"
        _write_json(extraction_path, extraction)
        extraction_paths[model_type] = extraction_path
        extractions.append(extraction)

        model_sources.append(
            {
                "model_type": model_type,
                "experiment_identity": plan_model["experiment_identity"],
                "materialized_manifest_sha256": plan_model["manifest_sha256"],
                "materialized_config_sha256": plan_model["config_sha256"],
                "run_provenance_sha256": f"{index + 1}" * 64,
                "run_provenance": {
                    "stage": "backtest",
                    "git_commit": execution_commit,
                    "manifest_sha256": plan_model["manifest_sha256"],
                    "config_sha256": plan_model["config_sha256"],
                    "strategy_sha256": strategy_sha256,
                },
                "backtest_archive_sha256": f"{index + 3}" * 64,
                "extraction_sha256": _sha256(extraction_path.read_bytes()),
            }
        )

    decision = evaluate_model_selection(extractions)
    decision_path = tmp_path / "selection-decision.json"
    _write_json(decision_path, decision)

    provenance = {
        "schema_version": 1,
        "provenance_contract_id": "freqai-model-comparison-result-provenance-v1",
        "comparison_id": basis["comparison_id"],
        "materialization_plan_sha256": basis["materialization_plan_sha256"],
        "execution_git_commit": execution_commit,
        "selection_policy_sha256": basis["selection_policy_sha256"],
        "selection_decision_sha256": _sha256(decision_path.read_bytes()),
        "model_sources": model_sources,
    }
    provenance_path = tmp_path / "result-provenance.json"
    _write_json(provenance_path, provenance)
    return provenance_path, extraction_paths, decision_path, provenance


def test_assembler_emits_schema_valid_completed_result_from_bound_evidence(
    tmp_path: Path,
) -> None:
    provenance_path, extraction_paths, decision_path, provenance = _artifact_set(tmp_path)

    result = assemble_model_comparison_result(
        provenance_path,
        extraction_paths=extraction_paths,
        selection_decision_path=decision_path,
    )

    assert validate_model_comparison_result(result) == result
    assert result["status"] == "completed"
    assert result["git_commit"] == provenance["execution_git_commit"]
    assert result["plan_sha256"] == provenance["materialization_plan_sha256"]
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert result["selection"] == decision["selection"]
    assert result["selection"]["selected_model"] == "XGBoostRegressor"
    assert result["selection"]["final_holdout_used"] is False
    assert result["selection"]["promotion_allowed"] is False
    assert result["selection"]["profitability_claim_allowed"] is False

    for model_result in result["model_results"]:
        model_type = model_result["model_type"]
        extraction = json.loads(extraction_paths[model_type].read_text(encoding="utf-8"))
        assert model_result["experiment_identity"] == extraction["experiment_identity"]
        assert model_result["metrics"] == extraction["metrics"]
        assert model_result["artifact_paths"] == [extraction_paths[model_type].as_posix()]

    output = tmp_path / "comparison-result.json"
    write_model_comparison_result(output, result)
    assert json.loads(output.read_text(encoding="utf-8")) == result


def test_assembler_rejects_extraction_bytes_not_bound_by_provenance(
    tmp_path: Path,
) -> None:
    provenance_path, extraction_paths, decision_path, _ = _artifact_set(tmp_path)
    extraction_path = extraction_paths["LightGBMRegressor"]
    extraction = json.loads(extraction_path.read_text(encoding="utf-8"))
    extraction["metrics"]["profit"] = 0.09
    _write_json(extraction_path, extraction)

    with pytest.raises(ModelComparisonResultAssemblerError, match="exact-byte hash"):
        assemble_model_comparison_result(
            provenance_path,
            extraction_paths=extraction_paths,
            selection_decision_path=decision_path,
        )


def test_assembler_rejects_selection_decision_bytes_not_bound_by_provenance(
    tmp_path: Path,
) -> None:
    provenance_path, extraction_paths, decision_path, _ = _artifact_set(tmp_path)
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    decision["selection"]["basis"] = "eligible_models_inconclusive_no_strict_pareto_dominance"
    _write_json(decision_path, decision)

    with pytest.raises(
        ModelComparisonResultAssemblerError,
        match="Selection decision exact-byte hash",
    ):
        assemble_model_comparison_result(
            provenance_path,
            extraction_paths=extraction_paths,
            selection_decision_path=decision_path,
        )


def test_assembler_rejects_bound_but_semantically_unrelated_selection_decision(
    tmp_path: Path,
) -> None:
    provenance_path, extraction_paths, decision_path, provenance = _artifact_set(tmp_path)
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    decision["selection"]["selected_model"] = "LightGBMRegressor"
    _write_json(decision_path, decision)

    provenance["selection_decision_sha256"] = _sha256(decision_path.read_bytes())
    _write_json(provenance_path, provenance)

    with pytest.raises(ModelComparisonResultAssemblerError, match="recomputed from bound"):
        assemble_model_comparison_result(
            provenance_path,
            extraction_paths=extraction_paths,
            selection_decision_path=decision_path,
        )


def test_assembler_requires_exactly_one_extraction_path_per_canonical_model(
    tmp_path: Path,
) -> None:
    provenance_path, extraction_paths, decision_path, _ = _artifact_set(tmp_path)
    extraction_paths.pop("XGBoostRegressor")

    with pytest.raises(ModelComparisonResultAssemblerError, match="exactly one extraction path"):
        assemble_model_comparison_result(
            provenance_path,
            extraction_paths=extraction_paths,
            selection_decision_path=decision_path,
        )
