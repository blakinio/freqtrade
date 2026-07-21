#!/usr/bin/env python3
"""Validate the exact one-shot Phase 6 historical comparison execution request."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REQUEST = (
    REPO_ROOT / "ai_platform/model_comparison/run-requests/historical-comparison-v1.json"
)
COMPARISON_CONTRACT = REPO_ROOT / "ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json"
SELECTION_POLICY = REPO_ROOT / "ai_platform/model_comparison/selection-policy-v1.json"
BASELINE_MANIFEST = REPO_ROOT / "ai_platform/experiments/baseline-v1.json"
FINAL_HOLDOUT_DECLARATION = REPO_ROOT / "ai_platform/validation/final-holdout-v2-declaration.json"
EXPECTED_MODELS = ["LightGBMRegressor", "XGBoostRegressor"]
EXPECTED_COMPARISON_ID = "freqai-lightgbm-vs-xgboost-v1"
EXPECTED_REQUEST_ID = "freqai-lightgbm-vs-xgboost-historical-comparison-run-v1"
EXPECTED_TRAINING_WINDOW = "20251201-20260228"
EXPECTED_TUNING_WINDOW = "20260301-20260430"
EXPECTED_HISTORICAL_OOS = "20260501-20260630"
EXPECTED_DOWNLOAD_TIMERANGE = "20250801-20260630"
EXPECTED_FINAL_HOLDOUT = "20260801-20260930"
EXPECTED_ENTRY_THRESHOLD = 0.006
EXPECTED_EXIT_THRESHOLD = -0.009


class ModelComparisonExecutionRequestError(RuntimeError):
    """Raised when a historical comparison execution request is not exactly frozen."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelComparisonExecutionRequestError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ModelComparisonExecutionRequestError(f"{label} must contain a JSON object")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ModelComparisonExecutionRequestError(f"Unable to hash {path}: {exc}") from exc
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ModelComparisonExecutionRequestError(message)


