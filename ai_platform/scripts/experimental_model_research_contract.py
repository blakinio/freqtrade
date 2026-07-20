#!/usr/bin/env python3
"""Validate isolated PyTorch and RL research-foundation contracts without executing research."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

from ai_platform.scripts.protected_final_holdout import protected_timerange
from ai_platform.scripts.run_experiment import load_manifest, validate_research_config


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FOUNDATION = REPO_ROOT / "ai_platform/experimental_model_research/foundation-v1.json"
EXPECTED_TRACKS = {"pytorch-research-v1", "rl-research-v1"}
EXPECTED_METRICS = ["profit", "drawdown", "trades", "stability"]
EXPECTED_GEOMETRY = {
    "training_window": "20251201-20260228",
    "tuning_window": "20260301-20260430",
    "historical_oos_window": "20260501-20260630",
    "prediction_window": "20260301-20260630",
    "download_timerange": "20250801-20260630",
    "train_period_days": 90,
    "backtest_period_days": 122,
}


class ExperimentalModelResearchContractError(RuntimeError):
    """Raised when the isolated experimental-model research foundation drifts."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentalModelResearchContractError(
            f"Unable to read {label} {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ExperimentalModelResearchContractError(f"{label} must contain a JSON object")
    return payload


def _repo_path(value: str, label: str) -> Path:
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ExperimentalModelResearchContractError(
            f"{label} must stay inside the repository: {value}"
        ) from exc
    return candidate


def _strategy_constants(path: Path, class_name: str) -> dict[str, Any]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        raise ExperimentalModelResearchContractError(
            f"Unable to parse strategy {path}: {exc}"
        ) from exc

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            values: dict[str, Any] = {}
            for statement in node.body:
                if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                    continue
                target = statement.targets[0]
                if isinstance(target, ast.Name) and target.id in {
                    "entry_prediction_threshold",
                    "exit_prediction_threshold",
                }:
                    values[target.id] = ast.literal_eval(statement.value)
            return values
    raise ExperimentalModelResearchContractError(f"Strategy class {class_name} not found in {path}")


def _validate_shared_contract(foundation: dict[str, Any]) -> None:
    if foundation.get("schema_version") != 1:
        raise ExperimentalModelResearchContractError("Foundation schema_version must be 1")
    if foundation.get("status") != "foundation_only":
        raise ExperimentalModelResearchContractError("Foundation must remain foundation_only")

    phase6 = foundation.get("phase6_isolation")
    if not isinstance(phase6, dict) or phase6.get("membership") is not False:
        raise ExperimentalModelResearchContractError("Experimental tracks must not join Phase 6")
    for field in ("may_change_candidates", "may_change_selection_policy", "may_consume_research_results"):
        if phase6.get(field) is not False:
            raise ExperimentalModelResearchContractError(f"Phase 6 isolation requires {field}=false")

    final_holdout = foundation.get("protected_final_holdout")
    if not isinstance(final_holdout, dict):
        raise ExperimentalModelResearchContractError("Protected final holdout contract is missing")
    if final_holdout.get("timerange") != protected_timerange():
        raise ExperimentalModelResearchContractError("Protected final holdout timerange drifted")
    if final_holdout.get("used") is not False or final_holdout.get("usage") != "forbidden":
        raise ExperimentalModelResearchContractError("Protected final holdout must remain unused")

    geometry = foundation.get("shared_temporal_geometry")
    if not isinstance(geometry, dict):
        raise ExperimentalModelResearchContractError("Shared temporal geometry is missing")
    for field, expected in EXPECTED_GEOMETRY.items():
        if geometry.get(field) != expected:
            raise ExperimentalModelResearchContractError(
                f"Shared temporal geometry drifted for {field}: expected {expected}"
            )
    if geometry.get("historical_oos_status") != "consumed_historical_oos":
        raise ExperimentalModelResearchContractError("Research may use only consumed historical OOS")
    if geometry.get("training_mode") != "single_frozen_training_window":
        raise ExperimentalModelResearchContractError("Research training mode must stay single-window")
    if geometry.get("backtest_retraining_allowed") is not False:
        raise ExperimentalModelResearchContractError("Backtest retraining into OOS is forbidden")

    evaluation = foundation.get("evaluation_contract")
    if not isinstance(evaluation, dict):
        raise ExperimentalModelResearchContractError("Evaluation contract is missing")
    if evaluation.get("scoring_window") != EXPECTED_GEOMETRY["historical_oos_window"]:
        raise ExperimentalModelResearchContractError("Evaluation scoring window drifted")
    if evaluation.get("metrics") != EXPECTED_METRICS:
        raise ExperimentalModelResearchContractError("Trading metric contract drifted")
    if evaluation.get("strict_oos_trade_filter_required") is not True:
        raise ExperimentalModelResearchContractError("Strict OOS trade filtering must remain required")
    for field in ("training_loss_is_selection_evidence", "promotion_allowed", "profitability_claim_allowed"):
        if evaluation.get(field) is not False:
            raise ExperimentalModelResearchContractError(f"Evaluation contract requires {field}=false")


