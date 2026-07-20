import copy
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from jsonschema import Draft202012Validator

from ai_platform.scripts.model_comparison_harness import build_materialization
from ai_platform.scripts.model_comparison_oos_result_extractor import (
    CANONICAL_MATERIALIZATION_ROOT,
    DEFAULT_COMPARISON_CONTRACT,
    ModelComparisonOosExtractorError,
    extract_oos_result,
)


ROOT = Path(__file__).resolve().parents[2]
EXTRACTION_SCHEMA_PATH = ROOT / "ai_platform/model_comparison/oos-extraction-schema-v1.json"


def _canonical_manifest(model_type: str = "LightGBMRegressor") -> dict:
    materialization = build_materialization(
        DEFAULT_COMPARISON_CONTRACT,
        output_root=CANONICAL_MATERIALIZATION_ROOT,
    )
    for model in materialization["models"]:
        if model["model_type"] == model_type:
            return copy.deepcopy(model["manifest"])
    raise AssertionError(f"Missing model in materialization: {model_type}")


def _write_manifest(tmp_path: Path, manifest: dict) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _strategy_result(
    manifest: dict,
    trades: list[dict],
    *,
    starting_balance: float = 1000.0,
) -> dict:
    return {
        "strategy_name": manifest["strategy"],
        "freqaimodel": manifest["freqai_model"],
        "freqai_identifier": manifest["experiment_id"],
        "timerange": manifest["timerange"],
        "starting_balance": starting_balance,
        "trades": trades,
    }


def _write_archive(
    tmp_path: Path,
    manifest: dict,
    trades: list[dict],
    *,
    strategy_result: dict | None = None,
    extra_stats_member: bool = False,
) -> Path:
    archive_path = tmp_path / "backtest-result-synthetic.zip"
    result = strategy_result or _strategy_result(manifest, trades)
    stats = {
        "strategy": {manifest["strategy"]: result},
        "strategy_comparison": [],
    }
    with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("backtest-result-synthetic.json", json.dumps(stats))
        archive.writestr(
            "backtest-result-synthetic_config.json",
            json.dumps({"dry_run": True}),
        )
        if extra_stats_member:
            archive.writestr("backtest-result-duplicate.json", json.dumps(stats))
    return archive_path


def _trade(
    open_date: str,
    close_date: str,
    profit_abs: float,
    exit_reason: str = "roi",
) -> dict:
    return {
        "open_date": open_date,
        "close_date": close_date,
        "profit_abs": profit_abs,
        "exit_reason": exit_reason,
    }


