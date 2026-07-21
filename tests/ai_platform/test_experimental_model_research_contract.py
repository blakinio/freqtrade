import json
from pathlib import Path

import pytest

from ai_platform.scripts.experimental_model_research_contract import (
    DEFAULT_FOUNDATION,
    ExperimentalModelResearchContractError,
    validate_experimental_model_research_foundation,
)
from ai_platform.scripts.protected_final_holdout import (
    protected_timerange,
    timeranges_overlap,
)
from ai_platform.scripts.run_experiment import load_manifest


ROOT = Path(__file__).resolve().parents[2]


def _foundation() -> dict:
    return json.loads(DEFAULT_FOUNDATION.read_text(encoding="utf-8"))


def _write_foundation(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "foundation.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_canonical_experimental_model_research_foundation_validates() -> None:
    foundation = validate_experimental_model_research_foundation()

    assert foundation["foundation_id"] == "experimental-model-research-foundation-v1"
    assert {track["status"] for track in foundation["tracks"]} == {"feasible"}
    assert foundation["phase6_isolation"]["membership"] is False
    assert foundation["protected_final_holdout"]["used"] is False


def test_research_tracks_are_distinct_and_guarded_from_final_holdout() -> None:
    foundation = validate_experimental_model_research_foundation()
    tracks = foundation["tracks"]

    assert len({track["freqai_identifier"] for track in tracks}) == 2
    assert len({track["artifact_root"] for track in tracks}) == 2
    assert len({track["manifest"] for track in tracks}) == 2
    assert len({track["config"] for track in tracks}) == 2

    for track in tracks:
        manifest = load_manifest(ROOT / track["manifest"])
        assert not timeranges_overlap(manifest["timerange"], protected_timerange())
        assert not timeranges_overlap(
            manifest["download_timerange"], protected_timerange()
        )


def test_research_tracks_pin_dependency_closed_heavy_runtime_profile() -> None:
    foundation = validate_experimental_model_research_foundation()

    assert {track["dependency_profile"] for track in foundation["tracks"]} == {
        "freqtrade[freqai,freqai_rl]"
    }


def test_foundation_rejects_phase6_membership(tmp_path: Path) -> None:
    foundation = _foundation()
    foundation["phase6_isolation"]["membership"] = True

    with pytest.raises(
        ExperimentalModelResearchContractError, match="must not join Phase 6"
    ):
        validate_experimental_model_research_foundation(
            _write_foundation(tmp_path, foundation)
        )


def test_foundation_rejects_shared_freqai_identifier(tmp_path: Path) -> None:
    foundation = _foundation()
    foundation["tracks"][1]["freqai_identifier"] = foundation["tracks"][0][
        "freqai_identifier"
    ]

    with pytest.raises(
        ExperimentalModelResearchContractError,
        match=r"RL seed drifted|identifier drifted",
    ):
        validate_experimental_model_research_foundation(
            _write_foundation(tmp_path, foundation)
        )


def test_foundation_rejects_rl_future_information_reward(tmp_path: Path) -> None:
    foundation = _foundation()
    foundation["tracks"][1]["reward_contract"]["future_market_information_used"] = True

    with pytest.raises(
        ExperimentalModelResearchContractError, match="future market data"
    ):
        validate_experimental_model_research_foundation(
            _write_foundation(tmp_path, foundation)
        )


def test_rl_reward_timing_is_pinned_to_decision_tick() -> None:
    foundation = validate_experimental_model_research_foundation()
    rl_track = next(
        track for track in foundation["tracks"] if track["track_id"] == "rl-research-v1"
    )

    assert rl_track["reward_contract"]["timing"] == "pre_transition_decision_tick"
    assert rl_track["reward_contract"]["future_market_information_used"] is False


def test_trading_metrics_are_required_and_training_loss_is_not_selection_evidence() -> (
    None
):
    foundation = validate_experimental_model_research_foundation()
    evaluation = foundation["evaluation_contract"]

    assert evaluation["metrics"] == ["profit", "drawdown", "trades", "stability"]
    assert evaluation["training_loss_is_selection_evidence"] is False
    assert evaluation["strict_oos_trade_filter_required"] is True


def test_pytorch_track_keeps_frozen_candidate_thresholds() -> None:
    foundation = validate_experimental_model_research_foundation()
    frozen = foundation["shared_trading_assumptions"]["frozen_candidate_reference"]

    assert frozen == {
        "entry_prediction_threshold": 0.006,
        "exit_prediction_threshold": -0.009,
    }