def _validate_track(track: dict[str, Any], foundation: dict[str, Any]) -> None:
    track_id = track.get("track_id")
    manifest_path = _repo_path(str(track.get("manifest", "")), f"{track_id} manifest")
    config_path = _repo_path(str(track.get("config", "")), f"{track_id} config")

    manifest = load_manifest(manifest_path)
    config = validate_research_config(config_path)
    freqai = config.get("freqai")
    if not isinstance(freqai, dict):
        raise ExperimentalModelResearchContractError(f"{track_id} config is missing freqai")

    expected_pairs = foundation["shared_trading_assumptions"]["pairs"]
    expected_timeframes = foundation["shared_trading_assumptions"]["timeframes"]
    geometry = foundation["shared_temporal_geometry"]

    expected_manifest_values = {
        "experiment_id": track_id,
        "config": track["config"],
        "strategy": track["strategy"],
        "freqai_model": track["freqai_model"],
        "timerange": geometry["prediction_window"],
        "download_timerange": geometry["download_timerange"],
        "pairs": expected_pairs,
        "timeframes": expected_timeframes,
        "fee": foundation["shared_trading_assumptions"]["fee"],
        "output_root": track["artifact_root"],
    }
    for field, expected in expected_manifest_values.items():
        if manifest.get(field) != expected:
            raise ExperimentalModelResearchContractError(
                f"{track_id} manifest drifted for {field}: expected {expected}"
            )

    if config.get("freqaimodel_path") != track.get("freqaimodel_path"):
        raise ExperimentalModelResearchContractError(f"{track_id} custom model path drifted")
    if freqai.get("identifier") != track.get("freqai_identifier"):
        raise ExperimentalModelResearchContractError(f"{track_id} FreqAI identifier drifted")
    if freqai.get("train_period_days") != geometry["train_period_days"]:
        raise ExperimentalModelResearchContractError(f"{track_id} train period drifted")
    if freqai.get("backtest_period_days") != geometry["backtest_period_days"]:
        raise ExperimentalModelResearchContractError(f"{track_id} prediction period drifted")
    if freqai.get("data_split_parameters", {}).get("shuffle") is not False:
        raise ExperimentalModelResearchContractError(f"{track_id} data split must not shuffle")

    for field in (
        "phase6_member",
        "final_holdout_used",
        "execution_performed",
        "promotion_allowed",
        "profitability_claim_allowed",
    ):
        if track.get(field) is not False:
            raise ExperimentalModelResearchContractError(f"{track_id} requires {field}=false")

    if track_id == "pytorch-research-v1":
        if track.get("freqai_model") != "SeededPyTorchMLPRegressor":
            raise ExperimentalModelResearchContractError("PyTorch baseline model identity drifted")
        seed = freqai.get("model_training_parameters", {}).get("research_seed")
        if seed != track.get("seed"):
            raise ExperimentalModelResearchContractError("PyTorch training seed drifted")
        strategy_path = REPO_ROOT / "ai_platform/strategies/AiFrozenCandidateStrategy.py"
        thresholds = _strategy_constants(strategy_path, "AiFrozenCandidateStrategy")
        frozen = foundation["shared_trading_assumptions"]["frozen_candidate_reference"]
        if thresholds != frozen:
            raise ExperimentalModelResearchContractError("Frozen candidate thresholds drifted")

    if track_id == "rl-research-v1":
        if track.get("backend") != "stable_baselines3" or track.get("algorithm") != "PPO":
            raise ExperimentalModelResearchContractError("RL backend or algorithm drifted")
        rl_config = freqai.get("rl_config")
        if not isinstance(rl_config, dict):
            raise ExperimentalModelResearchContractError("RL config is missing rl_config")
        if rl_config.get("model_type") != track.get("algorithm"):
            raise ExperimentalModelResearchContractError("RL configured algorithm drifted")
        if rl_config.get("add_state_info") is not False:
            raise ExperimentalModelResearchContractError("RL backtesting cannot add live state info")
        if rl_config.get("drop_ohlc_from_features") is not True:
            raise ExperimentalModelResearchContractError("Raw OHLC must stay outside agent features")
        if rl_config.get("randomize_starting_position") is not False:
            raise ExperimentalModelResearchContractError("RL episode start randomization is disabled")
        if freqai.get("continual_learning") is not False:
            raise ExperimentalModelResearchContractError("RL continual learning is forbidden")
        if freqai.get("model_training_parameters", {}).get("seed") != track.get("seed"):
            raise ExperimentalModelResearchContractError("RL seed drifted")
        if track.get("reward_contract", {}).get("future_market_information_used") is not False:
            raise ExperimentalModelResearchContractError("RL reward may not use future market data")
        expected_actions = {"0": "neutral", "1": "long_enter", "2": "long_exit"}
        if track.get("action_contract", {}).get("actions") != expected_actions:
            raise ExperimentalModelResearchContractError("RL action contract drifted")
        if track.get("action_contract", {}).get("short_actions_available") is not False:
            raise ExperimentalModelResearchContractError("RL research must remain long-only")


