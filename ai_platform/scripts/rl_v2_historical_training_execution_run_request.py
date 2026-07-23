#!/usr/bin/env python3
"""Guard the one-shot RL-v2 historical training/backtest execution request."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REPO_PATH = (
    "ai_platform/experimental_model_research/rl-v2-historical-training-execution-contract-v1.json"
)
CONTRACT_PATH = REPO_ROOT / CONTRACT_REPO_PATH
REQUEST_REPO_PATH = (
    "ai_platform/experimental_model_research/run-requests/"
    "rl-v2-historical-training-execution-v1.json"
)
DESCRIPTOR_REPO_PATH = (
    "ai_platform/experimental_model_research/rl-v2-training-configuration-v1.json"
)
BASE_CONFIG_REPO_PATH = "ai_platform/configs/rl_v2_training_research.json"
MODEL_REPO_PATH = "ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py"
STRATEGY_REPO_PATH = "ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py"
WORKFLOW_REPO_PATH = ".github/workflows/ai-platform-rl-v2-historical-training-execution.yml"
VALIDATOR_REPO_PATH = "ai_platform/scripts/rl_v2_historical_training_execution_run_request.py"
TASK_REPO_PATH = "docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md"

EXPECTED_REQUEST_ID = "rl-v2-historical-training-execution-v1"
EXPECTED_ACTION = "execute_rl_v2_historical_training_backtest"
EXPECTED_TRIGGER = {
    "event": "pull_request_opened",
    "base_branch": "develop",
    "exact_one_file": True,
}
EXPECTED_PARENT = {
    "descriptor_path": DESCRIPTOR_REPO_PATH,
    "configuration_id": "rl-v2-training-configuration-v1",
    "config_path": BASE_CONFIG_REPO_PATH,
    "merge_commit": "da1d5b8abe86ec2ac57dc2293d913fdcf1c286ae",
}
EXPECTED_RUNTIME = {
    "freqai_model": "DesiredPositionReinforcementLearner",
    "freqai_model_path": MODEL_REPO_PATH,
    "strategy": "AiDesiredPositionRLResearchStrategy",
    "strategy_path": STRATEGY_REPO_PATH,
    "backend_family": "stable_baselines3_via_freqai_reinforcement_learner",
    "model_type": "PPO",
    "policy_type": "MlpPolicy",
    "action_space": {"0": "target_flat", "1": "target_long"},
    "action_space_size": 2,
    "long_only": True,
    "transition_reference": (
        "ai_platform.scripts.rl_v2_synthetic_reference.desired_position_transition"
    ),
    "reward_reference": "ai_platform.scripts.rl_v2_synthetic_reference.reference_reward",
    "reward_constants_source": "ai_platform.scripts.rl_v2_synthetic_reference.REWARD_REFERENCE",
}
EXPECTED_EXECUTION = {
    "mode": "one_shot_trigger_pr",
    "executions": 1,
    "download_timerange": "20250801-20260501",
    "execution_timerange": "20260301-20260501",
    "semantic_evidence_window": "20260301-20260430",
    "freqtrade_stop_semantics": "end_exclusive",
    "train_period_days": 90,
    "backtest_period_days": 61,
    "live_retrain_hours_present": False,
}
EXPECTED_MATERIALIZATION = {
    "base_config_immutable": True,
    "temporary_runtime_config": True,
    "allowed_added_freqai_keys": {
        "train_period_days": 90,
        "backtest_period_days": 61,
    },
    "timerange_added_to_config": False,
    "live_retrain_hours_added": False,
}
EXPECTED_MARKET_DATA = {
    "exchange": "kraken",
    "pairs": ["BTC/USDT", "ETH/USDT"],
    "timeframes": ["15m", "1h", "4h"],
    "fee": 0.002,
    "verification_module": "ai_platform.scripts.rl_v2_historical_training_execution_run_request",
    "cache_namespace": "rl-v2-historical-training-pre-oos-v1",
    "restore_from_post_20260501_cache_allowed": False,
}
EXPECTED_EVIDENCE = {
    "classification": "historical_development_evidence",
    "strict_oos": False,
    "protected_final_validation": False,
    "automatic_ranking": False,
    "automatic_promotion": False,
    "negative_or_zero_trade_result_is_valid_evidence": True,
}
EXPECTED_ISOLATION = {
    "consumed_historical_oos": {
        "timerange": "20260501-20260630",
        "start_inclusive": "2026-05-01T00:00:00Z",
        "usage": "forbidden",
    },
    "protected_final_holdout": {
        "timerange": "20260801-20260930",
        "usage": "forbidden",
    },
    "frozen_entry_prediction_threshold": 0.006,
    "frozen_exit_prediction_threshold": -0.009,
    "thresholds_used_for_rl_tuning": False,
    "phase6_authoritative_selected_model": None,
    "phase6_member": False,
    "pytorch_rl_ranking_allowed": False,
}
EXPECTED_AUTHORIZATION = {
    "infrastructure_merge_executes_model": False,
    "canonical_request_required": True,
    "historical_training_execution_allowed_after_canonical_request": True,
    "historical_backtest_allowed_after_canonical_request": True,
    "market_data_download_allowed_after_canonical_request": True,
    "strict_oos_scoring_allowed": False,
    "consumed_historical_oos_access_allowed": False,
    "protected_final_holdout_access_allowed": False,
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
TIMEFRAME_SECONDS = {"15m": 15 * 60, "1h": 60 * 60, "4h": 4 * 60 * 60}
FORBIDDEN_BASE_CONFIG_KEYS = {
    "timerange",
    "train_period_days",
    "backtest_period_days",
    "live_retrain_hours",
}


class RLV2HistoricalTrainingExecutionError(RuntimeError):
    """Raised when the RL-v2 execution contract or request drifts."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RLV2HistoricalTrainingExecutionError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RLV2HistoricalTrainingExecutionError(f"{label} must contain a JSON object")
    return payload


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise RLV2HistoricalTrainingExecutionError(
            f"Unable to hash canonical input {path}: {exc}"
        ) from exc


