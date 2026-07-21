#!/usr/bin/env python3
"""Validate the exact one-shot PyTorch/RL historical backtest execution request."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from ai_platform.scripts.experimental_model_research_contract import (
    ExperimentalModelResearchContractError,
    validate_experimental_model_research_foundation,
)
from ai_platform.scripts.run_experiment import ExperimentError, load_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REPO_PATH = (
    "ai_platform/experimental_model_research/historical-backtest-execution-contract-v1.json"
)
CONTRACT_PATH = REPO_ROOT / CONTRACT_REPO_PATH
REQUEST_REPO_PATH = (
    "ai_platform/experimental_model_research/run-requests/historical-backtest-execution-v1.json"
)
EXPECTED_REQUEST_ID = "experimental-model-historical-backtest-execution-v1"
EXPECTED_ACTION = "execute_experimental_model_historical_backtests"
EXPECTED_TRACKS = {
    "pytorch-research-v1": {
        "track_id": "pytorch-research-v1",
        "manifest": "ai_platform/experiments/pytorch-research-v1.json",
        "config": "ai_platform/configs/freqai-pytorch-research.example.json",
        "strategy": "AiFrozenCandidateStrategy",
        "strategy_file": "ai_platform/strategies/AiFrozenCandidateStrategy.py",
        "freqai_model": "SeededPyTorchMLPRegressor",
        "freqai_model_file": "ai_platform/freqaimodels/SeededPyTorchMLPRegressor.py",
        "freqai_identifier": "ai-platform-pytorch-research-v1",
    },
    "rl-research-v1": {
        "track_id": "rl-research-v1",
        "manifest": "ai_platform/experiments/rl-research-v1.json",
        "config": "ai_platform/configs/freqai-rl-research.example.json",
        "strategy": "AiLongOnlyRLResearchStrategy",
        "strategy_file": "ai_platform/strategies/AiLongOnlyRLResearchStrategy.py",
        "freqai_model": "LongOnlyReinforcementLearner",
        "freqai_model_file": "ai_platform/freqaimodels/LongOnlyReinforcementLearner.py",
        "freqai_identifier": "ai-platform-rl-research-v1",
    },
}
EXPECTED_EXECUTION = {
    "mode": "one_shot_trigger_pr",
    "executions_per_track": 1,
    "semantic_prediction_window": "20260301-20260630",
    "timerange": "20260301-20260701",
    "download_timerange": "20250801-20260701",
}
EXPECTED_MARKET_DATA = {
    "exchange": "kraken",
    "pairs": ["BTC/USDT", "ETH/USDT"],
    "timeframes": ["15m", "1h", "4h"],
    "fee": 0.002,
    "verification_module": "ai_platform.scripts.experimental_model_historical_execution_preflight",
    "cache_namespace": "experimental-model-historical-preflight-v2",
}
EXPECTED_STRICT_OOS = {
    "module": "ai_platform.scripts.experimental_model_oos_result_extractor",
    "contract": "ai_platform/experimental_model_research/oos-extraction-contract-v1.json",
    "scoring_window": "20260501-20260630",
    "start_inclusive": "2026-05-01T00:00:00Z",
    "end_exclusive": "2026-07-01T00:00:00Z",
    "one_extraction_per_track": True,
}
EXPECTED_FROZEN_PARAMETERS = {
    "entry_prediction_threshold": 0.006,
    "exit_prediction_threshold": -0.009,
}
EXPECTED_PROTECTED_FINAL_HOLDOUT = {
    "timerange": "20260801-20260930",
    "used": False,
    "usage": "forbidden",
}
EXPECTED_PHASE6_ISOLATION = {
    "member": False,
    "may_change_candidates": False,
    "may_change_selection_policy": False,
    "may_consume_results": False,
}
EXPECTED_AUTHORIZATION = {
    "historical_backtest_execution_allowed": True,
    "strict_oos_extraction_allowed": True,
    "final_holdout_used": False,
    "retuning_allowed": False,
    "model_parameter_changes_allowed": False,
    "feature_changes_allowed": False,
    "reward_changes_allowed": False,
    "cross_track_selection_allowed": False,
    "promotion_allowed": False,
    "live_trading_allowed": False,
    "profitability_claim_allowed": False,
    "superiority_claim_allowed": False,
}
EXPECTED_TRIGGER = {
    "event": "pull_request_opened",
    "base_branch": "develop",
    "exact_one_file": True,
}


class ExperimentalModelHistoricalBacktestRunRequestError(RuntimeError):
    """Raised when the one-shot experimental execution request is not canonical and safe."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            f"Unable to read {label} {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            f"{label} must contain a JSON object"
        )
    return payload


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            f"Unable to hash canonical input {path}: {exc}"
        ) from exc


def _repo_path(value: str) -> Path:
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            f"Canonical path escapes repository root: {value}"
        ) from exc
    return candidate


