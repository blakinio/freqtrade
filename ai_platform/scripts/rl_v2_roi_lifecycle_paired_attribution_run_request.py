#!/usr/bin/env python3
"""Guard the one-shot RL-v2 ROI lifecycle paired-attribution request."""

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
    "ai_platform/experimental_model_research/"
    "rl-v2-roi-lifecycle-paired-attribution-execution-contract-v1.json"
)
REQUEST_REPO_PATH = (
    "ai_platform/experimental_model_research/run-requests/"
    "rl-v2-roi-lifecycle-paired-attribution-execution-v1.json"
)
DIAGNOSIS_REPO_PATH = (
    "ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json"
)
VARIANT_DECLARATION_REPO_PATH = (
    "ai_platform/experimental_model_research/rl-v2-roi-lifecycle-alignment-v1.json"
)
BASE_CONFIG_REPO_PATH = "ai_platform/configs/rl_v2_training_research.json"
MODEL_REPO_PATH = "ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py"
BASELINE_STRATEGY_REPO_PATH = "ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py"
STRATEGY_REPO_PATH = "ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py"
WORKFLOW_REPO_PATH = ".github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml"
VALIDATOR_REPO_PATH = "ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py"
EVIDENCE_EXTRACTOR_REPO_PATH = (
    "ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_evidence.py"
)
TASK_REPO_PATH = (
    "docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md"
)

CONTRACT_PATH = REPO_ROOT / CONTRACT_REPO_PATH
EXPECTED_REQUEST_ID = "rl-v2-roi-lifecycle-paired-attribution-execution-v1"
EXPECTED_ACTION = "execute_rl_v2_roi_lifecycle_paired_attribution"
EXPECTED_DECLARATION_MERGE = "d26f2221107bb2c0a95753cb2d8ea4bacf3a65f9"
EXPECTED_CONFIG_SHA256 = "5adc805deadcfe6dc3c52d0745f62546952a96b38b3bd06bc28ac9987063f6de"
EXPECTED_MODEL_SHA256 = "3cec25cc7b43e3214a8e22d153107307a7a7bfbfd48b6bf313ecb4624cb79d46"
EXPECTED_BASELINE_STRATEGY_SHA256 = (
    "9318a4d13937d9b572c4bcecfb56f999fd82d8309c6f898d0166c0c71dfd5c19"
)
EXPECTED_STRATEGY_SHA256 = "366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7"
EXPECTED_RUNTIME_IDENTIFIER = "rl-v2-roi-lifecycle-paired-attribution-v1"
EXPECTED_BASELINE_METRICS: dict[str, int | float] = {
    "roi_exit_count": 122,
    "roi_exit_followed_by_same_pair_15m_reentry_count": 122,
    "immediate_external_exit_reentry_boundary_count": 131,
    "external_exit_reentry_boundary_fee_usdt": 52.582123,
}
EXPECTED_EXECUTION: dict[str, Any] = {
    "mode": "one_shot_variant_trigger_pr",
    "variant_executions": 1,
    "baseline_executions": 0,
    "download_timerange": "20250801-20260501",
    "execution_timerange": "20260301-20260501",
    "semantic_evidence_window": "20260301-20260430",
    "freqtrade_stop_semantics": "end_exclusive",
    "train_period_days": 90,
    "backtest_period_days": 61,
    "live_retrain_hours_present": False,
}
EXPECTED_MARKET_DATA: dict[str, Any] = {
    "exchange": "kraken",
    "pairs": ["BTC/USDT", "ETH/USDT"],
    "timeframes": ["15m", "1h", "4h"],
    "fee": 0.002,
    "verification_module": (
        "ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_run_request"
    ),
    "cache_namespace": "rl-v2-historical-training-pre-oos-v1",
    "reuse_verified_baseline_cache": True,
    "restore_from_post_20260501_cache_allowed": False,
}
EXPECTED_CLASSIFICATION = "paired_historical_development_attribution"
TIMEFRAME_SECONDS = {"15m": 15 * 60, "1h": 60 * 60, "4h": 4 * 60 * 60}
FORBIDDEN_BASE_CONFIG_KEYS = {
    "timerange",
    "train_period_days",
    "backtest_period_days",
    "live_retrain_hours",
}


