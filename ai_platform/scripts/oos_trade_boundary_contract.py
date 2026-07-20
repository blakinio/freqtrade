#!/usr/bin/env python3
"""Validate the Phase 6 model-comparison OOS trade-boundary contract."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ai_platform.scripts.model_comparison_contract import load_model_comparison_contract
from ai_platform.scripts.protected_final_holdout import (
    load_protected_final_holdout,
    timeranges_overlap,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_BOUNDARY_ID = "freqai-model-comparison-oos-trade-boundary-v1"
EXPECTED_COMPARISON_CONTRACT = "ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json"
EXPECTED_POLICY = "fully_contained_closed_trades"


class OosTradeBoundaryContractError(RuntimeError):
    """Raised when the OOS trade-boundary definition is unsafe or inconsistent."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OosTradeBoundaryContractError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise OosTradeBoundaryContractError(f"{label} must contain a JSON object")
    return payload


def _resolve_repo_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise OosTradeBoundaryContractError(f"{label} must be a repository-relative path")
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise OosTradeBoundaryContractError(f"{label} escapes repository root") from exc
    return candidate


def _parse_iso_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise OosTradeBoundaryContractError(
            f"{label} must be an explicit UTC timestamp ending in Z"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OosTradeBoundaryContractError(f"{label} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo != UTC:
        raise OosTradeBoundaryContractError(f"{label} must use UTC")
    return parsed


def _parse_timerange(value: Any, label: str) -> tuple[datetime, datetime]:
    if not isinstance(value, str):
        raise OosTradeBoundaryContractError(f"{label} must be a timerange string")
    try:
        start_raw, end_raw = value.split("-", maxsplit=1)
        start = datetime.strptime(start_raw, "%Y%m%d").replace(tzinfo=UTC)
        end_inclusive = datetime.strptime(end_raw, "%Y%m%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise OosTradeBoundaryContractError(
            f"{label} must use valid YYYYMMDD-YYYYMMDD dates"
        ) from exc
    if start > end_inclusive:
        raise OosTradeBoundaryContractError(f"{label} starts after it ends")
    return start, end_inclusive + timedelta(days=1)


def _validate_scoring_window(boundary: dict[str, Any], comparison: dict[str, Any]) -> str:
    scoring = boundary.get("scoring_window")
    if not isinstance(scoring, dict):
        raise OosTradeBoundaryContractError("scoring_window must be an object")

    historical = comparison["shared_experiment"]["historical_oos_windows"]
    if len(historical) != 1:
        raise OosTradeBoundaryContractError(
            "Boundary v1 requires exactly one comparison historical OOS window"
        )
    source = historical[0]
    if source.get("unseen_status") != "consumed_historical_oos":
        raise OosTradeBoundaryContractError("Scoring source must remain consumed_historical_oos")

    timerange = scoring.get("timerange")
    if timerange != source.get("timerange"):
        raise OosTradeBoundaryContractError(
            "scoring_window.timerange must exactly match the comparison historical OOS window"
        )
    if scoring.get("source_status") != source.get("unseen_status"):
        raise OosTradeBoundaryContractError("scoring_window.source_status drifted from comparison")
    if scoring.get("timezone") != "UTC":
        raise OosTradeBoundaryContractError("OOS trade-boundary timestamps must use UTC")

    timerange_start, timerange_end_exclusive = _parse_timerange(
        timerange,
        "scoring_window.timerange",
    )
    start_inclusive = _parse_iso_utc(
        scoring.get("start_inclusive"), "scoring_window.start_inclusive"
    )
    end_exclusive = _parse_iso_utc(scoring.get("end_exclusive"), "scoring_window.end_exclusive")
    if start_inclusive != timerange_start:
        raise OosTradeBoundaryContractError(
            "scoring_window.start_inclusive does not match timerange start"
        )
    if end_exclusive != timerange_end_exclusive:
        raise OosTradeBoundaryContractError(
            "scoring_window.end_exclusive must be the UTC day after timerange end"
        )
    return timerange


def _validate_trade_policy(boundary: dict[str, Any]) -> None:
    trade = boundary.get("trade_inclusion")
    if not isinstance(trade, dict) or trade.get("policy") != EXPECTED_POLICY:
        raise OosTradeBoundaryContractError("OOS scoring must use fully_contained_closed_trades")
    if trade.get("open_date") != {"operator": ">=", "boundary": "start_inclusive"}:
        raise OosTradeBoundaryContractError("OOS scoring must require open_date >= start_inclusive")
    if trade.get("close_date") != {"operator": "<", "boundary": "end_exclusive"}:
        raise OosTradeBoundaryContractError("OOS scoring must require close_date < end_exclusive")
    expected_actions = {
        "pre_window_open_trade": "exclude_and_count",
        "post_window_close_trade": "exclude_and_count",
        "force_exit_within_window": "include_and_count",
        "missing_or_invalid_timestamp": "fail_closed",
    }
    for field, expected in expected_actions.items():
        if trade.get(field) != expected:
            raise OosTradeBoundaryContractError(f"trade_inclusion.{field} must remain {expected}")


def _validate_extractor_requirements(boundary: dict[str, Any]) -> None:
    requirements = boundary.get("future_extractor_requirements")
    expected = {
        "metric_scope": "included_trades_only",
        "record_excluded_pre_window_open_trades": True,
        "record_excluded_post_window_close_trades": True,
        "record_included_force_exit_trades": True,
        "preserve_original_trade_timestamps": True,
    }
    if requirements != expected:
        raise OosTradeBoundaryContractError(
            "future_extractor_requirements must preserve strict boundary evidence"
        )


def _validate_protected_final_holdout(boundary: dict[str, Any], scoring_timerange: str) -> None:
    protected = boundary.get("protected_final_holdout")
    if not isinstance(protected, dict):
        raise OosTradeBoundaryContractError("protected_final_holdout must be an object")
    declaration = load_protected_final_holdout()
    declaration_timerange = declaration["final_holdout"]["timerange"]
    if protected.get("timerange") != declaration_timerange:
        raise OosTradeBoundaryContractError(
            "protected_final_holdout.timerange must match the prospective declaration"
        )
    declaration_path = protected.get("declaration")
    if declaration_path != "ai_platform/validation/final-holdout-v2-declaration.json":
        raise OosTradeBoundaryContractError("Protected final holdout declaration path drifted")
    if protected.get("must_not_overlap_scoring_window") is not True:
        raise OosTradeBoundaryContractError(
            "Scoring/final-holdout non-overlap must remain mandatory"
        )
    if timeranges_overlap(scoring_timerange, declaration_timerange):
        raise OosTradeBoundaryContractError("OOS scoring window overlaps protected final holdout")


def _validate_authorization(boundary: dict[str, Any]) -> None:
    expected = {
        "final_holdout_used": False,
        "retuning_allowed": False,
        "promotion_allowed": False,
        "profitability_claim_allowed": False,
    }
    if boundary.get("authorization") != expected:
        raise OosTradeBoundaryContractError(
            "OOS boundary cannot authorize holdout use, retuning, promotion, or "
            "profitability claims"
        )


def load_oos_trade_boundary_contract(path: Path) -> dict[str, Any]:
    boundary = _read_json(path.resolve(), "OOS trade-boundary contract")
    if boundary.get("schema_version") != 1:
        raise OosTradeBoundaryContractError("Only OOS trade-boundary schema_version 1 is supported")
    if boundary.get("boundary_id") != EXPECTED_BOUNDARY_ID:
        raise OosTradeBoundaryContractError("Unexpected OOS trade-boundary id")
    if boundary.get("comparison_contract") != EXPECTED_COMPARISON_CONTRACT:
        raise OosTradeBoundaryContractError("Unexpected model comparison contract path")

    comparison_path = _resolve_repo_path(
        boundary.get("comparison_contract"),
        "comparison_contract",
    )
    comparison = load_model_comparison_contract(comparison_path)
    scoring_timerange = _validate_scoring_window(boundary, comparison)
    _validate_trade_policy(boundary)
    _validate_extractor_requirements(boundary)
    _validate_protected_final_holdout(boundary, scoring_timerange)
    _validate_authorization(boundary)
    return boundary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to OOS trade-boundary contract JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        boundary = load_oos_trade_boundary_contract(args.contract)
    except OosTradeBoundaryContractError as exc:
        print(f"OOS trade-boundary contract invalid: {exc}", file=sys.stderr)
        return 1
    print(boundary["boundary_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