def _validate_contract() -> tuple[dict[str, Any], list[dict[str, Any]]]:  # noqa: C901
    contract = _read_json(CONTRACT_PATH, "experimental historical backtest contract")
    if contract.get("schema_version") != 1:
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            "Historical backtest contract schema_version must be 1"
        )
    if contract.get("contract_id") != EXPECTED_REQUEST_ID:
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            "Historical backtest contract_id drifted"
        )
    if contract.get("task") != (
        "docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md"
    ):
        raise ExperimentalModelHistoricalBacktestRunRequestError("Historical backtest task drifted")
    if contract.get("foundation") != "ai_platform/experimental_model_research/foundation-v1.json":
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            "Experimental research foundation path drifted"
        )
    if contract.get("request_path") != REQUEST_REPO_PATH:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Canonical request path drifted")
    if contract.get("trigger") != EXPECTED_TRIGGER:
        raise ExperimentalModelHistoricalBacktestRunRequestError("One-shot trigger contract drifted")
    if contract.get("execution") != EXPECTED_EXECUTION:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Execution geometry drifted")
    if contract.get("market_data") != EXPECTED_MARKET_DATA:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Market-data contract drifted")
    if contract.get("strict_oos_extraction") != EXPECTED_STRICT_OOS:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Strict OOS extraction contract drifted")
    if contract.get("frozen_parameters") != EXPECTED_FROZEN_PARAMETERS:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Frozen thresholds drifted")
    if contract.get("protected_final_holdout") != EXPECTED_PROTECTED_FINAL_HOLDOUT:
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            "Protected final holdout contract drifted"
        )
    if contract.get("phase6_isolation") != EXPECTED_PHASE6_ISOLATION:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Phase 6 isolation contract drifted")
    if contract.get("authorization") != EXPECTED_AUTHORIZATION:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Execution authorization drifted")

    contract_tracks = contract.get("tracks")
    if not isinstance(contract_tracks, list) or len(contract_tracks) != len(EXPECTED_TRACKS):
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            "Historical backtest contract must contain exactly two canonical tracks"
        )
    actual_tracks = {track.get("track_id"): track for track in contract_tracks if isinstance(track, dict)}
    if actual_tracks != EXPECTED_TRACKS:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Canonical track contract drifted")

    try:
        foundation = validate_experimental_model_research_foundation(
            _repo_path(contract["foundation"])
        )
    except ExperimentalModelResearchContractError as exc:
        raise ExperimentalModelHistoricalBacktestRunRequestError(str(exc)) from exc

    geometry = foundation["shared_temporal_geometry"]
    if geometry.get("prediction_window") != EXPECTED_EXECUTION["semantic_prediction_window"]:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Semantic prediction window drifted")
    if geometry.get("freqtrade_prediction_timerange") != EXPECTED_EXECUTION["timerange"]:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Execution timerange drifted")
    if geometry.get("freqtrade_download_timerange") != EXPECTED_EXECUTION["download_timerange"]:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Download timerange drifted")
    if geometry.get("historical_oos_window") != EXPECTED_STRICT_OOS["scoring_window"]:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Historical OOS window drifted")
    if foundation["protected_final_holdout"]["timerange"] != EXPECTED_PROTECTED_FINAL_HOLDOUT["timerange"]:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Foundation final holdout drifted")
    if foundation["shared_trading_assumptions"]["frozen_candidate_reference"] != EXPECTED_FROZEN_PARAMETERS:
        raise ExperimentalModelHistoricalBacktestRunRequestError("Foundation frozen thresholds drifted")

    foundation_tracks = {track["track_id"]: track for track in foundation["tracks"]}
    canonical_tracks: list[dict[str, Any]] = []
    for track_id in EXPECTED_TRACKS:
        expected_track = EXPECTED_TRACKS[track_id]
        foundation_track = foundation_tracks.get(track_id)
        if foundation_track is None:
            raise ExperimentalModelHistoricalBacktestRunRequestError(
                f"Foundation is missing canonical track {track_id}"
            )
        for field in ("manifest", "config", "strategy", "freqai_model", "freqai_identifier"):
            if foundation_track.get(field) != expected_track[field]:
                raise ExperimentalModelHistoricalBacktestRunRequestError(
                    f"{track_id} foundation field {field} drifted"
                )
        if foundation_track.get("phase6_member") is not False:
            raise ExperimentalModelHistoricalBacktestRunRequestError(
                f"{track_id} must remain outside Phase 6"
            )
        if foundation_track.get("final_holdout_used") is not False:
            raise ExperimentalModelHistoricalBacktestRunRequestError(
                f"{track_id} must not use the protected final holdout"
            )

        manifest_path = _repo_path(expected_track["manifest"])
        try:
            manifest = load_manifest(manifest_path)
        except ExperimentError as exc:
            raise ExperimentalModelHistoricalBacktestRunRequestError(str(exc)) from exc
        manifest_expected = {
            "experiment_id": track_id,
            "config": expected_track["config"],
            "strategy": expected_track["strategy"],
            "freqai_model": expected_track["freqai_model"],
            "timerange": EXPECTED_EXECUTION["timerange"],
            "download_timerange": EXPECTED_EXECUTION["download_timerange"],
            "pairs": EXPECTED_MARKET_DATA["pairs"],
            "timeframes": EXPECTED_MARKET_DATA["timeframes"],
            "fee": EXPECTED_MARKET_DATA["fee"],
        }
        for field, expected_value in manifest_expected.items():
            if manifest.get(field) != expected_value:
                raise ExperimentalModelHistoricalBacktestRunRequestError(
                    f"{track_id} manifest field {field} drifted"
                )

        config_path = _repo_path(expected_track["config"])
        strategy_path = _repo_path(expected_track["strategy_file"])
        model_path = _repo_path(expected_track["freqai_model_file"])
        for path, label in (
            (config_path, "config"),
            (strategy_path, "strategy"),
            (model_path, "FreqAI model"),
        ):
            if not path.is_file():
                raise ExperimentalModelHistoricalBacktestRunRequestError(
                    f"{track_id} canonical {label} file is missing: {path}"
                )

        canonical_tracks.append(
            {
                "track_id": track_id,
                "manifest_path": expected_track["manifest"],
                "manifest_sha256": _sha256(manifest_path),
                "config_path": expected_track["config"],
                "config_sha256": _sha256(config_path),
                "strategy": expected_track["strategy"],
                "strategy_path": expected_track["strategy_file"],
                "strategy_sha256": _sha256(strategy_path),
                "freqai_model": expected_track["freqai_model"],
                "freqai_model_path": expected_track["freqai_model_file"],
                "freqai_model_sha256": _sha256(model_path),
                "freqai_identifier": expected_track["freqai_identifier"],
            }
        )
    return contract, canonical_tracks


