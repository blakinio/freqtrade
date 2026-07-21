#!/usr/bin/env python3
"""Validate the exact one-shot Phase 6 historical model-comparison run request."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ai_platform.scripts.model_comparison_contract import load_model_comparison_contract
from ai_platform.scripts.model_comparison_harness import build_materialization


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REPO_PATH = "ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json"
CONTRACT_PATH = REPO_ROOT / CONTRACT_REPO_PATH
CANONICAL_MATERIALIZATION_ROOT = "ai_platform/artifacts/model-comparison/materialized"
EXPECTED_REQUEST_ID = "freqai-lightgbm-vs-xgboost-v1-historical-run-v1"
EXPECTED_ACTION = "execute_historical_model_comparison"
EXPECTED_WINDOWS = {
    "training_window": "20251201-20260228",
    "tuning_window": "20260301-20260430",
    "scoring_window": "20260501-20260630",
    "prediction_window": "20260301-20260630",
    "download_timerange": "20250801-20260630",
}
EXPECTED_PROTECTED_FINAL_HOLDOUT = "20260801-20260930"
EXPECTED_FROZEN_PARAMETERS = {
    "entry_prediction_threshold": 0.006,
    "exit_prediction_threshold": -0.009,
}
EXPECTED_AUTHORIZATION = {
    "final_holdout_used": False,
    "retuning_allowed": False,
    "model_parameter_changes_allowed": False,
    "feature_changes_allowed": False,
    "promotion_allowed": False,
    "live_trading_allowed": False,
    "profitability_claim_allowed": False,
}


class ModelComparisonRunRequestError(RuntimeError):
    """Raised when a Phase 6 one-shot execution request is not canonical and safe."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelComparisonRunRequestError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ModelComparisonRunRequestError(f"{label} must contain a JSON object")
    return payload


def _canonical_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    contract = load_model_comparison_contract(CONTRACT_PATH)
    materialization = build_materialization(
        CONTRACT_PATH,
        output_root=CANONICAL_MATERIALIZATION_ROOT,
    )

    actual_windows = {field: materialization[field] for field in EXPECTED_WINDOWS}
    if actual_windows != EXPECTED_WINDOWS:
        raise ModelComparisonRunRequestError(
            "Canonical Phase 6 historical windows drifted from the predeclared execution request"
        )

    protected_timerange = contract["protected_final_holdout"]["timerange"]
    if protected_timerange != EXPECTED_PROTECTED_FINAL_HOLDOUT:
        raise ModelComparisonRunRequestError(
            "Protected final holdout drifted from the prospectively declared Phase 6 boundary"
        )

    risk = contract["shared_experiment"]["risk_assumptions"]
    frozen_parameters = {parameter: risk.get(parameter) for parameter in EXPECTED_FROZEN_PARAMETERS}
    if frozen_parameters != EXPECTED_FROZEN_PARAMETERS:
        raise ModelComparisonRunRequestError(
            "Frozen Phase 5.2 thresholds drifted from the Phase 6 execution boundary"
        )
    return contract, materialization


def canonical_model_comparison_run_request() -> dict[str, Any]:
    """Return the only run-request payload authorized by the Phase 6 workflow."""
    contract, materialization = _canonical_inputs()
    return {
        "schema_version": 1,
        "request_id": EXPECTED_REQUEST_ID,
        "action": EXPECTED_ACTION,
        "comparison_id": contract["comparison_id"],
        "contract_path": CONTRACT_REPO_PATH,
        "contract_sha256": materialization["contract_sha256"],
        **EXPECTED_WINDOWS,
        "protected_final_holdout": EXPECTED_PROTECTED_FINAL_HOLDOUT,
        "frozen_parameters": dict(EXPECTED_FROZEN_PARAMETERS),
        "authorization": dict(EXPECTED_AUTHORIZATION),
    }


def load_model_comparison_run_request(path: Path) -> dict[str, Any]:
    """Load and fail closed unless the request exactly matches the canonical payload."""
    request = _read_json(path.resolve(), "model comparison run request")
    expected = canonical_model_comparison_run_request()

    if set(request) != set(expected):
        missing = sorted(set(expected) - set(request))
        extra = sorted(set(request) - set(expected))
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if extra:
            details.append(f"extra={','.join(extra)}")
        raise ModelComparisonRunRequestError(
            "Run request fields do not match the canonical execution request: " + "; ".join(details)
        )

    for field, expected_value in expected.items():
        if request[field] != expected_value:
            raise ModelComparisonRunRequestError(
                f"Run request field {field} drifted from the canonical execution request"
            )
    return request


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "request",
        nargs="?",
        type=Path,
        help="Path to the one-shot Phase 6 historical comparison request JSON",
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
        print(json.dumps(canonical_model_comparison_run_request(), indent=2, sort_keys=True))
        return 0
    if args.request is None:
        print(
            "A request path is required unless --print-canonical is used",
            file=sys.stderr,
        )
        return 2
    try:
        request = load_model_comparison_run_request(args.request)
    except ModelComparisonRunRequestError as exc:
        print(f"Model comparison run request invalid: {exc}", file=sys.stderr)
        return 1
    print(request["request_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