def _repo_path(value: str) -> Path:
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise RLV2HistoricalTrainingExecutionError(
            f"Canonical path escapes repository root: {value}"
        ) from exc
    return candidate


def _date_token(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d").replace(tzinfo=UTC)


def _split_timerange(value: str) -> tuple[str, str]:
    try:
        start, stop = value.split("-", maxsplit=1)
    except ValueError as exc:
        raise RLV2HistoricalTrainingExecutionError(
            f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}"
        ) from exc
    if len(start) != 8 or len(stop) != 8:
        raise RLV2HistoricalTrainingExecutionError(
            f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}"
        )
    return start, stop


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, list):
        list_keys: set[str] = set()
        for child in value:
            list_keys.update(_collect_keys(child))
        return list_keys
    return set()


def _validate_temporal_boundaries() -> None:
    download_start, download_stop = _split_timerange(EXPECTED_EXECUTION["download_timerange"])
    execution_start, execution_stop = _split_timerange(EXPECTED_EXECUTION["execution_timerange"])
    evidence_start, evidence_end_inclusive = _split_timerange(
        EXPECTED_EXECUTION["semantic_evidence_window"]
    )
    consumed_start = _date_token("20260501")

    if _date_token(download_stop) > consumed_start or _date_token(execution_stop) > consumed_start:
        raise RLV2HistoricalTrainingExecutionError(
            "RL-v2 historical execution geometry crosses into consumed May-June OOS"
        )
    if download_stop != "20260501" or execution_stop != "20260501":
        raise RLV2HistoricalTrainingExecutionError(
            "RL-v2 historical data and execution must stop at exclusive 2026-05-01"
        )
    if evidence_start != execution_start:
        raise RLV2HistoricalTrainingExecutionError("Historical evidence start drifted")
    expected_stop = (_date_token(evidence_end_inclusive) + timedelta(days=1)).strftime("%Y%m%d")
    if execution_stop != expected_stop:
        raise RLV2HistoricalTrainingExecutionError(
            f"Historical evidence inclusive end must map to exclusive stop {expected_stop}"
        )
    execution_days = (_date_token(execution_stop) - _date_token(execution_start)).days
    if execution_days != EXPECTED_EXECUTION["backtest_period_days"]:
        raise RLV2HistoricalTrainingExecutionError(
            "Execution window length must equal frozen backtest_period_days"
        )
    if _date_token(download_start) >= _date_token(execution_start):
        raise RLV2HistoricalTrainingExecutionError(
            "Download history must begin before the historical execution window"
        )


