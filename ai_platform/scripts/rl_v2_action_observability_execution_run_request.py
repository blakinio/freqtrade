#!/usr/bin/env python3
"""Guard the request-gated RL-v2 action-observability execution."""

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
    "ai_platform/experimental_model_research/rl-v2-action-observability-execution-contract-v1.json"
)
DECLARATION_REPO_PATH = (
    "ai_platform/experimental_model_research/"
    "rl-v2-action-observability-execution-declaration-v1.json"
)
REQUEST_REPO_PATH = (
    "ai_platform/experimental_model_research/run-requests/"
    "rl-v2-action-observability-execution-v1.json"
)
BASE_CONFIG_REPO_PATH = "ai_platform/configs/rl_v2_training_research.json"
MODEL_REPO_PATH = "ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py"
PARENT_STRATEGY_REPO_PATH = (
    "ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py"
)
OBSERVABLE_STRATEGY_REPO_PATH = (
    "ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy.py"
)
RECORDER_REPO_PATH = "ai_platform/scripts/rl_v2_action_observability.py"
VALIDATOR_REPO_PATH = "ai_platform/scripts/rl_v2_action_observability_execution_run_request.py"
EVIDENCE_REPO_PATH = "ai_platform/scripts/rl_v2_action_observability_execution_evidence.py"
WORKFLOW_REPO_PATH = ".github/workflows/ai-platform-rl-v2-action-observability-execution.yml"
INFRA_TASK_REPO_PATH = (
    "docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-infrastructure.md"
)
EXECUTION_TASK_REPO_PATH = "docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md"

EXPECTED_CONTRACT_ID = "rl-v2-action-observability-execution-v1"
EXPECTED_REQUEST_ID = EXPECTED_CONTRACT_ID
EXPECTED_ACTION = "execute_rl_v2_action_observability"
EXPECTED_DECLARATION_MERGE = "b8e3fa1b946a5fb6e14a8ccccb1d96a8cbbd2787"
EXPECTED_DECLARATION_CLOSURE_MERGE = "c04725708fbc229a71cb0bd4217a131959181d01"
EXPECTED_INFRA_TASK_MERGE = "76e13f37588c766c73e12543885aadf86bdcbb15"
EXPECTED_CONFIG_SHA256 = "5adc805deadcfe6dc3c52d0745f62546952a96b38b3bd06bc28ac9987063f6de"
EXPECTED_MODEL_SHA256 = "3cec25cc7b43e3214a8e22d153107307a7a7bfbfd48b6bf313ecb4624cb79d46"
EXPECTED_PARENT_STRATEGY_SHA256 = "366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7"
NEW_SEEDS = (271828182, 628318530, 1414213562, 1618033988)
EXPECTED_CLASSIFICATION = "fresh_historical_development_action_observability"
RUNTIME_IDENTIFIER_TEMPLATE = "rl-v2-action-observability-fresh-v1-seed-{seed}"
EXPECTED_GEOMETRY: dict[str, Any] = {
    "mode": "four_new_seed_action_observability_matrix",
    "download_timerange": "20250601-20251101",
    "execution_timerange": "20250901-20251101",
    "semantic_evidence_window": "20250901-20251031",
    "freqtrade_stop_semantics": "end_exclusive",
    "train_period_days": 90,
    "backtest_period_days": 61,
    "exchange": "kraken",
    "pairs": ["BTC/USDT", "ETH/USDT"],
    "timeframes": ["15m", "1h", "4h"],
    "fee": 0.002,
    "cache_restore_allowed": False,
}
TIMEFRAME_SECONDS = {"15m": 15 * 60, "1h": 60 * 60, "4h": 4 * 60 * 60}
FORBIDDEN_CONFIG_KEYS = {"timerange", "train_period_days", "backtest_period_days"}


class RLV2ActionObservabilityExecutionError(RuntimeError):
    """Raised when action-observability infrastructure or a request drifts."""