def _validate_frozen_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = _read_json(COMPARISON_CONTRACT, "model comparison contract")
    policy = _read_json(SELECTION_POLICY, "model selection policy")
    baseline = _read_json(BASELINE_MANIFEST, "baseline experiment manifest")
    declaration = _read_json(FINAL_HOLDOUT_DECLARATION, "protected final holdout declaration")

    shared = contract.get("shared_experiment")
    _require(isinstance(shared, dict), "Comparison contract shared_experiment must be an object")
    historical = shared.get("historical_oos_windows")
    _require(
        isinstance(historical, list) and len(historical) == 1 and isinstance(historical[0], dict),
        "Comparison contract must contain exactly one historical OOS window",
    )
    historical_window = historical[0]
    risk = shared.get("risk_assumptions")
    _require(isinstance(risk, dict), "Comparison contract risk_assumptions must be an object")

    checks = {
        "comparison_id": contract.get("comparison_id") == EXPECTED_COMPARISON_ID,
        "models": contract.get("models") == EXPECTED_MODELS,
        "variable_under_test": contract.get("variable_under_test") == "freqai_model",
        "training_window": shared.get("training_window") == EXPECTED_TRAINING_WINDOW,
        "tuning_window": shared.get("tuning_window") == EXPECTED_TUNING_WINDOW,
        "historical_oos_window": historical_window.get("timerange") == EXPECTED_HISTORICAL_OOS,
        "historical_oos_status": historical_window.get("unseen_status")
        == "consumed_historical_oos",
        "entry_threshold": risk.get("entry_prediction_threshold") == EXPECTED_ENTRY_THRESHOLD,
        "exit_threshold": risk.get("exit_prediction_threshold") == EXPECTED_EXIT_THRESHOLD,
        "dry_run": risk.get("dry_run") is True,
        "spot_only": risk.get("trading_mode") == "spot" and risk.get("can_short") is False,
        "joint_tuning_forbidden": contract.get("model_parameter_policy", {}).get(
            "joint_tuning_allowed"
        )
        is False,
        "feature_changes_forbidden": contract.get("model_parameter_policy", {}).get(
            "feature_changes_allowed"
        )
        is False,
        "contract_final_holdout": contract.get("protected_final_holdout", {}).get("timerange")
        == EXPECTED_FINAL_HOLDOUT,
        "contract_final_holdout_forbidden": contract.get("protected_final_holdout", {}).get("usage")
        == "forbidden_for_training_tuning_feature_selection_model_selection_model_comparison",
        "selection_policy_id": policy.get("selection_policy_id")
        == "freqai-model-comparison-selection-v1",
        "selection_retuning_forbidden": policy.get("authorization", {}).get("retuning_allowed")
        is False,
        "selection_final_holdout_unused": policy.get("authorization", {}).get("final_holdout_used")
        is False,
        "selection_promotion_forbidden": policy.get("authorization", {}).get("promotion_allowed")
        is False,
        "selection_profitability_claim_forbidden": policy.get("authorization", {}).get(
            "profitability_claim_allowed"
        )
        is False,
        "baseline_download_timerange": baseline.get("download_timerange")
        == EXPECTED_DOWNLOAD_TIMERANGE,
        "declaration_training": declaration.get("training", {}).get("timerange")
        == EXPECTED_TRAINING_WINDOW,
        "declaration_tuning": declaration.get("tuning", {}).get("timerange")
        == EXPECTED_TUNING_WINDOW,
        "declaration_consumed_oos": declaration.get("consumed_holdout_reference", {}).get(
            "timerange"
        )
        == EXPECTED_HISTORICAL_OOS,
        "declaration_consumed_oos_not_unseen": declaration.get(
            "consumed_holdout_reference", {}
        ).get("reusable_as_unseen")
        is False,
        "declaration_final_holdout": declaration.get("final_holdout", {}).get("timerange")
        == EXPECTED_FINAL_HOLDOUT,
        "declaration_final_holdout_unused": declaration.get("final_holdout", {}).get("used")
        is False,
        "declaration_retuning_forbidden": declaration.get("authorization", {}).get(
            "retuning_allowed"
        )
        is False,
        "declaration_final_validation_unauthorized": declaration.get("authorization", {}).get(
            "final_validation_authorized"
        )
        is False,
        "declaration_promotion_forbidden": declaration.get("authorization", {}).get(
            "promotion_allowed"
        )
        is False,
        "declaration_live_forbidden": declaration.get("authorization", {}).get(
            "live_trading_allowed"
        )
        is False,
        "declaration_profitability_claim_forbidden": declaration.get("authorization", {}).get(
            "profitability_claim_allowed"
        )
        is False,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ModelComparisonExecutionRequestError(
            "Frozen Phase 6 historical comparison sources drifted: " + ", ".join(failed)
        )
    return contract, policy, baseline


def expected_execution_request() -> dict[str, Any]:
    """Build the only request payload allowed to trigger the historical comparison workflow."""
    contract, _policy, baseline = _validate_frozen_sources()
    shared = contract["shared_experiment"]
    historical_window = shared["historical_oos_windows"][0]
    return {
        "schema_version": 1,
        "request_id": EXPECTED_REQUEST_ID,
        "execution_mode": "one_shot_historical_model_comparison",
        "comparison_id": contract["comparison_id"],
        "comparison_contract": COMPARISON_CONTRACT.relative_to(REPO_ROOT).as_posix(),
        "comparison_contract_sha256": _sha256(COMPARISON_CONTRACT),
        "selection_policy": SELECTION_POLICY.relative_to(REPO_ROOT).as_posix(),
        "selection_policy_sha256": _sha256(SELECTION_POLICY),
        "models": contract["models"],
        "training_window": shared["training_window"],
        "tuning_window": shared["tuning_window"],
        "historical_oos_timerange": historical_window["timerange"],
        "historical_oos_status": historical_window["unseen_status"],
        "download_timerange": baseline["download_timerange"],
        "protected_final_holdout": EXPECTED_FINAL_HOLDOUT,
        "execution_commit_policy": "pull_request_head_sha",
        "trigger_change_policy": "request_file_only",
        "final_holdout_used": False,
        "retuning_allowed": False,
        "model_parameter_tuning_allowed": False,
        "feature_changes_allowed": False,
        "promotion_allowed": False,
        "live_trading_allowed": False,
        "profitability_claim_allowed": False,
        "unseen_final_evidence_claim_allowed": False,
    }


def validate_execution_request(path: Path = DEFAULT_REQUEST) -> dict[str, Any]:
    """Fail closed unless the supplied request equals the canonical frozen request exactly."""
    actual = _read_json(path.resolve(), "historical comparison execution request")
    expected = expected_execution_request()
    if actual != expected:
        differing = sorted(
            key for key in set(actual) | set(expected) if actual.get(key) != expected.get(key)
        )
        detail = ", ".join(differing) if differing else "unknown difference"
        raise ModelComparisonExecutionRequestError(
            "Historical comparison execution request drifted from the frozen template: " + detail
        )
    return actual


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", nargs="?", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument(
        "--print-template",
        action="store_true",
        help="Print the exact request JSON that a later trigger-only PR must add",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.print_template:
            print(json.dumps(expected_execution_request(), indent=2, sort_keys=True))
            return 0
        request = validate_execution_request(args.request)
    except ModelComparisonExecutionRequestError as exc:
        print(f"Historical comparison execution request invalid: {exc}", file=sys.stderr)
        return 1
    print(request["request_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