def _validate_contract() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:  # noqa: C901
    contract = _read_json(CONTRACT_PATH, "RL-v2 historical training execution contract")
    if contract.get("schema_version") != 1:
        raise RLV2HistoricalTrainingExecutionError("Execution contract schema_version must be 1")
    if contract.get("contract_id") != EXPECTED_REQUEST_ID:
        raise RLV2HistoricalTrainingExecutionError("Execution contract_id drifted")
    if contract.get("task") != TASK_REPO_PATH:
        raise RLV2HistoricalTrainingExecutionError("Execution task path drifted")
    if contract.get("task_declaration_merge") != "c663626ea8581fe82c107f959873d8c260927881":
        raise RLV2HistoricalTrainingExecutionError("Execution task declaration merge drifted")
    if contract.get("request_path") != REQUEST_REPO_PATH:
        raise RLV2HistoricalTrainingExecutionError("Canonical request path drifted")

    expected_sections = {
        "trigger": EXPECTED_TRIGGER,
        "parent_training_configuration": EXPECTED_PARENT,
        "runtime_binding": EXPECTED_RUNTIME,
        "execution_geometry": EXPECTED_EXECUTION,
        "configuration_materialization": EXPECTED_MATERIALIZATION,
        "market_data": EXPECTED_MARKET_DATA,
        "evidence": EXPECTED_EVIDENCE,
        "isolation": EXPECTED_ISOLATION,
        "authorization": EXPECTED_AUTHORIZATION,
    }
    for field, expected in expected_sections.items():
        if contract.get(field) != expected:
            raise RLV2HistoricalTrainingExecutionError(f"Execution contract field {field} drifted")

    _validate_temporal_boundaries()

    descriptor_path = _repo_path(DESCRIPTOR_REPO_PATH)
    base_config_path = _repo_path(BASE_CONFIG_REPO_PATH)
    model_path = _repo_path(MODEL_REPO_PATH)
    strategy_path = _repo_path(STRATEGY_REPO_PATH)
    for path, label in (
        (descriptor_path, "training configuration descriptor"),
        (base_config_path, "base training config"),
        (model_path, "FreqAI model"),
        (strategy_path, "strategy"),
    ):
        if not path.is_file():
            raise RLV2HistoricalTrainingExecutionError(f"Canonical {label} is missing: {path}")

    descriptor = _read_json(descriptor_path, "RL-v2 training configuration descriptor")
    base_config = _read_json(base_config_path, "RL-v2 base training config")
    if descriptor.get("configuration_id") != EXPECTED_PARENT["configuration_id"]:
        raise RLV2HistoricalTrainingExecutionError("Training configuration identity drifted")
    if descriptor.get("config_path") != BASE_CONFIG_REPO_PATH:
        raise RLV2HistoricalTrainingExecutionError("Training config path binding drifted")
    if (
        descriptor.get("runtime_binding", {}).get("freqai_model")
        != EXPECTED_RUNTIME["freqai_model"]
    ):
        raise RLV2HistoricalTrainingExecutionError("Descriptor FreqAI model binding drifted")
    if descriptor.get("runtime_binding", {}).get("strategy") != EXPECTED_RUNTIME["strategy"]:
        raise RLV2HistoricalTrainingExecutionError("Descriptor strategy binding drifted")
    if descriptor.get("runtime_binding", {}).get("model_type") != EXPECTED_RUNTIME["model_type"]:
        raise RLV2HistoricalTrainingExecutionError("Descriptor PPO binding drifted")
    if descriptor.get("runtime_binding", {}).get("policy_type") != EXPECTED_RUNTIME["policy_type"]:
        raise RLV2HistoricalTrainingExecutionError("Descriptor policy binding drifted")
    if (
        descriptor.get("semantic_binding", {}).get("action_space")
        != EXPECTED_RUNTIME["action_space"]
    ):
        raise RLV2HistoricalTrainingExecutionError(
            "Descriptor desired-position action space drifted"
        )
    if (
        descriptor.get("isolation", {}).get("consumed_historical_oos", {}).get("usage")
        != "forbidden"
    ):
        raise RLV2HistoricalTrainingExecutionError("Consumed historical OOS isolation drifted")
    if (
        descriptor.get("isolation", {}).get("protected_final_holdout", {}).get("usage")
        != "forbidden"
    ):
        raise RLV2HistoricalTrainingExecutionError("Protected final holdout isolation drifted")

    if FORBIDDEN_BASE_CONFIG_KEYS.intersection(_collect_keys(base_config)):
        raise RLV2HistoricalTrainingExecutionError(
            "Base RL-v2 training config must remain free of execution geometry"
        )
    if base_config.get("dry_run") is not True or base_config.get("trading_mode") != "spot":
        raise RLV2HistoricalTrainingExecutionError("Base RL-v2 config safety posture drifted")
    if base_config.get("initial_state") != "stopped":
        raise RLV2HistoricalTrainingExecutionError("Base RL-v2 config must remain stopped")
    if base_config.get("freqaimodel") != EXPECTED_RUNTIME["freqai_model"]:
        raise RLV2HistoricalTrainingExecutionError("Base config FreqAI model drifted")
    if base_config.get("strategy") != EXPECTED_RUNTIME["strategy"]:
        raise RLV2HistoricalTrainingExecutionError("Base config strategy drifted")
    if base_config.get("exchange", {}).get("name", "").lower() != EXPECTED_MARKET_DATA["exchange"]:
        raise RLV2HistoricalTrainingExecutionError("Base config exchange drifted")
    if base_config.get("exchange", {}).get("pair_whitelist") != EXPECTED_MARKET_DATA["pairs"]:
        raise RLV2HistoricalTrainingExecutionError("Base config pair whitelist drifted")
    if base_config.get("exchange", {}).get("key") or base_config.get("exchange", {}).get("secret"):
        raise RLV2HistoricalTrainingExecutionError(
            "Base config must not contain exchange credentials"
        )
    rl_config = base_config.get("freqai", {}).get("rl_config", {})
    if rl_config.get("model_type") != "PPO" or rl_config.get("policy_type") != "MlpPolicy":
        raise RLV2HistoricalTrainingExecutionError("Base config PPO/MlpPolicy binding drifted")
    if rl_config.get("model_reward_parameters") != {}:
        raise RLV2HistoricalTrainingExecutionError(
            "Base config must not redefine reward parameters"
        )

    return contract, descriptor, base_config


