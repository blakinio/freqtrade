#!/usr/bin/env python3
"""Extract strict historical-OOS metrics for isolated PyTorch and RL research tracks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from ai_platform.scripts.experimental_model_research_contract import (
    ExperimentalModelResearchContractError,
    validate_experimental_model_research_foundation,
)
from ai_platform.scripts.model_comparison_oos_result_extractor import (
    DrawdownCalculator,
    ParsedTrade,
    _freqtrade_drawdown,
    _load_backtest_stats,
    _parse_trade,
    _partition_trades,
    _starting_balance,
    _trade_evidence,
)
from ai_platform.scripts.protected_final_holdout import protected_timerange
from ai_platform.scripts.run_experiment import (
    ExperimentError,
    load_manifest,
    validate_research_config,
)
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (
    REPO_ROOT
    / "ai_platform/experimental_model_research/oos-extraction-contract-v1.json"
)
DEFAULT_SCHEMA = (
    REPO_ROOT / "ai_platform/experimental_model_research/oos-extraction-schema-v1.json"
)
EXTRACTOR_ID = "experimental-model-strict-oos-extractor-v1"
EXPECTED_TRACKS = {"pytorch-research-v1", "rl-research-v1"}
EXPECTED_AUTHORIZATION = {
    "extraction_only": True,
    "final_holdout_used": False,
    "retuning_allowed": False,
    "promotion_allowed": False,
    "profitability_claim_allowed": False,
}


class ExperimentalModelOosExtractorError(RuntimeError):
    """Raised when experimental-model historical-OOS evidence cannot be extracted safely."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentalModelOosExtractorError(
            f"Unable to read {label} {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ExperimentalModelOosExtractorError(f"{label} must contain a JSON object")
    return payload


def _resolve_repo_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ExperimentalModelOosExtractorError(
            f"{label} must be a repository-relative path"
        )
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ExperimentalModelOosExtractorError(
            f"{label} escapes repository root"
        ) from exc
    return candidate