def test_extractor_applies_strict_oos_boundary_and_metric_evidence(
    tmp_path: Path,
) -> None:
    manifest = _canonical_manifest()
    manifest_path = _write_manifest(tmp_path, manifest)
    trades = [
        _trade("2026-04-30T23:00:00Z", "2026-05-02T00:00:00Z", 10.0),
        _trade("2026-05-02T00:00:00Z", "2026-05-03T00:00:00Z", 20.0),
        _trade(
            "2026-05-15T00:00:00Z",
            "2026-05-16T00:00:00Z",
            10.0,
            "force_exit",
        ),
        _trade("2026-06-02T00:00:00Z", "2026-06-03T00:00:00Z", -5.0),
        _trade("2026-06-30T23:00:00Z", "2026-07-01T00:00:00Z", 40.0),
        _trade("2026-04-30T00:00:00Z", "2026-07-02T00:00:00Z", 50.0),
    ]
    archive_path = _write_archive(tmp_path, manifest, trades)

    result = extract_oos_result(
        archive_path,
        manifest_path,
        drawdown_calculator=lambda included, balance: 0.0125,
    )

    assert result["counts"] == {
        "input_trades": 6,
        "included_trades": 3,
        "excluded_trades": 3,
        "excluded_pre_window_open_trades": 2,
        "excluded_post_window_close_trades": 2,
        "included_force_exit_trades": 1,
    }
    assert result["metrics"] == {
        "profit": 0.025,
        "drawdown": 0.0125,
        "trades": 3,
        "stability": 0.5,
    }
    assert result["stability_evidence"] == {
        "evaluated_folds": 2,
        "profitable_folds": 1,
        "fold_trade_counts": {"2026-05": 2, "2026-06": 1},
        "fold_profits": {"2026-05": 0.03, "2026-06": -0.005},
    }
    assert result["included_trade_evidence"][0]["open_date"] == "2026-05-02T00:00:00Z"
    assert result["excluded_trade_evidence"][0]["exclusion_reasons"] == ["pre_window_open"]
    assert result["excluded_trade_evidence"][2]["exclusion_reasons"] == [
        "pre_window_open",
        "post_window_close",
    ]
    assert result["authorization"] == {
        "final_holdout_used": False,
        "retuning_allowed": False,
        "promotion_allowed": False,
        "profitability_claim_allowed": False,
    }

    schema = json.loads(EXTRACTION_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(result)


def test_extractor_includes_exact_start_and_excludes_exact_end(tmp_path: Path) -> None:
    manifest = _canonical_manifest()
    manifest_path = _write_manifest(tmp_path, manifest)
    trades = [
        _trade("2026-05-01T00:00:00Z", "2026-05-01T00:00:00Z", 1.0),
        _trade("2026-06-30T23:00:00Z", "2026-07-01T00:00:00Z", 1.0),
    ]
    archive_path = _write_archive(tmp_path, manifest, trades)

    result = extract_oos_result(
        archive_path,
        manifest_path,
        drawdown_calculator=lambda included, balance: 0.0,
    )

    assert result["counts"]["included_trades"] == 1
    assert result["counts"]["excluded_post_window_close_trades"] == 1


def test_extractor_rejects_noncanonical_manifest_identity_even_if_archive_matches(
    tmp_path: Path,
) -> None:
    manifest = _canonical_manifest()
    manifest["experiment_id"] = "freqai-lightgbm-vs-xgboost-v1-lightgbm-drifted"
    manifest_path = _write_manifest(tmp_path, manifest)
    archive_path = _write_archive(tmp_path, manifest, [])

    with pytest.raises(ModelComparisonOosExtractorError, match="experiment_id"):
        extract_oos_result(
            archive_path,
            manifest_path,
            drawdown_calculator=lambda trades, balance: 0.0,
        )


def test_extractor_rejects_archive_model_identity_drift(tmp_path: Path) -> None:
    manifest = _canonical_manifest()
    manifest_path = _write_manifest(tmp_path, manifest)
    strategy_result = _strategy_result(manifest, [])
    strategy_result["freqaimodel"] = "XGBoostRegressor"
    archive_path = _write_archive(
        tmp_path,
        manifest,
        [],
        strategy_result=strategy_result,
    )

    with pytest.raises(ModelComparisonOosExtractorError, match="freqaimodel"):
        extract_oos_result(
            archive_path,
            manifest_path,
            drawdown_calculator=lambda trades, balance: 0.0,
        )


def test_extractor_rejects_ambiguous_stats_members(tmp_path: Path) -> None:
    manifest = _canonical_manifest()
    manifest_path = _write_manifest(tmp_path, manifest)
    archive_path = _write_archive(tmp_path, manifest, [], extra_stats_member=True)

    with pytest.raises(
        ModelComparisonOosExtractorError,
        match="exactly one JSON stats member",
    ):
        extract_oos_result(
            archive_path,
            manifest_path,
            drawdown_calculator=lambda trades, balance: 0.0,
        )


def test_extractor_fails_closed_on_naive_trade_timestamp(tmp_path: Path) -> None:
    manifest = _canonical_manifest()
    manifest_path = _write_manifest(tmp_path, manifest)
    trades = [_trade("2026-05-01 00:00:00", "2026-05-02T00:00:00Z", 1.0)]
    archive_path = _write_archive(tmp_path, manifest, trades)

    with pytest.raises(ModelComparisonOosExtractorError, match="explicit timezone"):
        extract_oos_result(
            archive_path,
            manifest_path,
            drawdown_calculator=lambda trades, balance: 0.0,
        )


def test_extractor_empty_oos_emits_zero_metrics_without_selection_claim(
    tmp_path: Path,
) -> None:
    manifest = _canonical_manifest("XGBoostRegressor")
    manifest_path = _write_manifest(tmp_path, manifest)
    archive_path = _write_archive(tmp_path, manifest, [])

    result = extract_oos_result(
        archive_path,
        manifest_path,
        drawdown_calculator=lambda included, balance: 0.0,
    )

    assert result["metrics"] == {
        "profit": 0.0,
        "drawdown": 0.0,
        "trades": 0,
        "stability": 0.0,
    }
    assert result["counts"]["input_trades"] == 0
    assert "selection" not in result


def test_extractor_default_drawdown_matches_freqtrade_implementation_when_available(
    tmp_path: Path,
) -> None:
    pytest.importorskip("pandas")
    manifest = _canonical_manifest()
    manifest_path = _write_manifest(tmp_path, manifest)
    trades = [
        _trade("2026-05-01T00:00:00Z", "2026-05-02T00:00:00Z", 100.0),
        _trade("2026-05-03T00:00:00Z", "2026-05-04T00:00:00Z", -50.0),
        _trade("2026-05-05T00:00:00Z", "2026-05-06T00:00:00Z", -25.0),
    ]
    archive_path = _write_archive(tmp_path, manifest, trades)

    result = extract_oos_result(archive_path, manifest_path)

    assert result["metrics"]["drawdown"] == pytest.approx(75.0 / 1100.0)
