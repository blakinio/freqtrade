from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from ai_platform.scripts.experimental_model_oos_result_extractor import (
    ExperimentalModelOosExtractorError,
    extract_experimental_oos_result,
    validate_experimental_oos_extraction,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTORCH_MANIFEST = REPO_ROOT / "ai_platform/experiments/pytorch-research-v1.json"
RL_MANIFEST = REPO_ROOT / "ai_platform/experiments/rl-research-v1.json"


def _trade(open_date: str, close_date: str, profit_abs: float, exit_reason: str = "exit_signal"):
    return {
        "open_date": open_date,
        "close_date": close_date,
        "profit_abs": profit_abs,
        "exit_reason": exit_reason,
    }


def _write_archive(
    path: Path,
    *,
    strategy: str,
    model: str,
    identifier: str,
    timerange: str = "20260301-20260701",
    trades: list[dict] | None = None,
) -> Path:
    stats = {
        "strategy": {
            strategy: {
                "strategy_name": strategy,
                "freqaimodel": model,
                "freqai_identifier": identifier,
                "timerange": timerange,
                "starting_balance": 10000.0,
                "trades": trades or [],
            }
        },
        "strategy_comparison": [],
    }
    with ZipFile(path, "w") as archive:
        archive.writestr("backtest-result-synthetic.json", json.dumps(stats))
    return path


def _pytorch_archive(tmp_path: Path, trades: list[dict] | None = None) -> Path:
    return _write_archive(
        tmp_path / "pytorch.zip",
        strategy="AiFrozenCandidateStrategy",
        model="SeededPyTorchMLPRegressor",
        identifier="ai-platform-pytorch-research-v1",
        trades=trades,
    )


def test_pytorch_extraction_scores_only_fully_contained_historical_oos_trades(
    tmp_path: Path,
) -> None:
    trades = [
        _trade("2026-04-30T23:45:00Z", "2026-05-01T00:15:00Z", 200.0),
        _trade("2026-05-01T00:00:00Z", "2026-05-02T00:00:00Z", 100.0),
        _trade("2026-06-10T00:00:00Z", "2026-06-11T00:00:00Z", -50.0),
        _trade("2026-06-30T23:00:00Z", "2026-07-01T00:00:00Z", 300.0),
        _trade("2026-06-20T00:00:00Z", "2026-06-21T00:00:00Z", 25.0, "force_exit"),
    ]
    result = extract_experimental_oos_result(
        _pytorch_archive(tmp_path, trades),
        PYTORCH_MANIFEST,
        drawdown_calculator=lambda included, starting_balance: 0.02,
    )

    assert result["track_id"] == "pytorch-research-v1"
    assert result["model_type"] == "SeededPyTorchMLPRegressor"
    assert result["freqai_identifier"] == "ai-platform-pytorch-research-v1"
    assert result["scoring_window"]["timerange"] == "20260501-20260630"
    assert result["counts"] == {
        "input_trades": 5,
        "included_trades": 3,
        "excluded_trades": 2,
        "excluded_pre_window_open_trades": 1,
        "excluded_post_window_close_trades": 1,
        "included_force_exit_trades": 1,
    }
    assert result["metrics"] == {
        "profit": pytest.approx(0.0075),
        "drawdown": pytest.approx(0.02),
        "trades": 3,
        "stability": pytest.approx(0.5),
    }
    assert result["stability_evidence"]["fold_trade_counts"] == {
        "2026-05": 1,
        "2026-06": 2,
    }
    assert result["stability_evidence"]["fold_profits"] == {
        "2026-05": pytest.approx(0.01),
        "2026-06": pytest.approx(-0.0025),
    }
    assert result["authorization"] == {
        "extraction_only": True,
        "phase6_member": False,
        "final_holdout_used": False,
        "retuning_allowed": False,
        "promotion_allowed": False,
        "profitability_claim_allowed": False,
    }
    validate_experimental_oos_extraction(result)


def test_rl_track_uses_its_distinct_freqai_identifier(tmp_path: Path) -> None:
    archive = _write_archive(
        tmp_path / "rl.zip",
        strategy="AiLongOnlyRLResearchStrategy",
        model="LongOnlyReinforcementLearner",
        identifier="ai-platform-rl-research-v1",
        trades=[_trade("2026-05-05T00:00:00Z", "2026-05-06T00:00:00Z", 10.0)],
    )

    result = extract_experimental_oos_result(
        archive,
        RL_MANIFEST,
        drawdown_calculator=lambda included, starting_balance: 0.0,
    )

    assert result["track_id"] == "rl-research-v1"
    assert result["model_type"] == "LongOnlyReinforcementLearner"
    assert result["freqai_identifier"] == "ai-platform-rl-research-v1"
    assert result["strategy"] == "AiLongOnlyRLResearchStrategy"
    assert result["metrics"]["trades"] == 1


def test_extractor_rejects_noncanonical_manifest_drift(tmp_path: Path) -> None:
    manifest = json.loads(PYTORCH_MANIFEST.read_text(encoding="utf-8"))
    manifest["fee"] = 0.001
    drifted_manifest = tmp_path / "drifted.json"
    drifted_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ExperimentalModelOosExtractorError, match="differs from the canonical"):
        extract_experimental_oos_result(
            _pytorch_archive(tmp_path),
            drifted_manifest,
            drawdown_calculator=lambda included, starting_balance: 0.0,
        )


def test_extractor_rejects_protected_final_holdout_manifest_before_archive_use(
    tmp_path: Path,
) -> None:
    manifest = json.loads(PYTORCH_MANIFEST.read_text(encoding="utf-8"))
    manifest["timerange"] = "20260801-20260930"
    holdout_manifest = tmp_path / "holdout.json"
    holdout_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ExperimentalModelOosExtractorError, match="protected final holdout"):
        extract_experimental_oos_result(
            tmp_path / "does-not-need-to-exist.zip",
            holdout_manifest,
            drawdown_calculator=lambda included, starting_balance: 0.0,
        )


def test_extractor_rejects_backtest_identity_drift(tmp_path: Path) -> None:
    archive = _write_archive(
        tmp_path / "wrong-identifier.zip",
        strategy="AiFrozenCandidateStrategy",
        model="SeededPyTorchMLPRegressor",
        identifier="phase6-or-other-identifier",
    )

    with pytest.raises(ExperimentalModelOosExtractorError, match="freqai_identifier"):
        extract_experimental_oos_result(
            archive,
            PYTORCH_MANIFEST,
            drawdown_calculator=lambda included, starting_balance: 0.0,
        )


def test_extractor_rejects_negative_drawdown(tmp_path: Path) -> None:
    with pytest.raises(ExperimentalModelOosExtractorError, match="finite non-negative"):
        extract_experimental_oos_result(
            _pytorch_archive(tmp_path),
            PYTORCH_MANIFEST,
            drawdown_calculator=lambda included, starting_balance: -0.01,
        )