def canonical_rl_v2_historical_training_execution_request() -> dict[str, Any]:
    """Return the only request payload authorized by the one-shot RL-v2 workflow."""
    contract, _, _ = _validate_contract()
    descriptor_path = _repo_path(DESCRIPTOR_REPO_PATH)
    base_config_path = _repo_path(BASE_CONFIG_REPO_PATH)
    model_path = _repo_path(MODEL_REPO_PATH)
    strategy_path = _repo_path(STRATEGY_REPO_PATH)
    workflow_path = _repo_path(WORKFLOW_REPO_PATH)
    validator_path = _repo_path(VALIDATOR_REPO_PATH)
    for path, label in ((workflow_path, "workflow"), (validator_path, "request validator")):
        if not path.is_file():
            raise RLV2HistoricalTrainingExecutionError(f"Canonical {label} is missing: {path}")

    return {
        "schema_version": 1,
        "request_id": EXPECTED_REQUEST_ID,
        "action": EXPECTED_ACTION,
        "contract_path": CONTRACT_REPO_PATH,
        "contract_sha256": _sha256(CONTRACT_PATH),
        "training_configuration_descriptor_path": DESCRIPTOR_REPO_PATH,
        "training_configuration_descriptor_sha256": _sha256(descriptor_path),
        "config_path": BASE_CONFIG_REPO_PATH,
        "config_sha256": _sha256(base_config_path),
        "freqai_model": EXPECTED_RUNTIME["freqai_model"],
        "freqai_model_path": MODEL_REPO_PATH,
        "freqai_model_sha256": _sha256(model_path),
        "strategy": EXPECTED_RUNTIME["strategy"],
        "strategy_path": STRATEGY_REPO_PATH,
        "strategy_sha256": _sha256(strategy_path),
        "validator_path": VALIDATOR_REPO_PATH,
        "validator_sha256": _sha256(validator_path),
        "workflow_path": WORKFLOW_REPO_PATH,
        "workflow_sha256": _sha256(workflow_path),
        "download_timerange": EXPECTED_EXECUTION["download_timerange"],
        "execution_timerange": EXPECTED_EXECUTION["execution_timerange"],
        "semantic_evidence_window": EXPECTED_EXECUTION["semantic_evidence_window"],
        "train_period_days": EXPECTED_EXECUTION["train_period_days"],
        "backtest_period_days": EXPECTED_EXECUTION["backtest_period_days"],
        "pairs": list(EXPECTED_MARKET_DATA["pairs"]),
        "timeframes": list(EXPECTED_MARKET_DATA["timeframes"]),
        "fee": EXPECTED_MARKET_DATA["fee"],
        "evidence_classification": EXPECTED_EVIDENCE["classification"],
        "strict_oos": False,
        "consumed_historical_oos": EXPECTED_ISOLATION["consumed_historical_oos"]["timerange"],
        "protected_final_holdout": EXPECTED_ISOLATION["protected_final_holdout"]["timerange"],
        "authorization": dict(contract["authorization"]),
    }


