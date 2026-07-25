#!/usr/bin/env python3
"""Guard the exact RL-v2 lifecycle seed-robustness execution request."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_run_request import (
    EXPECTED_EXECUTION as PAIRED_EXECUTION,
)
from ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_run_request import (
    RLV2PairedAttributionError,
    _read_json,
    _repo_path,
    _sha256,
    verify_downloaded_data,
)
from ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_run_request import (
    _validate_contract as _validate_paired_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REPO_PATH = (
    "ai_platform/experimental_model_research/"
    "rl-v2-lifecycle-seed-robustness-execution-contract-v1.json"
)
DECLARATION_REPO_PATH = (
    "ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-declaration-v1.json"
)
INTERPRETATION_REPO_PATH = (
    "ai_platform/experimental_model_research/rl-v2-paired-attribution-interpretation-v1.json"
)
REQUEST_REPO_PATH = (
    "ai_platform/experimental_model_research/run-requests/"
    "rl-v2-lifecycle-seed-robustness-execution-v1.json"
)
BASE_CONFIG_REPO_PATH = "ai_platform/configs/rl_v2_training_research.json"
MODEL_REPO_PATH = "ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py"
STRATEGY_REPO_PATH = "ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py"
VALIDATOR_REPO_PATH = "ai_platform/scripts/rl_v2_lifecycle_seed_robustness_run_request.py"
EVIDENCE_REPO_PATH = "ai_platform/scripts/rl_v2_lifecycle_seed_robustness_evidence.py"
WORKFLOW_REPO_PATH = ".github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml"
INFRA_TASK_REPO_PATH = (
    "docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure.md"
)
EXECUTION_TASK_REPO_PATH = (
    "docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md"
)

EXPECTED_CONTRACT_ID = "rl-v2-lifecycle-seed-robustness-execution-v1"
EXPECTED_REQUEST_ID = EXPECTED_CONTRACT_ID
EXPECTED_ACTION = "execute_rl_v2_lifecycle_seed_robustness"
EXPECTED_DECLARATION_MERGE = "d943a670068484fc6391e17833c20c8abc757ede"
EXPECTED_DECLARATION_CLOSURE_MERGE = "2ea44b33423d199f5ab020e07031b14642806303"
EXPECTED_CONFIG_SHA256 = "5adc805deadcfe6dc3c52d0745f62546952a96b38b3bd06bc28ac9987063f6de"
EXPECTED_MODEL_SHA256 = "3cec25cc7b43e3214a8e22d153107307a7a7bfbfd48b6bf313ecb4624cb79d46"
EXPECTED_STRATEGY_SHA256 = "366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7"
EXPECTED_ANCHOR_DIGEST = "sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04"
EXPECTED_BASELINE_DIGEST = "sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55"
ANCHOR_SEED = 42
NEW_SEEDS = (300538280, 1710810709, 1950377252, 1146911492)
ORDERED_SEEDS = (ANCHOR_SEED, *NEW_SEEDS)
EXPECTED_CLASSIFICATION = "paired_historical_development_seed_robustness"
RUNTIME_IDENTIFIER_TEMPLATE = "rl-v2-lifecycle-seed-robustness-v1-seed-{seed}"
EXPECTED_BASELINE_METRICS: dict[str, int | float] = {
    "roi_exit_followed_by_same_pair_15m_reentry_count": 122,
    "immediate_external_exit_reentry_boundary_count": 131,
    "external_exit_reentry_boundary_fee_usdt": 52.582123,
}
EXPECTED_ANCHOR_METRICS: dict[str, int | float] = {
    "roi_exit_followed_by_same_pair_15m_reentry_count": 0,
    "immediate_external_exit_reentry_boundary_count": 0,
    "external_exit_reentry_boundary_fee_usdt": 0.0,
}
EXPECTED_VALIDITY_GATE: dict[str, Any] = {
    "exactly_one_backtest_archive": True,
    "both_pairs_minimum_completed_trades_each": 1,
    "minimum_total_trade_count": 20,
    "minimum_target_flat_exit_count": 1,
    "maximum_rejected_signals": 0,
    "maximum_timed_out_entry_orders": 0,
    "maximum_timed_out_exit_orders": 0,
    "accounting_must_reconcile": True,
    "runtime_hashes_must_reconcile": True,
    "consumed_historical_oos_accessed": False,
    "protected_final_holdout_accessed": False,
}
EXPECTED_MECHANISM_GATE: dict[str, Any] = {
    "original_directional_criteria_per_seed": {
        "roi_exit_followed_by_same_pair_15m_reentry_count_lt": 122,
        "external_exit_reentry_boundary_fee_usdt_lt": 52.582123,
        "all_required": True,
        "required_seed_count": 5,
    },
    "strong_reduction_criteria": {
        "roi_exit_followed_by_same_pair_15m_reentry_count_lte": 30,
        "external_exit_reentry_boundary_fee_usdt_lte": 13.145531,
        "minimum_seed_count_meeting_both": 4,
    },
}


class RLV2SeedRobustnessError(RuntimeError):
    """Raised when seed-robustness infrastructure or a request drifts."""


def runtime_identifier(seed: int) -> str:
    """Return the only isolated runtime identifier allowed for a new seed."""
    validate_new_seed(seed)
    return RUNTIME_IDENTIFIER_TEMPLATE.format(seed=seed)


def validate_new_seed(seed: int) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise RLV2SeedRobustnessError("Seed must be an integer")
    if seed == ANCHOR_SEED:
        raise RLV2SeedRobustnessError("Anchor seed 42 must be reused and cannot be rerun")
    if seed not in NEW_SEEDS:
        raise RLV2SeedRobustnessError(f"Seed is outside the frozen execution set: {seed}")


def _require_sha(path: str, expected: str, label: str) -> None:
    actual = _sha256(_repo_path(path))
    if actual != expected:
        raise RLV2SeedRobustnessError(f"{label} SHA-256 drifted: expected {expected}, got {actual}")


def _validate_declaration(  # noqa: C901
    contract: dict[str, Any],
) -> dict[str, Any]:
    declaration = _read_json(_repo_path(DECLARATION_REPO_PATH), "seed declaration")
    if declaration.get("schema_version") != 1:
        raise RLV2SeedRobustnessError("Seed declaration schema_version drifted")
    if declaration.get("declaration_id") != ("rl-v2-lifecycle-seed-robustness-declaration-v1"):
        raise RLV2SeedRobustnessError("Seed declaration id drifted")
    if declaration.get("status") != "declared_not_authorized_for_execution":
        raise RLV2SeedRobustnessError("Seed declaration status drifted")

    source = declaration.get("source", {})
    if source.get("anchor_artifact_digest") != EXPECTED_ANCHOR_DIGEST:
        raise RLV2SeedRobustnessError("Anchor artifact digest drifted")
    if source.get("anchor_seed") != ANCHOR_SEED:
        raise RLV2SeedRobustnessError("Anchor seed drifted")
    if source.get("strict_oos") is not False:
        raise RLV2SeedRobustnessError("Seed declaration cannot be strict OOS")
    if source.get("protected_final_validation") is not False:
        raise RLV2SeedRobustnessError("Seed declaration cannot be final validation")

    baseline = declaration.get("baseline", {})
    if baseline.get("artifact_digest") != EXPECTED_BASELINE_DIGEST:
        raise RLV2SeedRobustnessError("Baseline artifact digest drifted")
    if baseline.get("rerun_allowed") is not False:
        raise RLV2SeedRobustnessError("Baseline rerun boundary drifted")
    if baseline.get("primary_metrics") != EXPECTED_BASELINE_METRICS:
        raise RLV2SeedRobustnessError("Baseline mechanism metrics drifted")

    seed_set = declaration.get("seed_set", {})
    if seed_set.get("ordered_seeds") != list(ORDERED_SEEDS):
        raise RLV2SeedRobustnessError("Ordered seed set drifted")
    if seed_set.get("new_execution_seeds") != list(NEW_SEEDS):
        raise RLV2SeedRobustnessError("New execution seed set drifted")
    if seed_set.get("anchor_seed_rerun_allowed") is not False:
        raise RLV2SeedRobustnessError("Anchor rerun boundary drifted")
    if seed_set.get("new_variant_execution_count") != 4:
        raise RLV2SeedRobustnessError("New variant execution count drifted")
    if seed_set.get("baseline_execution_count") != 0:
        raise RLV2SeedRobustnessError("Baseline execution count drifted")

    runtime = declaration.get("runtime_binding", {})
    expected_runtime = contract["runtime_binding"]
    for key in (
        "model",
        "model_path",
        "model_sha256",
        "strategy",
        "strategy_path",
        "strategy_sha256",
        "base_config_path",
        "base_config_sha256",
        "only_behavioral_change_per_execution",
        "data_split_random_state",
        "data_split_shuffle",
        "model_type",
        "policy_type",
        "n_steps",
        "batch_size",
        "train_cycles",
        "only_lifecycle_semantic_delta",
    ):
        contract_key = {
            "model": "freqai_model",
            "model_path": "freqai_model_path",
            "model_sha256": "freqai_model_sha256",
        }.get(key, key)
        if runtime.get(key) != expected_runtime.get(contract_key):
            raise RLV2SeedRobustnessError(f"Declaration runtime field drifted: {key}")

    if declaration.get("per_seed_validity_gate") != EXPECTED_VALIDITY_GATE | {
        "invalid_seed_replacement_allowed": False
    }:
        raise RLV2SeedRobustnessError("Per-seed validity declaration drifted")
    mechanism = declaration.get("mechanism_consistency_gate", {})
    if (
        mechanism.get("original_directional_criteria_per_seed")
        != (EXPECTED_MECHANISM_GATE["original_directional_criteria_per_seed"])
    ):
        raise RLV2SeedRobustnessError("Original mechanism criteria drifted")
    strong = mechanism.get("strong_reduction_criteria", {})
    if {
        key: strong.get(key) for key in EXPECTED_MECHANISM_GATE["strong_reduction_criteria"]
    } != EXPECTED_MECHANISM_GATE["strong_reduction_criteria"]:
        raise RLV2SeedRobustnessError("Strong mechanism criteria drifted")

    evidence = declaration.get("evidence_classification", {})
    if evidence.get("aggregate_classification") != EXPECTED_CLASSIFICATION:
        raise RLV2SeedRobustnessError("Aggregate classification drifted")
    if evidence.get("strict_oos") is not False:
        raise RLV2SeedRobustnessError("Seed evidence cannot be strict OOS")
    if evidence.get("protected_final_validation") is not False:
        raise RLV2SeedRobustnessError("Seed evidence cannot be final validation")
    if evidence.get("profitability_is_non_gating") is not True:
        raise RLV2SeedRobustnessError("Profitability boundary drifted")

    isolation = declaration.get("isolation", {})
    if isolation.get("phase6_authoritative_selected_model") is not None:
        raise RLV2SeedRobustnessError("Phase 6 selected_model drifted")
    if isolation.get("baseline_rerun_allowed") is not False:
        raise RLV2SeedRobustnessError("Baseline isolation drifted")
    if isolation.get("retuning_allowed") is not False:
        raise RLV2SeedRobustnessError("Retuning isolation drifted")
    return declaration


def _validate_contract(  # noqa: C901
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    paired_contract, _, _, base_config = _validate_paired_contract()
    contract = _read_json(_repo_path(CONTRACT_REPO_PATH), "seed execution contract")
    if contract.get("schema_version") != 1:
        raise RLV2SeedRobustnessError("Seed contract schema_version must be 1")
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise RLV2SeedRobustnessError("Seed contract id drifted")
    if contract.get("infrastructure_task") != INFRA_TASK_REPO_PATH:
        raise RLV2SeedRobustnessError("Infrastructure task path drifted")
    if contract.get("execution_task") != EXECUTION_TASK_REPO_PATH:
        raise RLV2SeedRobustnessError("Execution task path drifted")
    if contract.get("declaration_path") != DECLARATION_REPO_PATH:
        raise RLV2SeedRobustnessError("Declaration path drifted")
    if contract.get("declaration_merge") != EXPECTED_DECLARATION_MERGE:
        raise RLV2SeedRobustnessError("Declaration merge drifted")
    if contract.get("declaration_closure_merge") != EXPECTED_DECLARATION_CLOSURE_MERGE:
        raise RLV2SeedRobustnessError("Declaration closure merge drifted")
    if contract.get("request_path") != REQUEST_REPO_PATH:
        raise RLV2SeedRobustnessError("Request path drifted")
    if contract.get("trigger") != {
        "event": "pull_request_opened",
        "base_branch": "develop",
        "exact_one_file": True,
    }:
        raise RLV2SeedRobustnessError("Trigger contract drifted")

    anchor = contract.get("anchor_evidence", {})
    if anchor.get("seed") != ANCHOR_SEED:
        raise RLV2SeedRobustnessError("Contract anchor seed drifted")
    if anchor.get("artifact_digest") != EXPECTED_ANCHOR_DIGEST:
        raise RLV2SeedRobustnessError("Contract anchor digest drifted")
    if anchor.get("rerun_allowed") is not False:
        raise RLV2SeedRobustnessError("Contract anchor rerun boundary drifted")
    if anchor.get("valid") is not True:
        raise RLV2SeedRobustnessError("Contract anchor validity drifted")
    if anchor.get("primary_mechanism_metrics") != EXPECTED_ANCHOR_METRICS:
        raise RLV2SeedRobustnessError("Contract anchor metrics drifted")

    baseline = contract.get("baseline_evidence", {})
    if baseline.get("artifact_digest") != EXPECTED_BASELINE_DIGEST:
        raise RLV2SeedRobustnessError("Contract baseline digest drifted")
    if baseline.get("rerun_allowed") is not False:
        raise RLV2SeedRobustnessError("Contract baseline rerun boundary drifted")
    if baseline.get("primary_metrics") != EXPECTED_BASELINE_METRICS:
        raise RLV2SeedRobustnessError("Contract baseline metrics drifted")

    seed_matrix = contract.get("seed_matrix", {})
    if seed_matrix.get("ordered_seeds") != list(ORDERED_SEEDS):
        raise RLV2SeedRobustnessError("Contract ordered seeds drifted")
    if seed_matrix.get("new_execution_seeds") != list(NEW_SEEDS):
        raise RLV2SeedRobustnessError("Contract execution seeds drifted")
    if seed_matrix.get("new_variant_executions") != 4:
        raise RLV2SeedRobustnessError("Contract execution count drifted")
    if seed_matrix.get("anchor_executions") != 0:
        raise RLV2SeedRobustnessError("Contract anchor execution count drifted")
    if seed_matrix.get("baseline_executions") != 0:
        raise RLV2SeedRobustnessError("Contract baseline execution count drifted")
    if seed_matrix.get("invalid_seed_replacement_allowed") is not False:
        raise RLV2SeedRobustnessError("Invalid seed replacement boundary drifted")

    runtime = contract.get("runtime_binding", {})
    expected_runtime = {
        "freqai_model": "DesiredPositionReinforcementLearner",
        "freqai_model_path": MODEL_REPO_PATH,
        "freqai_model_sha256": EXPECTED_MODEL_SHA256,
        "strategy": "AiDesiredPositionRLLifecycleAlignedResearchStrategy",
        "strategy_path": STRATEGY_REPO_PATH,
        "strategy_sha256": EXPECTED_STRATEGY_SHA256,
        "base_config_path": BASE_CONFIG_REPO_PATH,
        "base_config_sha256": EXPECTED_CONFIG_SHA256,
        "only_behavioral_change_per_execution": "freqai.model_training_parameters.seed",
        "data_split_random_state": 42,
        "data_split_shuffle": False,
        "model_type": "PPO",
        "policy_type": "MlpPolicy",
        "n_steps": 128,
        "batch_size": 64,
        "train_cycles": 1,
        "only_lifecycle_semantic_delta": {"ignore_roi_if_entry_signal": True},
        "runtime_identifier_template": RUNTIME_IDENTIFIER_TEMPLATE,
    }
    if runtime != expected_runtime:
        raise RLV2SeedRobustnessError("Runtime binding drifted")

    geometry = contract.get("execution_geometry", {})
    expected_geometry = {
        "mode": "four_new_seed_variant_matrix",
        "download_timerange": PAIRED_EXECUTION["download_timerange"],
        "execution_timerange": PAIRED_EXECUTION["execution_timerange"],
        "semantic_evidence_window": PAIRED_EXECUTION["semantic_evidence_window"],
        "train_period_days": 90,
        "backtest_period_days": 61,
        "exchange": "kraken",
        "pairs": ["BTC/USDT", "ETH/USDT"],
        "timeframes": ["15m", "1h", "4h"],
        "fee": 0.002,
    }
    if geometry != expected_geometry:
        raise RLV2SeedRobustnessError("Execution geometry drifted")
    if contract.get("per_seed_validity_gate") != EXPECTED_VALIDITY_GATE:
        raise RLV2SeedRobustnessError("Contract per-seed validity gate drifted")
    if contract.get("mechanism_consistency_gate") != EXPECTED_MECHANISM_GATE:
        raise RLV2SeedRobustnessError("Contract mechanism gate drifted")

    evidence = contract.get("evidence", {})
    if evidence != {
        "classification": EXPECTED_CLASSIFICATION,
        "strict_oos": False,
        "protected_final_validation": False,
        "profitability_is_non_gating": True,
        "automatic_ranking": False,
        "automatic_promotion": False,
        "decision_values": ["supported", "not_supported", "inconclusive"],
    }:
        raise RLV2SeedRobustnessError("Evidence classification contract drifted")

    authorization = contract.get("authorization", {})
    required_false = {
        "infrastructure_merge_executes_model",
        "anchor_seed_execution_allowed",
        "baseline_execution_allowed",
        "strict_oos_scoring_allowed",
        "consumed_historical_oos_access_allowed",
        "protected_final_holdout_access_allowed",
        "retuning_allowed",
        "behavioral_changes_beyond_seed_allowed",
        "cross_track_selection_allowed",
        "profitability_claim_allowed",
        "statistical_proof_claim_allowed",
        "promotion_allowed",
        "live_trading_allowed",
    }
    if any(authorization.get(field) is not False for field in required_false):
        raise RLV2SeedRobustnessError("Authorization false boundary drifted")
    required_true = {
        "canonical_request_required",
        "execution_task_required_before_trigger",
        "four_new_seed_training_backtests_allowed_after_canonical_request",
        "market_data_download_allowed_after_canonical_request",
    }
    if any(authorization.get(field) is not True for field in required_true):
        raise RLV2SeedRobustnessError("Authorization true boundary drifted")

    _require_sha(BASE_CONFIG_REPO_PATH, EXPECTED_CONFIG_SHA256, "Base config")
    _require_sha(MODEL_REPO_PATH, EXPECTED_MODEL_SHA256, "FreqAI model")
    _require_sha(STRATEGY_REPO_PATH, EXPECTED_STRATEGY_SHA256, "Lifecycle strategy")

    freqai = base_config.get("freqai", {})
    if freqai.get("data_split_parameters") != {
        "test_size": 0.2,
        "random_state": 42,
        "shuffle": False,
    }:
        raise RLV2SeedRobustnessError("Data split parameters drifted")
    if freqai.get("model_training_parameters") != {
        "seed": 42,
        "n_steps": 128,
        "batch_size": 64,
    }:
        raise RLV2SeedRobustnessError("Base model training parameters drifted")
    if paired_contract["runtime_binding"]["strategy"] != runtime["strategy"]:
        raise RLV2SeedRobustnessError("Paired lifecycle strategy binding drifted")

    declaration = _validate_declaration(contract)
    return contract, declaration, base_config


def canonical_rl_v2_lifecycle_seed_robustness_request() -> dict[str, Any]:
    """Return the only request allowed for a later exact-one-file trigger PR."""
    contract, declaration, _ = _validate_contract()
    hash_inputs = {
        "contract": CONTRACT_REPO_PATH,
        "declaration": DECLARATION_REPO_PATH,
        "interpretation": INTERPRETATION_REPO_PATH,
        "config": BASE_CONFIG_REPO_PATH,
        "freqai_model": MODEL_REPO_PATH,
        "strategy": STRATEGY_REPO_PATH,
        "validator": VALIDATOR_REPO_PATH,
        "evidence": EVIDENCE_REPO_PATH,
        "workflow": WORKFLOW_REPO_PATH,
    }
    for label, path in hash_inputs.items():
        if not _repo_path(path).is_file():
            raise RLV2SeedRobustnessError(f"Canonical {label} input is missing: {path}")
    return {
        "schema_version": 1,
        "request_id": EXPECTED_REQUEST_ID,
        "action": EXPECTED_ACTION,
        "contract_path": CONTRACT_REPO_PATH,
        "contract_sha256": _sha256(_repo_path(CONTRACT_REPO_PATH)),
        "declaration_path": DECLARATION_REPO_PATH,
        "declaration_sha256": _sha256(_repo_path(DECLARATION_REPO_PATH)),
        "interpretation_path": INTERPRETATION_REPO_PATH,
        "interpretation_sha256": _sha256(_repo_path(INTERPRETATION_REPO_PATH)),
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
        "evidence_path": EVIDENCE_REPO_PATH,
        "evidence_sha256": _sha256(_repo_path(EVIDENCE_REPO_PATH)),
        "workflow_path": WORKFLOW_REPO_PATH,
        "workflow_sha256": _sha256(_repo_path(WORKFLOW_REPO_PATH)),
        "execution_task_path": EXECUTION_TASK_REPO_PATH,
        "anchor_seed": ANCHOR_SEED,
        "anchor_artifact_name": contract["anchor_evidence"]["artifact_name"],
        "anchor_artifact_digest": contract["anchor_evidence"]["artifact_digest"],
        "anchor_seed_rerun_allowed": False,
        "new_execution_seeds": list(NEW_SEEDS),
        "new_variant_execution_count": 4,
        "baseline_rerun_allowed": False,
        "download_timerange": contract["execution_geometry"]["download_timerange"],
        "execution_timerange": contract["execution_geometry"]["execution_timerange"],
        "semantic_evidence_window": contract["execution_geometry"]["semantic_evidence_window"],
        "train_period_days": contract["execution_geometry"]["train_period_days"],
        "backtest_period_days": contract["execution_geometry"]["backtest_period_days"],
        "pairs": list(contract["execution_geometry"]["pairs"]),
        "timeframes": list(contract["execution_geometry"]["timeframes"]),
        "fee": contract["execution_geometry"]["fee"],
        "per_seed_validity_gate": deepcopy(contract["per_seed_validity_gate"]),
        "mechanism_consistency_gate": deepcopy(contract["mechanism_consistency_gate"]),
        "evidence_classification": EXPECTED_CLASSIFICATION,
        "strict_oos": False,
        "protected_final_validation": False,
        "profitability_is_non_gating": True,
        "consumed_historical_oos": "20260501-20260630",
        "protected_final_holdout": "20260801-20260930",
        "authorization": deepcopy(contract["authorization"]),
        "declaration_status": declaration["status"],
    }


def load_rl_v2_lifecycle_seed_robustness_request(path: Path) -> dict[str, Any]:
    """Load and fail closed unless a request exactly equals the canonical payload."""
    request = _read_json(path.resolve(), "seed-robustness request")
    expected = canonical_rl_v2_lifecycle_seed_robustness_request()
    if set(request) != set(expected):
        missing = sorted(set(expected) - set(request))
        extra = sorted(set(request) - set(expected))
        raise RLV2SeedRobustnessError(
            f"Canonical request fields drifted: missing={missing}; extra={extra}"
        )
    for field, expected_value in expected.items():
        if request[field] != expected_value:
            raise RLV2SeedRobustnessError(f"Request field {field} drifted from canonical payload")
    return request


def materialize_seed_runtime_config(output: Path, seed: int) -> Path:
    """Write one isolated runtime config changing only the frozen execution seed."""
    validate_new_seed(seed)
    contract, _, base_config = _validate_contract()
    output = output.resolve()
    if output == _repo_path(BASE_CONFIG_REPO_PATH):
        raise RLV2SeedRobustnessError("Refusing to overwrite immutable base config")

    runtime_config = deepcopy(base_config)
    runtime_config["strategy"] = contract["runtime_binding"]["strategy"]
    freqai = runtime_config.setdefault("freqai", {})
    freqai["identifier"] = runtime_identifier(seed)
    freqai["train_period_days"] = contract["execution_geometry"]["train_period_days"]
    freqai["backtest_period_days"] = contract["execution_geometry"]["backtest_period_days"]
    training = freqai.setdefault("model_training_parameters", {})
    training["seed"] = seed
    if freqai.get("data_split_parameters") != {
        "test_size": 0.2,
        "random_state": 42,
        "shuffle": False,
    }:
        raise RLV2SeedRobustnessError("Materialized data split drifted")
    if "timerange" in runtime_config or "live_retrain_hours" in freqai:
        raise RLV2SeedRobustnessError("Temporary config introduced unauthorized geometry")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(runtime_config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


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
            print(
                json.dumps(
                    canonical_rl_v2_lifecycle_seed_robustness_request(),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.materialize_config is not None:
            if args.seed is None:
                raise RLV2SeedRobustnessError("--seed is required with --materialize-config")
            print(materialize_seed_runtime_config(args.materialize_config, args.seed))
            return 0
        if args.verify_data is not None:
            payload = verify_downloaded_data(args.verify_data, pairs=args.pairs)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.request is None:
            _validate_contract()
            return 0
        load_rl_v2_lifecycle_seed_robustness_request(args.request)
        return 0
    except (RLV2SeedRobustnessError, RLV2PairedAttributionError) as exc:
        print(f"RL-v2 seed robustness validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