def _repo_path(value: str) -> Path:
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise RLV2ActionObservabilityExecutionError(
            f"Canonical path escapes repository root: {value}"
        ) from exc
    return candidate


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RLV2ActionObservabilityExecutionError(
            f"Unable to read {label} {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RLV2ActionObservabilityExecutionError(f"{label} must be a JSON object")
    return payload


def _sha256(path: Path) -> str:
    try:
        content = path.read_bytes().replace(b"\r\n", b"\n")
    except OSError as exc:
        raise RLV2ActionObservabilityExecutionError(
            f"Unable to hash canonical input {path}: {exc}"
        ) from exc
    return hashlib.sha256(content).hexdigest()


def _require_sha(path: str, expected: str, label: str) -> None:
    actual = _sha256(_repo_path(path))
    if actual != expected:
        raise RLV2ActionObservabilityExecutionError(
            f"{label} SHA-256 drifted: expected {expected}, got {actual}"
        )


def _date_token(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d").replace(tzinfo=UTC)


def _split_timerange(value: str) -> tuple[str, str]:
    try:
        start, stop = value.split("-", maxsplit=1)
    except ValueError as exc:
        raise RLV2ActionObservabilityExecutionError(
            f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}"
        ) from exc
    if len(start) != 8 or len(stop) != 8:
        raise RLV2ActionObservabilityExecutionError(
            f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}"
        )
    _date_token(start)
    _date_token(stop)
    return start, stop


def runtime_identifier(seed: int) -> str:
    """Return the only isolated identifier allowed for a declared seed."""
    validate_seed(seed)
    return RUNTIME_IDENTIFIER_TEMPLATE.format(seed=seed)


def validate_seed(seed: int) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise RLV2ActionObservabilityExecutionError("Seed must be an integer")
    if seed not in NEW_SEEDS:
        raise RLV2ActionObservabilityExecutionError(
            f"Seed is outside the frozen execution set: {seed}"
        )


def _validate_temporal_boundaries() -> None:
    download_start, download_stop = _split_timerange(EXPECTED_GEOMETRY["download_timerange"])
    execution_start, execution_stop = _split_timerange(EXPECTED_GEOMETRY["execution_timerange"])
    evidence_start, evidence_end = _split_timerange(EXPECTED_GEOMETRY["semantic_evidence_window"])
    if evidence_start != execution_start:
        raise RLV2ActionObservabilityExecutionError("Semantic evidence start drifted")
    expected_stop = (_date_token(evidence_end) + timedelta(days=1)).strftime("%Y%m%d")
    if expected_stop != execution_stop:
        raise RLV2ActionObservabilityExecutionError(
            "Semantic evidence end does not map to exclusive execution stop"
        )
    execution_days = (_date_token(execution_stop) - _date_token(execution_start)).days
    if execution_days != EXPECTED_GEOMETRY["backtest_period_days"]:
        raise RLV2ActionObservabilityExecutionError("Backtest period drifted")
    minimum_history_start = _date_token(execution_start) - timedelta(
        days=EXPECTED_GEOMETRY["train_period_days"]
    )
    if _date_token(download_start) > minimum_history_start:
        raise RLV2ActionObservabilityExecutionError(
            "Download range does not cover the frozen training period"
        )
    if download_stop != execution_stop:
        raise RLV2ActionObservabilityExecutionError("Fresh download and execution stops must match")
    consumed_start = _date_token("20260501")
    if _date_token(download_stop) >= consumed_start:
        raise RLV2ActionObservabilityExecutionError(
            "Fresh geometry approaches or crosses consumed OOS"
        )


def _validate_declaration() -> dict[str, Any]:
    declaration = _read_json(_repo_path(DECLARATION_REPO_PATH), "execution declaration")
    if declaration.get("schema_version") != 1:
        raise RLV2ActionObservabilityExecutionError("Declaration schema drifted")
    if declaration.get("declaration_id") != ("rl-v2-action-observability-execution-declaration-v1"):
        raise RLV2ActionObservabilityExecutionError("Declaration id drifted")
    if declaration.get("status") != "declared_not_implemented_or_executed":
        raise RLV2ActionObservabilityExecutionError("Declaration status drifted")
    if declaration.get("fresh_window") != {
        "download_timerange": "20250601-20251101",
        "execution_timerange": "20250901-20251101",
        "semantic_evidence_window": "20250901-20251031",
        "freqtrade_stop_semantics": "end_exclusive",
        "train_period_days": 90,
        "backtest_period_days": 61,
        "previously_consumed_by_rl_v2_execution": False,
        "cache_restore_allowed": False,
    }:
        raise RLV2ActionObservabilityExecutionError("Fresh-window declaration drifted")
    runtime = declaration.get("runtime", {})
    if runtime.get("seeds") != list(NEW_SEEDS):
        raise RLV2ActionObservabilityExecutionError("Declared seed set drifted")
    if runtime.get("identifier_template") != RUNTIME_IDENTIFIER_TEMPLATE:
        raise RLV2ActionObservabilityExecutionError("Identifier template drifted")
    isolation = declaration.get("isolation", {})
    if isolation.get("classification") != EXPECTED_CLASSIFICATION:
        raise RLV2ActionObservabilityExecutionError("Evidence classification drifted")
    if isolation.get("phase6_authoritative_selected_model") is not None:
        raise RLV2ActionObservabilityExecutionError("Phase 6 selected_model drifted")
    return declaration


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()