def load_rl_v2_historical_training_execution_request(path: Path) -> dict[str, Any]:
    """Load and fail closed unless a request exactly matches the canonical payload."""
    request = _read_json(path.resolve(), "RL-v2 historical training execution request")
    expected = canonical_rl_v2_historical_training_execution_request()
    if set(request) != set(expected):
        missing = sorted(set(expected) - set(request))
        extra = sorted(set(request) - set(expected))
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if extra:
            details.append(f"extra={','.join(extra)}")
        raise RLV2HistoricalTrainingExecutionError(
            "Run request fields do not match the canonical RL-v2 execution request: "
            + "; ".join(details)
        )
    for field, expected_value in expected.items():
        if request[field] != expected_value:
            raise RLV2HistoricalTrainingExecutionError(
                f"Run request field {field} drifted from the canonical RL-v2 execution request"
            )
    return request


def materialize_runtime_config(output: Path) -> Path:
    """Write the only temporary execution config allowed by the frozen contract."""
    _, _, base_config = _validate_contract()
    output = output.resolve()
    if output == _repo_path(BASE_CONFIG_REPO_PATH):
        raise RLV2HistoricalTrainingExecutionError(
            "Refusing to overwrite the immutable base config"
        )

    runtime_config = deepcopy(base_config)
    freqai = runtime_config.setdefault("freqai", {})
    freqai["train_period_days"] = EXPECTED_EXECUTION["train_period_days"]
    freqai["backtest_period_days"] = EXPECTED_EXECUTION["backtest_period_days"]
    if "timerange" in runtime_config or "live_retrain_hours" in freqai:
        raise RLV2HistoricalTrainingExecutionError(
            "Temporary runtime config introduced unauthorized execution geometry"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(runtime_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def verify_downloaded_data(datadir: Path, *, pairs: list[str] | None = None) -> dict[str, Any]:
    """Verify pre-May pair/timeframe coverage without scoring or model execution."""
    from freqtrade.configuration import TimeRange
    from freqtrade.data.history.history_utils import load_pair_history

    _validate_contract()
    selected_pairs = pairs or EXPECTED_MARKET_DATA["pairs"]
    if not selected_pairs or any(
        pair not in EXPECTED_MARKET_DATA["pairs"] for pair in selected_pairs
    ):
        raise RLV2HistoricalTrainingExecutionError("Data verification requested an unknown pair")

    timerange = TimeRange.parse_timerange(EXPECTED_EXECUTION["download_timerange"])
    startdt = timerange.startdt
    stopdt = timerange.stopdt
    if startdt is None or stopdt is None:
        raise RLV2HistoricalTrainingExecutionError("Expected a bounded download timerange")
    if stopdt != _date_token("20260501"):
        raise RLV2HistoricalTrainingExecutionError(
            "Freqtrade parser did not preserve the exclusive 2026-05-01 stop boundary"
        )

    coverage: dict[str, dict[str, str | int]] = {}
    for pair in selected_pairs:
        for timeframe in EXPECTED_MARKET_DATA["timeframes"]:
            frame = load_pair_history(
                pair=pair,
                timeframe=timeframe,
                datadir=datadir,
                timerange=timerange,
                fill_up_missing=False,
                drop_incomplete=False,
            )
            if frame.empty:
                raise RLV2HistoricalTrainingExecutionError(
                    f"No downloaded data for {pair} {timeframe}"
                )
            first_date = frame["date"].min().to_pydatetime()
            last_date = frame["date"].max().to_pydatetime()
            if first_date > startdt:
                raise RLV2HistoricalTrainingExecutionError(
                    "Downloaded data starts too late for "
                    f"{pair} {timeframe}: {first_date.isoformat()}"
                )
            minimum_last_ts = timerange.stopts - TIMEFRAME_SECONDS[timeframe]
            if int(last_date.timestamp()) < minimum_last_ts:
                raise RLV2HistoricalTrainingExecutionError(
                    "Downloaded data ends too early for "
                    f"{pair} {timeframe}: {last_date.isoformat()}"
                )
            coverage[f"{pair}:{timeframe}"] = {
                "rows": len(frame),
                "first": first_date.isoformat(),
                "last": last_date.isoformat(),
            }

    return {
        "schema_version": 1,
        "verification_id": "rl-v2-historical-training-pre-oos-data-v1",
        "status": "ready",
        "download_timerange": EXPECTED_EXECUTION["download_timerange"],
        "stop_exclusive": "2026-05-01T00:00:00+00:00",
        "consumed_historical_oos_accessed": False,
        "protected_final_holdout_accessed": False,
        "verified_pairs": selected_pairs,
        "timeframes": EXPECTED_MARKET_DATA["timeframes"],
        "coverage": coverage,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "request",
        nargs="?",
        type=Path,
        help="Path to the one-shot RL-v2 historical execution request JSON",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--print-canonical",
        action="store_true",
        help="Print the exact request payload that a separate trigger PR must add",
    )
    mode.add_argument(
        "--materialize-config",
        type=Path,
        help="Write the frozen temporary runtime config without executing a model",
    )
    mode.add_argument(
        "--verify-data",
        type=Path,
        metavar="DATADIR",
        help="Verify exact pre-May market-data coverage",
    )
    parser.add_argument(
        "--pair",
        action="append",
        choices=EXPECTED_MARKET_DATA["pairs"],
        dest="pairs",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.print_canonical:
            if args.request is not None:
                raise RLV2HistoricalTrainingExecutionError(
                    "Do not pass a request path with --print-canonical"
                )
            print(
                json.dumps(
                    canonical_rl_v2_historical_training_execution_request(),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.materialize_config is not None:
            if args.request is not None:
                raise RLV2HistoricalTrainingExecutionError(
                    "Do not pass a request path with --materialize-config"
                )
            print(materialize_runtime_config(args.materialize_config))
            return 0
        if args.verify_data is not None:
            if args.request is not None:
                raise RLV2HistoricalTrainingExecutionError(
                    "Do not pass a request path with --verify-data"
                )
            print(
                json.dumps(
                    verify_downloaded_data(args.verify_data, pairs=args.pairs),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.request is None:
            raise RLV2HistoricalTrainingExecutionError(
                "A request path is required unless an explicit validation mode is selected"
            )
        request = load_rl_v2_historical_training_execution_request(args.request)
    except RLV2HistoricalTrainingExecutionError as exc:
        print(f"RL-v2 historical training execution invalid: {exc}", file=sys.stderr)
        return 1
    print(request["request_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
