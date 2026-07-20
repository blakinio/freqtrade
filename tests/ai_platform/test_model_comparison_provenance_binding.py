import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from ai_platform.scripts.model_comparison_provenance_binding import (
    ModelArtifactFiles,
    ModelComparisonProvenanceBindingError,
    bind_model_comparison_provenance,
    write_bound_provenance,
)
from ai_platform.scripts.model_comparison_result_provenance import (
    EXPECTED_MODELS,
    build_canonical_materialization_plan,
    canonical_provenance_basis,
    validate_model_comparison_result_provenance,
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
    archive_sha256: str,
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
            "archive_sha256": archive_sha256,
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


def _artifact_set(tmp_path: Path) -> tuple[Path, dict[str, ModelArtifactFiles], Path]:
    basis = canonical_provenance_basis()
    plan = build_canonical_materialization_plan()
    plan_path = tmp_path / "materialization.json"
    _write_json(plan_path, plan)

    plan_by_model = {model["model_type"]: model for model in plan["models"]}
    execution_commit = "c" * 40
    strategy_sha256 = "d" * 64
    model_artifacts: dict[str, ModelArtifactFiles] = {}
    extractions: list[dict[str, Any]] = []

    for index, model_type in enumerate(EXPECTED_MODELS):
        model_dir = tmp_path / model_type
        model_dir.mkdir()
        plan_model = plan_by_model[model_type]

        run_provenance_path = model_dir / "provenance.json"
        _write_json(
            run_provenance_path,
            {
                "schema_version": 1,
                "experiment_id": plan_model["experiment_identity"],
                "run_id": f"synthetic-{index}",
                "git_commit": execution_commit,
                "manifest_sha256": plan_model["manifest_sha256"],
                "config_sha256": plan_model["config_sha256"],
                "strategy_sha256": strategy_sha256,
                "stage": "backtest",
            },
        )

        backtest_path = model_dir / "backtest-result-synthetic.zip"
        backtest_bytes = f"synthetic-backtest-{model_type}".encode()
        backtest_path.write_bytes(backtest_bytes)

        extraction = _extraction(
            model_type,
            experiment_identity=plan_model["experiment_identity"],
            archive_sha256=_sha256(backtest_bytes),
            profit=0.08 if index == 0 else 0.10,
            drawdown=0.12 if index == 0 else 0.10,
            stability=0.5 if index == 0 else 1.0,
        )
        extraction_path = model_dir / "oos-extraction.json"
        _write_json(extraction_path, extraction)
        extractions.append(extraction)

        model_artifacts[model_type] = ModelArtifactFiles(
            run_provenance=run_provenance_path,
            backtest_archive=backtest_path,
            extraction=extraction_path,
        )

    decision_path = tmp_path / "selection-decision.json"
    _write_json(decision_path, evaluate_model_selection(extractions))
    assert basis["materialization_plan_sha256"] == _sha256(plan_path.read_bytes())
    return plan_path, model_artifacts, decision_path


def test_binding_verifies_actual_artifact_hashes_and_emits_valid_evidence(tmp_path: Path) -> None:
    plan_path, model_artifacts, decision_path = _artifact_set(tmp_path)

    evidence = bind_model_comparison_provenance(
        plan_path,
        model_artifacts=model_artifacts,
        selection_decision_path=decision_path,
    )

    assert validate_model_comparison_result_provenance(evidence) == evidence
    assert evidence["materialization_plan_sha256"] == _sha256(plan_path.read_bytes())
    assert evidence["selection_decision_sha256"] == _sha256(decision_path.read_bytes())
    for source in evidence["model_sources"]:
        artifacts = model_artifacts[source["model_type"]]
        assert source["run_provenance_sha256"] == _sha256(artifacts.run_provenance.read_bytes())
        assert source["backtest_archive_sha256"] == _sha256(artifacts.backtest_archive.read_bytes())
        assert source["extraction_sha256"] == _sha256(artifacts.extraction.read_bytes())

    output = tmp_path / "bound-provenance.json"
    write_bound_provenance(output, evidence)
    assert json.loads(output.read_text(encoding="utf-8")) == evidence


def test_binding_rejects_noncanonical_materialization_bytes(tmp_path: Path) -> None:
    plan_path, model_artifacts, decision_path = _artifact_set(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(ModelComparisonProvenanceBindingError, match="Materialization plan bytes"):
        bind_model_comparison_provenance(
            plan_path,
            model_artifacts=model_artifacts,
            selection_decision_path=decision_path,
        )


def test_binding_rejects_run_provenance_manifest_hash_drift(tmp_path: Path) -> None:
    plan_path, model_artifacts, decision_path = _artifact_set(tmp_path)
    run_path = model_artifacts["XGBoostRegressor"].run_provenance
    run_provenance = json.loads(run_path.read_text(encoding="utf-8"))
    run_provenance["manifest_sha256"] = "0" * 64
    _write_json(run_path, run_provenance)

    with pytest.raises(ModelComparisonProvenanceBindingError, match="Run manifest hash"):
        bind_model_comparison_provenance(
            plan_path,
            model_artifacts=model_artifacts,
            selection_decision_path=decision_path,
        )


def test_binding_rejects_extraction_archive_hash_mismatch(tmp_path: Path) -> None:
    plan_path, model_artifacts, decision_path = _artifact_set(tmp_path)
    model_artifacts["LightGBMRegressor"].backtest_archive.write_bytes(b"tampered-backtest")

    with pytest.raises(ModelComparisonProvenanceBindingError, match="archive hash"):
        bind_model_comparison_provenance(
            plan_path,
            model_artifacts=model_artifacts,
            selection_decision_path=decision_path,
        )


def test_binding_rejects_selection_decision_not_derived_from_bound_extractions(
    tmp_path: Path,
) -> None:
    plan_path, model_artifacts, decision_path = _artifact_set(tmp_path)
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    decision["selection"]["selected_model"] = "LightGBMRegressor"
    _write_json(decision_path, decision)

    with pytest.raises(ModelComparisonProvenanceBindingError, match="recomputed from bound"):
        bind_model_comparison_provenance(
            plan_path,
            model_artifacts=model_artifacts,
            selection_decision_path=decision_path,
        )


def test_binding_rejects_extraction_experiment_identity_drift(tmp_path: Path) -> None:
    plan_path, model_artifacts, decision_path = _artifact_set(tmp_path)
    extraction_path = model_artifacts["XGBoostRegressor"].extraction
    extraction = json.loads(extraction_path.read_text(encoding="utf-8"))
    extraction["experiment_identity"] = "drifted-experiment"
    _write_json(extraction_path, extraction)

    with pytest.raises(ModelComparisonProvenanceBindingError, match="experiment identity drifted"):
        bind_model_comparison_provenance(
            plan_path,
            model_artifacts=model_artifacts,
            selection_decision_path=decision_path,
        )