def validate_experimental_model_research_foundation(
    path: Path = DEFAULT_FOUNDATION,
) -> dict[str, Any]:
    """Validate static research contracts and guarded manifests without training or backtesting."""
    foundation = _read_json(path.resolve(), "experimental model research foundation")
    _validate_shared_contract(foundation)

    tracks = foundation.get("tracks")
    if not isinstance(tracks, list) or len(tracks) != 2:
        raise ExperimentalModelResearchContractError("Foundation requires exactly two research tracks")
    track_ids = {track.get("track_id") for track in tracks if isinstance(track, dict)}
    if track_ids != EXPECTED_TRACKS:
        raise ExperimentalModelResearchContractError("Foundation research-track identities drifted")

    identifiers: set[str] = set()
    artifact_roots: set[str] = set()
    manifests: set[str] = set()
    configs: set[str] = set()
    for track in tracks:
        if not isinstance(track, dict):
            raise ExperimentalModelResearchContractError("Each research track must be an object")
        _validate_track(track, foundation)
        identifiers.add(str(track.get("freqai_identifier")))
        artifact_roots.add(str(track.get("artifact_root")))
        manifests.add(str(track.get("manifest")))
        configs.add(str(track.get("config")))

    if not all(len(values) == 2 for values in (identifiers, artifact_roots, manifests, configs)):
        raise ExperimentalModelResearchContractError(
            "Research tracks require distinct identifiers, artifacts, manifests, and configs"
        )
    return foundation


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "foundation",
        nargs="?",
        type=Path,
        default=DEFAULT_FOUNDATION,
        help="Path to the experimental model research foundation JSON",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        foundation = validate_experimental_model_research_foundation(args.foundation)
    except (ExperimentalModelResearchContractError, RuntimeError) as exc:
        print(f"Experimental model research foundation validation failed: {exc}", file=sys.stderr)
        return 1
    print(foundation["foundation_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