def _sha256(path: Path, label: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ExperimentalModelOosExtractorError(
            f"Unable to hash {label} {path}: {exc}"
        ) from exc


def _load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:  # noqa: C901
    contract = _read_json(path.resolve(), "experimental OOS extraction contract")
    if contract.get("schema_version") != 1:
        raise ExperimentalModelOosExtractorError(
            "OOS extraction contract schema_version must be 1"
        )
    if (
        contract.get("contract_id")
        != "experimental-model-research-strict-oos-extraction-v1"
    ):
        raise ExperimentalModelOosExtractorError(
            "Unexpected experimental OOS extraction contract_id"
        )
    if (
        contract.get("foundation")
        != "ai_platform/experimental_model_research/foundation-v1.json"
    ):
        raise ExperimentalModelOosExtractorError(
            "Experimental OOS foundation path drifted"
        )
    if (
        contract.get("schema")
        != "ai_platform/experimental_model_research/oos-extraction-schema-v1.json"
    ):
        raise ExperimentalModelOosExtractorError(
            "Experimental OOS extraction schema path drifted"
        )
    if set(contract.get("allowed_tracks", [])) != EXPECTED_TRACKS:
        raise ExperimentalModelOosExtractorError(
            "Experimental OOS allowed track identities drifted"
        )

    scoring = contract.get("scoring_window")
    expected_scoring = {
        "timerange": "20260501-20260630",
        "start_inclusive": "2026-05-01T00:00:00Z",
        "end_exclusive": "2026-07-01T00:00:00Z",
        "timezone": "UTC",
        "source_status": "consumed_historical_oos",
    }
    if scoring != expected_scoring:
        raise ExperimentalModelOosExtractorError(
            "Experimental OOS scoring window drifted"
        )

    inclusion = contract.get("trade_inclusion", {})
    if inclusion.get("policy") != "fully_contained_closed_trades":
        raise ExperimentalModelOosExtractorError(
            "Experimental OOS trade inclusion policy drifted"
        )
    if (
        inclusion.get("open_date_operator") != ">="
        or inclusion.get("close_date_operator") != "<"
    ):
        raise ExperimentalModelOosExtractorError(
            "Experimental OOS timestamp boundary semantics drifted"
        )
    if inclusion.get("pre_window_open_trade") != "exclude_and_count":
        raise ExperimentalModelOosExtractorError("Pre-window trade handling drifted")
    if inclusion.get("post_window_close_trade") != "exclude_and_count":
        raise ExperimentalModelOosExtractorError("Post-window trade handling drifted")
    if inclusion.get("force_exit_within_window") != "include_and_count":
        raise ExperimentalModelOosExtractorError("Force-exit trade handling drifted")
    if inclusion.get("missing_or_invalid_timestamp") != "fail_closed":
        raise ExperimentalModelOosExtractorError(
            "Invalid timestamp handling must remain fail-closed"
        )

    holdout = contract.get("protected_final_holdout", {})
    if holdout.get("timerange") != protected_timerange():
        raise ExperimentalModelOosExtractorError(
            "Protected final holdout timerange drifted"
        )
    if holdout.get("used") is not False or holdout.get("usage") != "forbidden":
        raise ExperimentalModelOosExtractorError(
            "Protected final holdout must remain forbidden"
        )

    phase6 = contract.get("phase6_isolation", {})
    if phase6 != {
        "member": False,
        "comparison_results_may_consume_extraction": False,
        "selection_policy_may_consume_extraction": False,
    }:
        raise ExperimentalModelOosExtractorError("Phase 6 isolation semantics drifted")
    if contract.get("authorization") != EXPECTED_AUTHORIZATION:
        raise ExperimentalModelOosExtractorError(
            "Experimental OOS authorization drifted"
        )
    return contract


def _load_track_and_manifest(
    manifest_path: Path,
    contract: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], Path, dict[str, Any]]:
    try:
        foundation = validate_experimental_model_research_foundation(
            _resolve_repo_path(contract["foundation"], "foundation")
        )
        manifest = load_manifest(manifest_path.resolve())
    except (ExperimentalModelResearchContractError, ExperimentError) as exc:
        raise ExperimentalModelOosExtractorError(str(exc)) from exc

    track_id = manifest.get("experiment_id")
    tracks = {
        track["track_id"]: track
        for track in foundation["tracks"]
        if isinstance(track, dict) and track.get("track_id") in EXPECTED_TRACKS
    }
    track = tracks.get(track_id)
    if track is None or track_id not in contract["allowed_tracks"]:
        raise ExperimentalModelOosExtractorError(
            "Manifest is not one of the isolated PyTorch/RL research tracks"
        )

    canonical_manifest_path = _resolve_repo_path(
        track["manifest"], f"{track_id} canonical manifest"
    )
    canonical_manifest = load_manifest(canonical_manifest_path)
    if manifest != canonical_manifest:
        raise ExperimentalModelOosExtractorError(
            f"{track_id} manifest differs from the canonical tracked research manifest"
        )

    config_path = _resolve_repo_path(track["config"], f"{track_id} config")
    try:
        config = validate_research_config(config_path)
    except ExperimentError as exc:
        raise ExperimentalModelOosExtractorError(str(exc)) from exc
    freqai = config.get("freqai")
    if (
        not isinstance(freqai, dict)
        or freqai.get("identifier") != track["freqai_identifier"]
    ):
        raise ExperimentalModelOosExtractorError(
            f"{track_id} FreqAI identifier drifted"
        )
    return foundation, track, config_path, manifest