def _validate_contract(  # noqa: C901
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = _read_json(_repo_path(CONTRACT_REPO_PATH), "execution contract")
    if contract.get("schema_version") != 1:
        raise RLV2ActionObservabilityExecutionError("Contract schema_version drifted")
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise RLV2ActionObservabilityExecutionError("Contract id drifted")
    if contract.get("infrastructure_task") != INFRA_TASK_REPO_PATH:
        raise RLV2ActionObservabilityExecutionError("Infrastructure task path drifted")
    if contract.get("infrastructure_task_merge") != EXPECTED_INFRA_TASK_MERGE:
        raise RLV2ActionObservabilityExecutionError("Infrastructure task merge drifted")
    if contract.get("execution_task") != EXECUTION_TASK_REPO_PATH:
        raise RLV2ActionObservabilityExecutionError("Execution task path drifted")
    if contract.get("declaration_path") != DECLARATION_REPO_PATH:
        raise RLV2ActionObservabilityExecutionError("Declaration path drifted")
    if contract.get("declaration_merge") != EXPECTED_DECLARATION_MERGE:
        raise RLV2ActionObservabilityExecutionError("Declaration merge drifted")
    if contract.get("declaration_closure_merge") != EXPECTED_DECLARATION_CLOSURE_MERGE:
        raise RLV2ActionObservabilityExecutionError("Declaration closure merge drifted")
    if contract.get("request_path") != REQUEST_REPO_PATH:
        raise RLV2ActionObservabilityExecutionError("Request path drifted")
    if contract.get("trigger") != {
        "event": "pull_request_opened",
        "base_branch": "develop",
        "exact_one_file": True,
    }:
        raise RLV2ActionObservabilityExecutionError("Request trigger drifted")

    runtime = contract.get("runtime_binding", {})
    expected_runtime = {
        "freqai_model": "DesiredPositionReinforcementLearner",
        "freqai_model_path": MODEL_REPO_PATH,
        "freqai_model_sha256": EXPECTED_MODEL_SHA256,
        "parent_strategy": "AiDesiredPositionRLLifecycleAlignedResearchStrategy",
        "parent_strategy_path": PARENT_STRATEGY_REPO_PATH,
        "parent_strategy_sha256": EXPECTED_PARENT_STRATEGY_SHA256,
        "observable_strategy": ("AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy"),
        "observable_strategy_path": OBSERVABLE_STRATEGY_REPO_PATH,
        "recorder_path": RECORDER_REPO_PATH,
        "base_config_path": BASE_CONFIG_REPO_PATH,
        "base_config_sha256": EXPECTED_CONFIG_SHA256,
        "model_type": "PPO",
        "policy_type": "MlpPolicy",
        "n_steps": 128,
        "batch_size": 64,
        "data_split_random_state": 42,
        "data_split_shuffle": False,
        "only_strategy_delta": (
            "disabled-by-default action telemetry after inherited exit-signal evaluation"
        ),
        "runtime_identifier_template": RUNTIME_IDENTIFIER_TEMPLATE,
    }
    if runtime != expected_runtime:
        raise RLV2ActionObservabilityExecutionError("Runtime binding drifted")

    if contract.get("seed_matrix") != {
        "ordered_execution_seeds": list(NEW_SEEDS),
        "execution_count": 4,
        "prior_seed_executions": 0,
        "baseline_executions": 0,
        "outcome_aware_replacement_allowed": False,
    }:
        raise RLV2ActionObservabilityExecutionError("Seed matrix drifted")
    if contract.get("execution_geometry") != EXPECTED_GEOMETRY:
        raise RLV2ActionObservabilityExecutionError("Execution geometry drifted")

    authorization = contract.get("authorization", {})
    required_true = {
        "canonical_request_required",
        "execution_task_required_before_trigger",
        "four_seed_training_backtests_allowed_after_canonical_request",
        "market_data_download_allowed_after_canonical_request",
    }
    required_false = set(authorization) - required_true
    if any(authorization.get(field) is not True for field in required_true):
        raise RLV2ActionObservabilityExecutionError("Required authorization drifted")
    if any(authorization.get(field) is not False for field in required_false):
        raise RLV2ActionObservabilityExecutionError("Forbidden authorization drifted")

    _validate_temporal_boundaries()
    _require_sha(BASE_CONFIG_REPO_PATH, EXPECTED_CONFIG_SHA256, "Base config")
    _require_sha(MODEL_REPO_PATH, EXPECTED_MODEL_SHA256, "FreqAI model")
    _require_sha(
        PARENT_STRATEGY_REPO_PATH,
        EXPECTED_PARENT_STRATEGY_SHA256,
        "Parent lifecycle strategy",
    )

    base_config = _read_json(_repo_path(BASE_CONFIG_REPO_PATH), "base config")
    if FORBIDDEN_CONFIG_KEYS.intersection(_collect_keys(base_config)):
        raise RLV2ActionObservabilityExecutionError(
            "Base config must remain free of execution geometry"
        )
    if base_config.get("dry_run") is not True:
        raise RLV2ActionObservabilityExecutionError("Base config dry_run drifted")
    if base_config.get("initial_state") != "stopped":
        raise RLV2ActionObservabilityExecutionError("Base initial_state drifted")
    if base_config.get("trading_mode") != "spot":
        raise RLV2ActionObservabilityExecutionError("Base trading mode drifted")
    freqai = base_config.get("freqai", {})
    if freqai.get("data_split_parameters") != {
        "test_size": 0.2,
        "random_state": 42,
        "shuffle": False,
    }:
        raise RLV2ActionObservabilityExecutionError("Data split drifted")
    if freqai.get("model_training_parameters") != {
        "seed": 42,
        "n_steps": 128,
        "batch_size": 64,
    }:
        raise RLV2ActionObservabilityExecutionError("Training parameters drifted")
    declaration = _validate_declaration()
    return contract, declaration, base_config


def canonical_request() -> dict[str, Any]:
    """Return the only payload authorized for a later trigger PR."""
    contract, declaration, _ = _validate_contract()
    inputs = {
        "contract": CONTRACT_REPO_PATH,
        "declaration": DECLARATION_REPO_PATH,
        "config": BASE_CONFIG_REPO_PATH,
        "freqai_model": MODEL_REPO_PATH,
        "parent_strategy": PARENT_STRATEGY_REPO_PATH,
        "observable_strategy": OBSERVABLE_STRATEGY_REPO_PATH,
        "recorder": RECORDER_REPO_PATH,
        "validator": VALIDATOR_REPO_PATH,
        "evidence": EVIDENCE_REPO_PATH,
        "workflow": WORKFLOW_REPO_PATH,
    }
    for label, path in inputs.items():
        if not _repo_path(path).is_file():
            raise RLV2ActionObservabilityExecutionError(
                f"Canonical {label} input is missing: {path}"
            )
    return {
        "schema_version": 1,
        "request_id": EXPECTED_REQUEST_ID,
        "action": EXPECTED_ACTION,
        "contract_path": CONTRACT_REPO_PATH,
        "contract_sha256": _sha256(_repo_path(CONTRACT_REPO_PATH)),
        "declaration_path": DECLARATION_REPO_PATH,
        "declaration_sha256": _sha256(_repo_path(DECLARATION_REPO_PATH)),
        "config_path": BASE_CONFIG_REPO_PATH,
        "config_sha256": _sha256(_repo_path(BASE_CONFIG_REPO_PATH)),
        "freqai_model": contract["runtime_binding"]["freqai_model"],
        "freqai_model_path": MODEL_REPO_PATH,
        "freqai_model_sha256": _sha256(_repo_path(MODEL_REPO_PATH)),
        "parent_strategy_path": PARENT_STRATEGY_REPO_PATH,
        "parent_strategy_sha256": _sha256(_repo_path(PARENT_STRATEGY_REPO_PATH)),
        "strategy": contract["runtime_binding"]["observable_strategy"],
        "strategy_path": OBSERVABLE_STRATEGY_REPO_PATH,
        "strategy_sha256": _sha256(_repo_path(OBSERVABLE_STRATEGY_REPO_PATH)),
        "recorder_path": RECORDER_REPO_PATH,
        "recorder_sha256": _sha256(_repo_path(RECORDER_REPO_PATH)),
        "validator_path": VALIDATOR_REPO_PATH,
        "validator_sha256": _sha256(_repo_path(VALIDATOR_REPO_PATH)),
        "evidence_path": EVIDENCE_REPO_PATH,
        "evidence_sha256": _sha256(_repo_path(EVIDENCE_REPO_PATH)),
        "workflow_path": WORKFLOW_REPO_PATH,
        "workflow_sha256": _sha256(_repo_path(WORKFLOW_REPO_PATH)),
        "execution_task_path": EXECUTION_TASK_REPO_PATH,
        "execution_seeds": list(NEW_SEEDS),
        "execution_count": 4,
        "download_timerange": EXPECTED_GEOMETRY["download_timerange"],
        "execution_timerange": EXPECTED_GEOMETRY["execution_timerange"],
        "semantic_evidence_window": EXPECTED_GEOMETRY["semantic_evidence_window"],
        "train_period_days": EXPECTED_GEOMETRY["train_period_days"],
        "backtest_period_days": EXPECTED_GEOMETRY["backtest_period_days"],
        "pairs": list(EXPECTED_GEOMETRY["pairs"]),
        "timeframes": list(EXPECTED_GEOMETRY["timeframes"]),
        "fee": EXPECTED_GEOMETRY["fee"],
        "cache_restore_allowed": False,
        "evidence_classification": EXPECTED_CLASSIFICATION,
        "strict_oos": False,
        "protected_final_validation": False,
        "profitability_is_non_gating": True,
        "automatic_decision": False,
        "consumed_historical_oos": "20260501-20260630",
        "protected_final_holdout": "20260801-20260930",
        "authorization": deepcopy(contract["authorization"]),
        "declaration_status": declaration["status"],
    }


def load_request(path: Path) -> dict[str, Any]:
    """Fail closed unless a request exactly equals the canonical payload."""
    request = _read_json(path.resolve(), "execution request")
    expected = canonical_request()
    if set(request) != set(expected):
        missing = sorted(set(expected) - set(request))
        extra = sorted(set(request) - set(expected))
        raise RLV2ActionObservabilityExecutionError(
            f"Canonical request fields drifted: missing={missing}; extra={extra}"
        )
    for field, value in expected.items():
        if request[field] != value:
            raise RLV2ActionObservabilityExecutionError(
                f"Request field {field} drifted from canonical payload"
            )
    return request


def materialize_runtime_config(output: Path, seed: int) -> Path:
    """Write one isolated config changing only declared runtime fields."""
    validate_seed(seed)
    contract, _, base_config = _validate_contract()
    output = output.resolve()
    if output == _repo_path(BASE_CONFIG_REPO_PATH):
        raise RLV2ActionObservabilityExecutionError("Refusing to overwrite immutable base config")
    runtime = deepcopy(base_config)
    runtime["strategy"] = contract["runtime_binding"]["observable_strategy"]
    freqai = runtime.setdefault("freqai", {})
    freqai["identifier"] = runtime_identifier(seed)
    freqai["train_period_days"] = EXPECTED_GEOMETRY["train_period_days"]
    freqai["backtest_period_days"] = EXPECTED_GEOMETRY["backtest_period_days"]
    freqai.setdefault("model_training_parameters", {})["seed"] = seed
    if freqai.get("data_split_parameters") != {
        "test_size": 0.2,
        "random_state": 42,
        "shuffle": False,
    }:
        raise RLV2ActionObservabilityExecutionError("Materialized data split drifted")
    if "timerange" in runtime or "live_retrain_hours" in freqai:
        raise RLV2ActionObservabilityExecutionError(
            "Temporary config introduced unauthorized geometry"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def _validate_coverage(
    *,
    pair: str,
    timeframe: str,
    first_date: datetime,
    last_date: datetime,
    startdt: datetime,
    stopdt: datetime,
) -> None:
    if first_date > startdt:
        raise RLV2ActionObservabilityExecutionError(
            f"Data starts too late for {pair} {timeframe}: {first_date.isoformat()}"
        )
    minimum_last = int(stopdt.timestamp()) - TIMEFRAME_SECONDS[timeframe]
    if int(last_date.timestamp()) < minimum_last:
        raise RLV2ActionObservabilityExecutionError(
            f"Data ends too early for {pair} {timeframe}: {last_date.isoformat()}"
        )
    if last_date > stopdt:
        raise RLV2ActionObservabilityExecutionError(
            f"Data crosses exclusive stop for {pair} {timeframe}"
        )


def verify_downloaded_data(
    datadir: Path,
    *,
    pairs: list[str] | None = None,
) -> dict[str, Any]:
    """Verify fresh declared pair/timeframe coverage without execution."""
    from freqtrade.configuration import TimeRange
    from freqtrade.data.history.history_utils import load_pair_history

    _validate_contract()
    selected = pairs or list(EXPECTED_GEOMETRY["pairs"])
    if not selected or any(pair not in EXPECTED_GEOMETRY["pairs"] for pair in selected):
        raise RLV2ActionObservabilityExecutionError("Unknown pair for data verification")

    timerange = TimeRange.parse_timerange(EXPECTED_GEOMETRY["download_timerange"])
    startdt = timerange.startdt
    stopdt = timerange.stopdt
    if startdt is None or stopdt is None:
        raise RLV2ActionObservabilityExecutionError("Expected bounded download timerange")
    if stopdt != _date_token("20251101"):
        raise RLV2ActionObservabilityExecutionError(
            "Freqtrade parser did not preserve exclusive 2025-11-01 stop"
        )

    coverage: dict[str, dict[str, str | int]] = {}
    for pair in selected:
        for timeframe in EXPECTED_GEOMETRY["timeframes"]:
            frame = load_pair_history(
                pair=pair,
                timeframe=timeframe,
                datadir=datadir,
                timerange=timerange,
                fill_up_missing=False,
                drop_incomplete=False,
            )
            if frame.empty:
                raise RLV2ActionObservabilityExecutionError(
                    f"No downloaded data for {pair} {timeframe}"
                )
            first_date = frame["date"].min().to_pydatetime()
            last_date = frame["date"].max().to_pydatetime()
            _validate_coverage(
                pair=pair,
                timeframe=timeframe,
                first_date=first_date,
                last_date=last_date,
                startdt=startdt,
                stopdt=stopdt,
            )
            coverage[f"{pair}:{timeframe}"] = {
                "rows": len(frame),
                "first": first_date.isoformat(),
                "last": last_date.isoformat(),
            }
    return {
        "schema_version": 1,
        "download_timerange": EXPECTED_GEOMETRY["download_timerange"],
        "exclusive_stop": stopdt.isoformat(),
        "cache_restore_used": False,
        "consumed_historical_oos_accessed": False,
        "protected_final_holdout_accessed": False,
        "coverage": coverage,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", nargs="?", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--print-canonical", action="store_true")
    mode.add_argument("--materialize-config", type=Path)
    mode.add_argument("--verify-data", type=Path)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--pair", action="append", dest="pairs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.print_canonical:
            print(json.dumps(canonical_request(), indent=2, sort_keys=True))
            return 0
        if args.materialize_config is not None:
            if args.seed is None:
                raise RLV2ActionObservabilityExecutionError(
                    "--seed is required with --materialize-config"
                )
            print(materialize_runtime_config(args.materialize_config, args.seed))
            return 0
        if args.verify_data is not None:
            payload = verify_downloaded_data(args.verify_data, pairs=args.pairs)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.request is None:
            _validate_contract()
            return 0
        load_request(args.request)
        return 0
    except RLV2ActionObservabilityExecutionError as exc:
        print(f"RL-v2 action-observability validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