def canonical_experimental_model_historical_backtest_run_request() -> dict[str, Any]:
    """Return the only request payload authorized by the one-shot execution workflow."""
    contract, tracks = _validate_contract()
    return {
        "schema_version": 1,
        "request_id": EXPECTED_REQUEST_ID,
        "action": EXPECTED_ACTION,
        "contract_path": CONTRACT_REPO_PATH,
        "contract_sha256": _sha256(CONTRACT_PATH),
        "tracks": tracks,
        "semantic_prediction_window": EXPECTED_EXECUTION["semantic_prediction_window"],
        "execution_timerange": EXPECTED_EXECUTION["timerange"],
        "download_timerange": EXPECTED_EXECUTION["download_timerange"],
        "strict_oos_scoring_window": EXPECTED_STRICT_OOS["scoring_window"],
        "protected_final_holdout": EXPECTED_PROTECTED_FINAL_HOLDOUT["timerange"],
        "frozen_parameters": dict(EXPECTED_FROZEN_PARAMETERS),
        "authorization": dict(contract["authorization"]),
    }


def load_experimental_model_historical_backtest_run_request(path: Path) -> dict[str, Any]:
    """Load and fail closed unless a request exactly matches the canonical payload."""
    request = _read_json(path.resolve(), "experimental historical backtest run request")
    expected = canonical_experimental_model_historical_backtest_run_request()
    if set(request) != set(expected):
        missing = sorted(set(expected) - set(request))
        extra = sorted(set(request) - set(expected))
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if extra:
            details.append(f"extra={','.join(extra)}")
        raise ExperimentalModelHistoricalBacktestRunRequestError(
            "Run request fields do not match the canonical execution request: " + "; ".join(details)
        )
    for field, expected_value in expected.items():
        if request[field] != expected_value:
            raise ExperimentalModelHistoricalBacktestRunRequestError(
                f"Run request field {field} drifted from the canonical execution request"
            )
    return request


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "request",
        nargs="?",
        type=Path,
        help="Path to the one-shot experimental historical backtest request JSON",
    )
    parser.add_argument(
        "--print-canonical",
        action="store_true",
        help="Print the exact request payload that a separate trigger PR must add",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.print_canonical:
        if args.request is not None:
            print("Do not pass a request path with --print-canonical", file=sys.stderr)
            return 2
        print(
            json.dumps(
                canonical_experimental_model_historical_backtest_run_request(),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.request is None:
        print("A request path is required unless --print-canonical is used", file=sys.stderr)
        return 2
    try:
        request = load_experimental_model_historical_backtest_run_request(args.request)
    except ExperimentalModelHistoricalBacktestRunRequestError as exc:
        print(f"Experimental historical backtest run request invalid: {exc}", file=sys.stderr)
        return 1
    print(request["request_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