def _strategy_stats_for_track(
    stats: dict[str, Any],
    track: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    strategies = stats.get("strategy")
    if not isinstance(strategies, dict) or set(strategies) != {track["strategy"]}:
        raise ExperimentalModelOosExtractorError(
            "Backtest archive must contain exactly the experimental manifest strategy result"
        )
    strategy_stats = strategies[track["strategy"]]
    if not isinstance(strategy_stats, dict):
        raise ExperimentalModelOosExtractorError(
            "Backtest strategy result must be a JSON object"
        )

    expected_identity = {
        "strategy_name": track["strategy"],
        "freqaimodel": track["freqai_model"],
        "freqai_identifier": track["freqai_identifier"],
        "timerange": manifest["timerange"],
    }
    for field, expected in expected_identity.items():
        if strategy_stats.get(field) != expected:
            raise ExperimentalModelOosExtractorError(
                f"Backtest strategy result field {field} does not match the research track identity"
            )
    return strategy_stats


def _stability_metrics(
    trades: list[ParsedTrade],
    starting_balance: float,
    contract: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    folds = contract["metrics"]["stability"]["folds"]
    fold_trade_counts: dict[str, int] = {}
    fold_profits: dict[str, float] = {}
    profitable_folds = 0

    for fold in folds:
        start = _parse_contract_timestamp(
            fold["start_inclusive"], f"fold {fold['name']} start"
        )
        end = _parse_contract_timestamp(
            fold["end_exclusive"], f"fold {fold['name']} end"
        )
        fold_trades = [trade for trade in trades if start <= trade.close_date < end]
        fold_profit = (
            math.fsum(trade.profit_abs for trade in fold_trades) / starting_balance
        )
        fold_trade_counts[fold["name"]] = len(fold_trades)
        fold_profits[fold["name"]] = fold_profit
        if fold_profit > 0:
            profitable_folds += 1

    evaluated_folds = len(folds)
    stability = profitable_folds / evaluated_folds if evaluated_folds else 0.0
    return stability, {
        "evaluated_folds": evaluated_folds,
        "profitable_folds": profitable_folds,
        "fold_trade_counts": fold_trade_counts,
        "fold_profits": fold_profits,
    }


def _parse_contract_timestamp(value: str, label: str):
    from datetime import UTC, datetime

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ExperimentalModelOosExtractorError(
            f"{label} is not valid ISO-8601"
        ) from exc
    if parsed.tzinfo is None:
        raise ExperimentalModelOosExtractorError(
            f"{label} must include an explicit timezone"
        )
    return parsed.astimezone(UTC)


def validate_experimental_oos_extraction(result: dict[str, Any]) -> dict[str, Any]:
    schema = _read_json(DEFAULT_SCHEMA, "experimental OOS extraction schema")
    try:
        Draft202012Validator(schema).validate(result)
    except ValidationError as exc:
        raise ExperimentalModelOosExtractorError(
            f"Experimental OOS extraction does not match schema: {exc.message}"
        ) from exc
    return result


def extract_experimental_oos_result(
    archive_path: Path,
    manifest_path: Path,
    *,
    drawdown_calculator: DrawdownCalculator | None = None,
) -> dict[str, Any]:
    """Extract strict May-June historical-OOS evidence without running training or backtesting."""
    contract = _load_contract()
    _, track, config_path, manifest = _load_track_and_manifest(manifest_path, contract)
    stats, stats_member, archive_sha256 = _load_backtest_stats(archive_path)
    strategy_stats = _strategy_stats_for_track(stats, track, manifest)
    starting_balance = _starting_balance(strategy_stats)

    raw_trades = strategy_stats.get("trades")
    if not isinstance(raw_trades, list):
        raise ExperimentalModelOosExtractorError(
            "Backtest strategy result trades must be a list"
        )
    required_fields = contract["required_trade_fields"]
    trades = [
        _parse_trade(trade, source_index, required_fields)
        for source_index, trade in enumerate(raw_trades)
    ]
    boundary = {"scoring_window": contract["scoring_window"]}
    included, excluded_evidence, counts = _partition_trades(trades, boundary)

    profit = math.fsum(trade.profit_abs for trade in included) / starting_balance
    calculator = drawdown_calculator or _freqtrade_drawdown
    drawdown = float(calculator(included, starting_balance))
    if not math.isfinite(drawdown) or drawdown < 0:
        raise ExperimentalModelOosExtractorError(
            "Drawdown calculator must return a finite non-negative ratio"
        )
    stability, stability_evidence = _stability_metrics(
        included, starting_balance, contract
    )

    result = {
        "schema_version": 1,
        "extractor_id": EXTRACTOR_ID,
        "contract_id": contract["contract_id"],
        "track_id": track["track_id"],
        "model_type": track["freqai_model"],
        "experiment_identity": manifest["experiment_id"],
        "freqai_identifier": track["freqai_identifier"],
        "strategy": track["strategy"],
        "source": {
            "archive_sha256": archive_sha256,
            "stats_member": stats_member,
            "manifest_sha256": _sha256(manifest_path.resolve(), "manifest"),
            "config_sha256": _sha256(config_path, "config"),
        },
        "scoring_window": contract["scoring_window"],
        "starting_balance": starting_balance,
        "counts": counts,
        "metrics": {
            "profit": profit,
            "drawdown": drawdown,
            "trades": len(included),
            "stability": stability,
        },
        "stability_evidence": stability_evidence,
        "included_trade_evidence": [_trade_evidence(trade) for trade in included],
        "excluded_trade_evidence": excluded_evidence,
        "authorization": {
            **contract["authorization"],
            "phase6_member": False,
        },
    }
    return validate_experimental_oos_extraction(result)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        raise ExperimentalModelOosExtractorError(
            f"Unable to write extraction output: {exc}"
        ) from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "archive", type=Path, help="Existing Freqtrade backtest result ZIP"
    )
    parser.add_argument(
        "manifest", type=Path, help="Canonical PyTorch or RL research manifest"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output JSON evidence path"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = extract_experimental_oos_result(args.archive, args.manifest)
        _write_json(args.output, result)
    except (ExperimentalModelOosExtractorError, RuntimeError) as exc:
        print(f"Experimental OOS result extraction failed: {exc}", file=sys.stderr)
        return 1
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