class RLV2PairedAttributionError(RuntimeError):
    """Raised when the paired-attribution contract or request drifts."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RLV2PairedAttributionError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RLV2PairedAttributionError(f"{label} must contain a JSON object")
    return payload


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise RLV2PairedAttributionError(f"Unable to hash canonical input {path}: {exc}") from exc


def _repo_path(value: str) -> Path:
    candidate = (REPO_ROOT / value).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise RLV2PairedAttributionError(
            f"Canonical path escapes repository root: {value}"
        ) from exc
    return candidate


def _date_token(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d").replace(tzinfo=UTC)


def _split_timerange(value: str) -> tuple[str, str]:
    try:
        start, stop = value.split("-", maxsplit=1)
    except ValueError as exc:
        raise RLV2PairedAttributionError(
            f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}"
        ) from exc
    if len(start) != 8 or len(stop) != 8:
        raise RLV2PairedAttributionError(f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}")
    return start, stop


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


def _require_sha(path: str, expected: str, label: str) -> None:
    actual = _sha256(_repo_path(path))
    if actual != expected:
        raise RLV2PairedAttributionError(
            f"{label} SHA-256 drifted: expected {expected}, got {actual}"
        )


def _validate_temporal_boundaries() -> None:
    download_start, download_stop = _split_timerange(EXPECTED_EXECUTION["download_timerange"])
    execution_start, execution_stop = _split_timerange(EXPECTED_EXECUTION["execution_timerange"])
    evidence_start, evidence_end_inclusive = _split_timerange(
        EXPECTED_EXECUTION["semantic_evidence_window"]
    )
    consumed_start = _date_token("20260501")
    if _date_token(download_stop) > consumed_start:
        raise RLV2PairedAttributionError("Download geometry crosses consumed OOS")
    if _date_token(execution_stop) > consumed_start:
        raise RLV2PairedAttributionError("Execution geometry crosses consumed OOS")
    if download_stop != "20260501" or execution_stop != "20260501":
        raise RLV2PairedAttributionError("Download and execution must stop at exclusive 2026-05-01")
    if evidence_start != execution_start:
        raise RLV2PairedAttributionError("Semantic evidence start drifted")
    expected_stop = (_date_token(evidence_end_inclusive) + timedelta(days=1)).strftime("%Y%m%d")
    if execution_stop != expected_stop:
        raise RLV2PairedAttributionError(
            "Semantic evidence inclusive end does not map to execution stop"
        )
    execution_days = (_date_token(execution_stop) - _date_token(execution_start)).days
    if execution_days != EXPECTED_EXECUTION["backtest_period_days"]:
        raise RLV2PairedAttributionError("Frozen backtest period drifted")
    if _date_token(download_start) >= _date_token(execution_start):
        raise RLV2PairedAttributionError("Download history must begin before execution")


# Centralized intentionally: every immutable boundary is checked in one fail-closed guard.
def _validate_contract(  # noqa: C901
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = _read_json(CONTRACT_PATH, "paired-attribution contract")
    if contract.get("schema_version") != 1:
        raise RLV2PairedAttributionError("Contract schema_version must be 1")
    if contract.get("contract_id") != EXPECTED_REQUEST_ID:
        raise RLV2PairedAttributionError("Contract id drifted")
    if contract.get("task") != TASK_REPO_PATH:
        raise RLV2PairedAttributionError("Task path drifted")
    if contract.get("task_declaration_merge") != EXPECTED_DECLARATION_MERGE:
        raise RLV2PairedAttributionError("Task declaration merge drifted")
    if contract.get("request_path") != REQUEST_REPO_PATH:
        raise RLV2PairedAttributionError("Request path drifted")
    if contract.get("trigger") != {
        "event": "pull_request_opened",
        "base_branch": "develop",
        "exact_one_file": True,
    }:
        raise RLV2PairedAttributionError("Trigger contract drifted")

    baseline = contract.get("baseline_evidence")
    if not isinstance(baseline, dict):
        raise RLV2PairedAttributionError("Baseline evidence contract missing")
    expected_baseline = {
        "workflow_run_id": 30022863894,
        "trigger_pr": 218,
        "artifact_name": "rl-v2-historical-training-execution-218",
        "artifact_digest": (
            "sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55"
        ),
        "diagnosis_path": DIAGNOSIS_REPO_PATH,
        "baseline_strategy": "AiDesiredPositionRLResearchStrategy",
        "baseline_strategy_path": BASELINE_STRATEGY_REPO_PATH,
        "baseline_strategy_sha256": EXPECTED_BASELINE_STRATEGY_SHA256,
        "rerun_allowed": False,
        "primary_metrics": EXPECTED_BASELINE_METRICS,
    }
    if baseline != expected_baseline:
        raise RLV2PairedAttributionError("Baseline evidence binding drifted")

    runtime = contract.get("runtime_binding")
    if not isinstance(runtime, dict):
        raise RLV2PairedAttributionError("Runtime binding missing")
    expected_runtime = {
        "freqai_model": "DesiredPositionReinforcementLearner",
        "freqai_model_path": MODEL_REPO_PATH,
        "base_config_path": BASE_CONFIG_REPO_PATH,
        "variant_declaration_path": VARIANT_DECLARATION_REPO_PATH,
        "strategy": "AiDesiredPositionRLLifecycleAlignedResearchStrategy",
        "strategy_path": STRATEGY_REPO_PATH,
        "strategy_sha256": EXPECTED_STRATEGY_SHA256,
        "only_semantic_delta": {"ignore_roi_if_entry_signal": True},
        "runtime_identifier": EXPECTED_RUNTIME_IDENTIFIER,
        "backend_family": "stable_baselines3_via_freqai_reinforcement_learner",
        "model_type": "PPO",
        "policy_type": "MlpPolicy",
        "seed": 42,
        "action_space": {"0": "target_flat", "1": "target_long"},
        "action_space_size": 2,
        "long_only": True,
        "transition_reference": (
            "ai_platform.scripts.rl_v2_synthetic_reference.desired_position_transition"
        ),
        "reward_reference": "ai_platform.scripts.rl_v2_synthetic_reference.reference_reward",
        "reward_constants_source": (
            "ai_platform.scripts.rl_v2_synthetic_reference.REWARD_REFERENCE"
        ),
    }
    if runtime != expected_runtime:
        raise RLV2PairedAttributionError("Runtime binding drifted")

    if contract.get("execution_geometry") != EXPECTED_EXECUTION:
        raise RLV2PairedAttributionError("Execution geometry drifted")
    expected_materialization = {
        "base_config_immutable": True,
        "temporary_runtime_config": True,
        "allowed_replacements": {
            "strategy": "AiDesiredPositionRLLifecycleAlignedResearchStrategy",
            "freqai.identifier": EXPECTED_RUNTIME_IDENTIFIER,
        },
        "allowed_added_freqai_keys": {
            "train_period_days": 90,
            "backtest_period_days": 61,
        },
        "timerange_added_to_config": False,
        "live_retrain_hours_added": False,
    }
    if contract.get("configuration_materialization") != expected_materialization:
        raise RLV2PairedAttributionError("Configuration materialization drifted")
    if contract.get("market_data") != EXPECTED_MARKET_DATA:
        raise RLV2PairedAttributionError("Market-data contract drifted")

    attribution = contract.get("attribution")
    if not isinstance(attribution, dict):
        raise RLV2PairedAttributionError("Attribution contract missing")
    if attribution.get("classification") != EXPECTED_CLASSIFICATION:
        raise RLV2PairedAttributionError("Attribution classification drifted")
    if attribution.get("strict_oos") is not False:
        raise RLV2PairedAttributionError("Paired attribution cannot be strict OOS")
    if attribution.get("protected_final_validation") is not False:
        raise RLV2PairedAttributionError("Paired attribution cannot be protected final validation")
    if attribution.get("profitability_is_non_gating") is not True:
        raise RLV2PairedAttributionError("Profitability must remain non-gating")
    if attribution.get("primary_directional_criteria") != {
        "roi_exit_followed_by_same_pair_15m_reentry_count_lt": 122,
        "external_exit_reentry_boundary_fee_usdt_lt": 52.582123,
        "all_required": True,
    }:
        raise RLV2PairedAttributionError("Primary attribution criteria drifted")

    isolation = contract.get("isolation")
    if not isinstance(isolation, dict):
        raise RLV2PairedAttributionError("Isolation contract missing")
    if isolation.get("consumed_historical_oos") != {
        "timerange": "20260501-20260630",
        "start_inclusive": "2026-05-01T00:00:00Z",
        "usage": "forbidden",
    }:
        raise RLV2PairedAttributionError("Consumed OOS isolation drifted")
    if isolation.get("protected_final_holdout") != {
        "timerange": "20260801-20260930",
        "usage": "forbidden",
    }:
        raise RLV2PairedAttributionError("Final holdout isolation drifted")
    if isolation.get("frozen_entry_prediction_threshold") != 0.006:
        raise RLV2PairedAttributionError("Entry threshold drifted")
    if isolation.get("frozen_exit_prediction_threshold") != -0.009:
        raise RLV2PairedAttributionError("Exit threshold drifted")
    if isolation.get("phase6_authoritative_selected_model") is not None:
        raise RLV2PairedAttributionError("Phase 6 selected_model drifted")

    authorization = contract.get("authorization")
    if not isinstance(authorization, dict):
        raise RLV2PairedAttributionError("Authorization contract missing")
    required_false = {
        "infrastructure_merge_executes_model",
        "baseline_execution_allowed",
        "strict_oos_scoring_allowed",
        "consumed_historical_oos_access_allowed",
        "protected_final_holdout_access_allowed",
        "retuning_allowed",
        "model_parameter_changes_allowed",
        "feature_changes_allowed",
        "reward_changes_allowed",
        "strategy_changes_beyond_declared_variant_allowed",
        "cross_track_selection_allowed",
        "promotion_allowed",
        "live_trading_allowed",
        "profitability_claim_allowed",
        "superiority_claim_allowed",
    }
    if any(authorization.get(field) is not False for field in required_false):
        raise RLV2PairedAttributionError("Authorization boundary drifted")
    required_true = {
        "canonical_request_required",
        "variant_historical_training_execution_allowed_after_canonical_request",
        "variant_historical_backtest_allowed_after_canonical_request",
        "market_data_download_allowed_after_canonical_request",
    }
    if any(authorization.get(field) is not True for field in required_true):
        raise RLV2PairedAttributionError("Execution authorization drifted")

    _validate_temporal_boundaries()
    _require_sha(BASE_CONFIG_REPO_PATH, EXPECTED_CONFIG_SHA256, "Base config")
    _require_sha(MODEL_REPO_PATH, EXPECTED_MODEL_SHA256, "FreqAI model")
    _require_sha(
        BASELINE_STRATEGY_REPO_PATH,
        EXPECTED_BASELINE_STRATEGY_SHA256,
        "Baseline strategy",
    )
    _require_sha(STRATEGY_REPO_PATH, EXPECTED_STRATEGY_SHA256, "Variant strategy")

    diagnosis = _read_json(_repo_path(DIAGNOSIS_REPO_PATH), "baseline diagnosis")
    if diagnosis.get("status") != "complete":
        raise RLV2PairedAttributionError("Baseline diagnosis is not complete")
    source = diagnosis.get("source", {})
    if source.get("artifact_digest") != baseline["artifact_digest"]:
        raise RLV2PairedAttributionError("Baseline artifact digest drifted")
    if source.get("workflow_run_id") != 30022863894 or source.get("trigger_pr") != 218:
        raise RLV2PairedAttributionError("Baseline provenance drifted")
    if source.get("strict_oos") is not False:
        raise RLV2PairedAttributionError("Baseline diagnosis strict-OOS flag drifted")
    churn = diagnosis.get("churn", {})
    diagnosis_metrics = {
        "roi_exit_count": diagnosis.get("by_exit_reason", {}).get("roi", {}).get("trades"),
        "roi_exit_followed_by_same_pair_15m_reentry_count": churn.get(
            "roi_exits_followed_by_15m_reentry"
        ),
        "immediate_external_exit_reentry_boundary_count": churn.get(
            "immediate_external_exit_reentry_boundaries"
        ),
        "external_exit_reentry_boundary_fee_usdt": churn.get(
            "fees_at_immediate_external_exit_reentry_boundaries_usdt"
        ),
    }
    if diagnosis_metrics != EXPECTED_BASELINE_METRICS:
        raise RLV2PairedAttributionError("Committed baseline metrics drifted")

    variant = _read_json(_repo_path(VARIANT_DECLARATION_REPO_PATH), "lifecycle variant declaration")
    if variant.get("status") != "implemented_not_executed":
        raise RLV2PairedAttributionError("Variant implementation status drifted")
    experimental_variant = variant.get("experimental_variant", {})
    if experimental_variant.get("strategy") != runtime["strategy"]:
        raise RLV2PairedAttributionError("Variant strategy identity drifted")
    if experimental_variant.get("strategy_path") != STRATEGY_REPO_PATH:
        raise RLV2PairedAttributionError("Variant strategy path drifted")
    if experimental_variant.get("strategy_sha256") != EXPECTED_STRATEGY_SHA256:
        raise RLV2PairedAttributionError("Variant strategy hash binding drifted")
    if experimental_variant.get("only_allowed_override") != {"ignore_roi_if_entry_signal": True}:
        raise RLV2PairedAttributionError("Variant semantic delta drifted")
    future = variant.get("future_attribution", {})
    if future.get("classification") != EXPECTED_CLASSIFICATION:
        raise RLV2PairedAttributionError("Variant attribution classification drifted")
    if future.get("strict_oos") is not False:
        raise RLV2PairedAttributionError("Variant attribution strict-OOS drifted")

    base_config = _read_json(_repo_path(BASE_CONFIG_REPO_PATH), "base config")
    if FORBIDDEN_BASE_CONFIG_KEYS.intersection(_collect_keys(base_config)):
        raise RLV2PairedAttributionError("Base config must remain free of execution geometry")
    if base_config.get("dry_run") is not True:
        raise RLV2PairedAttributionError("Base config dry_run drifted")
    if base_config.get("trading_mode") != "spot":
        raise RLV2PairedAttributionError("Base config trading mode drifted")
    if base_config.get("initial_state") != "stopped":
        raise RLV2PairedAttributionError("Base config initial_state drifted")
    if base_config.get("freqaimodel") != runtime["freqai_model"]:
        raise RLV2PairedAttributionError("Base config model drifted")
    if base_config.get("strategy") != baseline["baseline_strategy"]:
        raise RLV2PairedAttributionError("Base config baseline strategy drifted")
    freqai = base_config.get("freqai", {})
    if freqai.get("identifier") != "ai-platform-rl-v2-training-research-v1":
        raise RLV2PairedAttributionError("Base FreqAI identifier drifted")
    rl_config = freqai.get("rl_config", {})
    if rl_config.get("model_type") != "PPO":
        raise RLV2PairedAttributionError("PPO model type drifted")
    if rl_config.get("policy_type") != "MlpPolicy":
        raise RLV2PairedAttributionError("Policy type drifted")
    if rl_config.get("training_fee") != 0.002:
        raise RLV2PairedAttributionError("Training fee drifted")
    if rl_config.get("model_reward_parameters") != {}:
        raise RLV2PairedAttributionError("Reward parameters drifted")
    if freqai.get("model_training_parameters", {}).get("seed") != 42:
        raise RLV2PairedAttributionError("Training seed drifted")

    return contract, diagnosis, variant, base_config


def canonical_rl_v2_roi_lifecycle_paired_attribution_request() -> dict[str, Any]:
    """Return the only payload authorized for the later one-file trigger PR."""
    contract, _, _, _ = _validate_contract()
    hash_inputs = {
        "contract": CONTRACT_REPO_PATH,
        "baseline_diagnosis": DIAGNOSIS_REPO_PATH,
        "variant_declaration": VARIANT_DECLARATION_REPO_PATH,
        "config": BASE_CONFIG_REPO_PATH,
        "freqai_model": MODEL_REPO_PATH,
        "strategy": STRATEGY_REPO_PATH,
        "validator": VALIDATOR_REPO_PATH,
        "evidence_extractor": EVIDENCE_EXTRACTOR_REPO_PATH,
        "workflow": WORKFLOW_REPO_PATH,
    }
    for label, path in hash_inputs.items():
        if not _repo_path(path).is_file():
            raise RLV2PairedAttributionError(f"Canonical {label} input is missing: {path}")
    return {
        "schema_version": 1,
        "request_id": EXPECTED_REQUEST_ID,
        "action": EXPECTED_ACTION,
        "contract_path": CONTRACT_REPO_PATH,
        "contract_sha256": _sha256(CONTRACT_PATH),
        "baseline_diagnosis_path": DIAGNOSIS_REPO_PATH,
        "baseline_diagnosis_sha256": _sha256(_repo_path(DIAGNOSIS_REPO_PATH)),
        "baseline_artifact_name": contract["baseline_evidence"]["artifact_name"],
        "baseline_artifact_digest": contract["baseline_evidence"]["artifact_digest"],
        "baseline_rerun_allowed": False,
        "variant_declaration_path": VARIANT_DECLARATION_REPO_PATH,
        "variant_declaration_sha256": _sha256(_repo_path(VARIANT_DECLARATION_REPO_PATH)),
        "config_path": BASE_CONFIG_REPO_PATH,
        "config_sha256": _sha256(_repo_path(BASE_CONFIG_REPO_PATH)),
        "freqai_model": contract["runtime_binding"]["freqai_model"],
        "freqai_model_path": MODEL_REPO_PATH,
        "freqai_model_sha256": _sha256(_repo_path(MODEL_REPO_PATH)),
        "strategy": contract["runtime_binding"]["strategy"],
        "strategy_path": STRATEGY_REPO_PATH,
        "strategy_sha256": _sha256(_repo_path(STRATEGY_REPO_PATH)),
        "validator_path": VALIDATOR_REPO_PATH,
        "validator_sha256": _sha256(_repo_path(VALIDATOR_REPO_PATH)),
        "evidence_extractor_path": EVIDENCE_EXTRACTOR_REPO_PATH,
        "evidence_extractor_sha256": _sha256(_repo_path(EVIDENCE_EXTRACTOR_REPO_PATH)),
        "workflow_path": WORKFLOW_REPO_PATH,
        "workflow_sha256": _sha256(_repo_path(WORKFLOW_REPO_PATH)),
        "runtime_identifier": EXPECTED_RUNTIME_IDENTIFIER,
        "download_timerange": EXPECTED_EXECUTION["download_timerange"],
        "execution_timerange": EXPECTED_EXECUTION["execution_timerange"],
        "semantic_evidence_window": EXPECTED_EXECUTION["semantic_evidence_window"],
        "train_period_days": EXPECTED_EXECUTION["train_period_days"],
        "backtest_period_days": EXPECTED_EXECUTION["backtest_period_days"],
        "pairs": list(EXPECTED_MARKET_DATA["pairs"]),
        "timeframes": list(EXPECTED_MARKET_DATA["timeframes"]),
        "fee": EXPECTED_MARKET_DATA["fee"],
        "evidence_classification": EXPECTED_CLASSIFICATION,
        "strict_oos": False,
        "protected_final_validation": False,
        "profitability_is_non_gating": True,
        "baseline_primary_metrics": dict(EXPECTED_BASELINE_METRICS),
        "consumed_historical_oos": "20260501-20260630",
        "protected_final_holdout": "20260801-20260930",
        "authorization": dict(contract["authorization"]),
    }


def load_rl_v2_roi_lifecycle_paired_attribution_request(path: Path) -> dict[str, Any]:
    """Load and fail closed unless the request exactly matches the canonical payload."""
    request = _read_json(path.resolve(), "paired-attribution request")
    expected = canonical_rl_v2_roi_lifecycle_paired_attribution_request()
    if set(request) != set(expected):
        missing = sorted(set(expected) - set(request))
        extra = sorted(set(request) - set(expected))
        raise RLV2PairedAttributionError(
            f"Canonical request fields drifted: missing={missing}; extra={extra}"
        )
    for field, expected_value in expected.items():
        if request[field] != expected_value:
            raise RLV2PairedAttributionError(
                f"Request field {field} drifted from canonical payload"
            )
    return request


def materialize_runtime_config(output: Path) -> Path:
    """Write the only temporary variant execution config allowed by the contract."""
    contract, _, _, base_config = _validate_contract()
    output = output.resolve()
    if output == _repo_path(BASE_CONFIG_REPO_PATH):
        raise RLV2PairedAttributionError("Refusing to overwrite immutable base config")

    runtime_config = deepcopy(base_config)
    runtime_config["strategy"] = contract["runtime_binding"]["strategy"]
    freqai = runtime_config.setdefault("freqai", {})
    freqai["identifier"] = EXPECTED_RUNTIME_IDENTIFIER
    freqai["train_period_days"] = EXPECTED_EXECUTION["train_period_days"]
    freqai["backtest_period_days"] = EXPECTED_EXECUTION["backtest_period_days"]
    if "timerange" in runtime_config or "live_retrain_hours" in freqai:
        raise RLV2PairedAttributionError("Temporary config introduced unauthorized geometry")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(runtime_config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def verify_downloaded_data(datadir: Path, *, pairs: list[str] | None = None) -> dict[str, Any]:
    """Verify exact pre-May pair/timeframe coverage without model execution."""
    from freqtrade.configuration import TimeRange
    from freqtrade.data.history.history_utils import load_pair_history

    _validate_contract()
    selected_pairs = pairs or EXPECTED_MARKET_DATA["pairs"]
    if not selected_pairs or any(
        pair not in EXPECTED_MARKET_DATA["pairs"] for pair in selected_pairs
    ):
        raise RLV2PairedAttributionError("Unknown pair requested for data verification")

    timerange = TimeRange.parse_timerange(EXPECTED_EXECUTION["download_timerange"])
    startdt = timerange.startdt
    stopdt = timerange.stopdt
    if startdt is None or stopdt is None:
        raise RLV2PairedAttributionError("Expected bounded download timerange")
    if stopdt != _date_token("20260501"):
        raise RLV2PairedAttributionError(
            "Freqtrade parser did not preserve exclusive 2026-05-01 stop"
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
                raise RLV2PairedAttributionError(f"No downloaded data for {pair} {timeframe}")
            first_date = frame["date"].min().to_pydatetime()
            last_date = frame["date"].max().to_pydatetime()
            if first_date > startdt:
                raise RLV2PairedAttributionError(
                    f"Data starts too late for {pair} {timeframe}: {first_date.isoformat()}"
                )
            minimum_last_ts = timerange.stopts - TIMEFRAME_SECONDS[timeframe]
            if int(last_date.timestamp()) < minimum_last_ts:
                raise RLV2PairedAttributionError(
                    f"Data ends too early for {pair} {timeframe}: {last_date.isoformat()}"
                )
            if last_date >= stopdt:
                raise RLV2PairedAttributionError(
                    f"Data crosses exclusive stop for {pair} {timeframe}"
                )
            coverage[f"{pair}:{timeframe}"] = {
                "rows": len(frame),
                "first": first_date.isoformat(),
                "last": last_date.isoformat(),
            }

    return {
        "schema_version": 1,
        "verification_id": "rl-v2-roi-lifecycle-paired-pre-oos-data-v1",
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
        help="Path to the one-shot paired-attribution request JSON",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--print-canonical", action="store_true")
    mode.add_argument("--materialize-config", type=Path)
    mode.add_argument("--verify-data", type=Path)
    parser.add_argument("--pair", action="append", dest="pairs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.print_canonical:
            payload = canonical_rl_v2_roi_lifecycle_paired_attribution_request()
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.materialize_config is not None:
            path = materialize_runtime_config(args.materialize_config)
            print(path)
            return 0
        if args.verify_data is not None:
            payload = verify_downloaded_data(args.verify_data, pairs=args.pairs)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.request is None:
            _validate_contract()
            return 0
        load_rl_v2_roi_lifecycle_paired_attribution_request(args.request)
        return 0
    except RLV2PairedAttributionError as exc:
        print(f"RL-v2 paired-attribution validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
