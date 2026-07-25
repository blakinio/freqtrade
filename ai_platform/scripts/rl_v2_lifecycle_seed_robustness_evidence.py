#!/usr/bin/env python3
"""Extract and aggregate RL-v2 lifecycle seed-robustness evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import zipfile
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from ai_platform.scripts.rl_v2_lifecycle_seed_robustness_run_request import (
    ANCHOR_SEED,
    EXPECTED_CLASSIFICATION,
    EXPECTED_MECHANISM_GATE,
    EXPECTED_VALIDITY_GATE,
    NEW_SEEDS,
    ORDERED_SEEDS,
    RLV2SeedRobustnessError,
    _validate_contract,
    runtime_identifier,
    validate_new_seed,
)
from ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_evidence import (
    EXPECTED_MODEL,
    EXPECTED_STRATEGY,
    RLV2PairedEvidenceError,
    _finite_number,
    _integer,
    _load_backtest_result,
    _strategy_result,
    _trade_metrics,
    _validated_trades,
)
from ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_run_request import (
    EXPECTED_EXECUTION,
    RLV2PairedAttributionError,
)


EXPECTED_PAIRS = ("BTC/USDT", "ETH/USDT")


class RLV2SeedEvidenceError(RuntimeError):
    """Raised when per-seed or aggregate evidence is malformed."""


def _summary_counter(result: dict[str, Any], field: str) -> int:
    value = result.get(field)
    return _integer(value, field)


def _validate_seed_summary(result: dict[str, Any], seed: int) -> None:
    if result.get("strategy_name") != EXPECTED_STRATEGY:
        raise RLV2SeedEvidenceError("Strategy name drifted")
    if result.get("freqaimodel") != EXPECTED_MODEL:
        raise RLV2SeedEvidenceError("FreqAI model drifted")
    if result.get("freqai_identifier") != runtime_identifier(seed):
        raise RLV2SeedEvidenceError("Seed runtime identifier drifted")
    if result.get("ignore_roi_if_entry_signal") is not True:
        raise RLV2SeedEvidenceError("Lifecycle alignment flag drifted")
    if result.get("timerange") != EXPECTED_EXECUTION["execution_timerange"]:
        raise RLV2SeedEvidenceError("Execution timerange drifted")
    if result.get("timeframe") != "15m":
        raise RLV2SeedEvidenceError("Base timeframe drifted")
    if result.get("trading_mode") != "spot":
        raise RLV2SeedEvidenceError("Trading mode drifted")
    if result.get("trade_count_short") not in (0, None):
        raise RLV2SeedEvidenceError("Short trades are forbidden")
    if result.get("minimal_roi") != {"0": 0.03, "240": 0.015, "720": 0.0}:
        raise RLV2SeedEvidenceError("Inherited ROI schedule drifted")
    if _finite_number(result.get("stoploss"), "stoploss") != -0.05:
        raise RLV2SeedEvidenceError("Hard stop-loss drifted")
    if result.get("use_exit_signal") is not True:
        raise RLV2SeedEvidenceError("Exit-signal behavior drifted")


def _load_backtest_config(archive: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(archive) as bundle:
            names = sorted(name for name in bundle.namelist() if name.endswith("_config.json"))
            if len(names) != 1:
                raise RLV2SeedEvidenceError(
                    f"Expected exactly one backtest config JSON, found {len(names)}"
                )
            payload = json.loads(bundle.read(names[0]))
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        raise RLV2SeedEvidenceError(
            f"Unable to read backtest config from {archive}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RLV2SeedEvidenceError("Backtest config root must be an object")
    return payload


def _expected_runtime_config(
    base_config: dict[str, Any],
    contract: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    expected = deepcopy(base_config)
    expected["strategy"] = contract["runtime_binding"]["strategy"]
    freqai = expected.setdefault("freqai", {})
    freqai["identifier"] = runtime_identifier(seed)
    freqai["train_period_days"] = contract["execution_geometry"]["train_period_days"]
    freqai["backtest_period_days"] = contract["execution_geometry"]["backtest_period_days"]
    freqai.setdefault("model_training_parameters", {})["seed"] = seed
    return expected


def _validate_archive_config(
    archive: Path,
    base_config: dict[str, Any],
    contract: dict[str, Any],
    seed: int,
) -> str:
    embedded = _load_backtest_config(archive)
    expected = _expected_runtime_config(base_config, contract, seed)

    embedded.pop("config_files", None)
    expected.pop("config_files", None)
    embedded_exchange = embedded.get("exchange")
    expected_exchange = expected.get("exchange")
    if not isinstance(embedded_exchange, dict) or not isinstance(expected_exchange, dict):
        raise RLV2SeedEvidenceError("Backtest exchange config is missing")
    for field in ("key", "secret"):
        value = embedded_exchange.get(field)
        if value not in (None, "", "REDACTED"):
            raise RLV2SeedEvidenceError(f"Unexpected embedded exchange {field} value")
        embedded_exchange[field] = expected_exchange.get(field, "")

    if embedded != expected:
        raise RLV2SeedEvidenceError(f"Backtest archive config drifted for seed {seed}")
    rendered = json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(rendered).hexdigest()


def _mechanism_support(
    primary: dict[str, Any],
) -> tuple[dict[str, bool], dict[str, bool]]:
    original = EXPECTED_MECHANISM_GATE["original_directional_criteria_per_seed"]
    strong = EXPECTED_MECHANISM_GATE["strong_reduction_criteria"]
    original_support = {
        "roi_15m_reentry_count_reduced": (
            int(primary["roi_exit_followed_by_same_pair_15m_reentry_count"])
            < int(original["roi_exit_followed_by_same_pair_15m_reentry_count_lt"])
        ),
        "boundary_fee_reduced": (
            float(primary["external_exit_reentry_boundary_fee_usdt"])
            < float(original["external_exit_reentry_boundary_fee_usdt_lt"])
        ),
    }
    original_support["all_required_criteria_met"] = all(original_support.values())
    strong_support = {
        "roi_15m_reentry_count_strongly_reduced": (
            int(primary["roi_exit_followed_by_same_pair_15m_reentry_count"])
            <= int(strong["roi_exit_followed_by_same_pair_15m_reentry_count_lte"])
        ),
        "boundary_fee_strongly_reduced": (
            float(primary["external_exit_reentry_boundary_fee_usdt"])
            <= float(strong["external_exit_reentry_boundary_fee_usdt_lte"])
        ),
    }
    strong_support["all_strong_criteria_met"] = all(strong_support.values())
    return original_support, strong_support


def extract_seed_evidence(archive: Path, seed: int) -> dict[str, Any]:
    """Extract one new seed and apply the prospectively frozen validity gate."""
    validate_new_seed(seed)
    contract, _, base_config = _validate_contract()
    runtime_config_sha256 = _validate_archive_config(
        archive,
        base_config,
        contract,
        seed,
    )
    result = _strategy_result(_load_backtest_result(archive))
    _validate_seed_summary(result, seed)
    trades = _validated_trades(result)
    metrics = _trade_metrics(trades, result)

    pair_counts = Counter(str(trade["pair"]) for trade in trades)
    rejected_signals = _summary_counter(result, "rejected_signals")
    timed_out_entry_orders = _summary_counter(result, "timedout_entry_orders")
    timed_out_exit_orders = _summary_counter(result, "timedout_exit_orders")

    validity_reasons: list[str] = []
    minimum_pair_trades = int(EXPECTED_VALIDITY_GATE["both_pairs_minimum_completed_trades_each"])
    for pair in EXPECTED_PAIRS:
        if pair_counts[pair] < minimum_pair_trades:
            validity_reasons.append(
                f"{pair} completed trades {pair_counts[pair]} < {minimum_pair_trades}"
            )
    if metrics["trade_count"] < int(EXPECTED_VALIDITY_GATE["minimum_total_trade_count"]):
        validity_reasons.append(
            "total trade count "
            f"{metrics['trade_count']} < {EXPECTED_VALIDITY_GATE['minimum_total_trade_count']}"
        )
    if metrics["target_flat_exit_count"] < int(
        EXPECTED_VALIDITY_GATE["minimum_target_flat_exit_count"]
    ):
        validity_reasons.append(
            "target-flat exit count "
            f"{metrics['target_flat_exit_count']} < "
            f"{EXPECTED_VALIDITY_GATE['minimum_target_flat_exit_count']}"
        )
    if rejected_signals > int(EXPECTED_VALIDITY_GATE["maximum_rejected_signals"]):
        validity_reasons.append("rejected signal count exceeded the frozen maximum")
    if timed_out_entry_orders > int(EXPECTED_VALIDITY_GATE["maximum_timed_out_entry_orders"]):
        validity_reasons.append("timed-out entry orders exceeded the frozen maximum")
    if timed_out_exit_orders > int(EXPECTED_VALIDITY_GATE["maximum_timed_out_exit_orders"]):
        validity_reasons.append("timed-out exit orders exceeded the frozen maximum")

    primary = metrics["primary_mechanism_metrics"]
    original_support, strong_support = _mechanism_support(primary)

    return {
        "schema_version": 1,
        "evidence_id": f"rl-v2-lifecycle-seed-robustness-v1-seed-{seed}",
        "classification": EXPECTED_CLASSIFICATION,
        "strict_oos": False,
        "protected_final_validation": False,
        "profitability_is_non_gating": True,
        "automatic_ranking": False,
        "automatic_promotion": False,
        "seed": seed,
        "anchor_seed": False,
        "runtime_identifier": runtime_identifier(seed),
        "strategy": EXPECTED_STRATEGY,
        "strategy_sha256": contract["runtime_binding"]["strategy_sha256"],
        "freqai_model": EXPECTED_MODEL,
        "freqai_model_sha256": contract["runtime_binding"]["freqai_model_sha256"],
        "runtime_config_sha256": runtime_config_sha256,
        "runtime_hashes_reconciled": True,
        "execution_timerange": contract["execution_geometry"]["execution_timerange"],
        "semantic_evidence_window": contract["execution_geometry"]["semantic_evidence_window"],
        "valid": not validity_reasons,
        "validity_reasons": validity_reasons,
        "pair_trade_counts": {pair: pair_counts[pair] for pair in EXPECTED_PAIRS},
        "rejected_signals": rejected_signals,
        "timed_out_entry_orders": timed_out_entry_orders,
        "timed_out_exit_orders": timed_out_exit_orders,
        "primary_mechanism_metrics": primary,
        "original_directional_support": original_support,
        "strong_reduction_support": strong_support,
        "descriptive_metrics": {
            key: metrics[key]
            for key in (
                "trade_count",
                "gross_price_pnl_usdt",
                "fees_usdt",
                "net_profit_usdt",
                "profit_factor",
                "max_drawdown_abs",
                "roi_exit_count",
                "target_flat_exit_count",
                "stop_loss_exit_count",
                "force_exit_count",
            )
        },
        "baseline_rerun": False,
        "anchor_seed_rerun": False,
        "consumed_historical_oos_accessed": False,
        "protected_final_holdout_accessed": False,
        "phase6_authoritative_selected_model": None,
    }


def _load_seed_evidence(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RLV2SeedEvidenceError(f"Unable to read seed evidence {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RLV2SeedEvidenceError(f"Seed evidence must be an object: {path}")
    return payload


def _anchor_evidence(contract: dict[str, Any]) -> dict[str, Any]:
    anchor = contract["anchor_evidence"]
    return {
        "seed": ANCHOR_SEED,
        "anchor_seed": True,
        "valid": True,
        "validity_reasons": [],
        "primary_mechanism_metrics": dict(anchor["primary_mechanism_metrics"]),
        "original_directional_support": {
            "roi_15m_reentry_count_reduced": True,
            "boundary_fee_reduced": True,
            "all_required_criteria_met": True,
        },
        "strong_reduction_support": {
            "roi_15m_reentry_count_strongly_reduced": True,
            "boundary_fee_strongly_reduced": True,
            "all_strong_criteria_met": True,
        },
        "descriptive_metrics": dict(anchor["descriptive_metrics"]),
        "artifact_name": anchor["artifact_name"],
        "artifact_digest": anchor["artifact_digest"],
        "workflow_run_id": anchor["workflow_run_id"],
        "execution_head_sha": anchor["execution_head_sha"],
        "rerun": False,
    }


def aggregate_seed_evidence(  # noqa: C901
    paths: list[Path],
) -> dict[str, Any]:
    """Combine exactly four new seeds with the immutable seed-42 anchor."""
    contract, _, _ = _validate_contract()
    if len(paths) != len(NEW_SEEDS):
        raise RLV2SeedEvidenceError(
            f"Expected exactly {len(NEW_SEEDS)} new seed evidence files, got {len(paths)}"
        )

    by_seed: dict[int, dict[str, Any]] = {}
    for path in paths:
        payload = _load_seed_evidence(path)
        seed = payload.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise RLV2SeedEvidenceError(f"Seed evidence has invalid seed: {path}")
        validate_new_seed(seed)
        if seed in by_seed:
            raise RLV2SeedEvidenceError(f"Duplicate seed evidence: {seed}")
        if payload.get("classification") != EXPECTED_CLASSIFICATION:
            raise RLV2SeedEvidenceError(f"Seed classification drifted: {seed}")
        if payload.get("strict_oos") is not False:
            raise RLV2SeedEvidenceError(f"Seed strict-OOS flag drifted: {seed}")
        if payload.get("protected_final_validation") is not False:
            raise RLV2SeedEvidenceError(f"Seed final-validation flag drifted: {seed}")
        if payload.get("profitability_is_non_gating") is not True:
            raise RLV2SeedEvidenceError(f"Seed profitability boundary drifted: {seed}")
        if payload.get("baseline_rerun") is not False:
            raise RLV2SeedEvidenceError(f"Seed baseline rerun flag drifted: {seed}")
        if payload.get("anchor_seed_rerun") is not False:
            raise RLV2SeedEvidenceError(f"Seed anchor rerun flag drifted: {seed}")
        if payload.get("consumed_historical_oos_accessed") is not False:
            raise RLV2SeedEvidenceError(f"Seed consumed OOS flag drifted: {seed}")
        if payload.get("protected_final_holdout_accessed") is not False:
            raise RLV2SeedEvidenceError(f"Seed protected holdout flag drifted: {seed}")
        if not isinstance(payload.get("valid"), bool):
            raise RLV2SeedEvidenceError(f"Seed validity flag is malformed: {seed}")
        if not isinstance(payload.get("validity_reasons"), list):
            raise RLV2SeedEvidenceError(f"Seed validity reasons are malformed: {seed}")
        primary = payload.get("primary_mechanism_metrics")
        if not isinstance(primary, dict):
            raise RLV2SeedEvidenceError(f"Seed primary metrics are missing: {seed}")
        expected_original, expected_strong = _mechanism_support(primary)
        if payload.get("original_directional_support") != expected_original:
            raise RLV2SeedEvidenceError(f"Seed original support drifted: {seed}")
        if payload.get("strong_reduction_support") != expected_strong:
            raise RLV2SeedEvidenceError(f"Seed strong support drifted: {seed}")
        by_seed[seed] = payload

    if set(by_seed) != set(NEW_SEEDS):
        missing = sorted(set(NEW_SEEDS) - set(by_seed))
        extra = sorted(set(by_seed) - set(NEW_SEEDS))
        raise RLV2SeedEvidenceError(
            f"Frozen seed evidence set drifted: missing={missing}; extra={extra}"
        )

    entries = [_anchor_evidence(contract)] + [by_seed[seed] for seed in NEW_SEEDS]
    invalid = [entry["seed"] for entry in entries if entry.get("valid") is not True]
    original_pass_count = sum(
        entry["original_directional_support"]["all_required_criteria_met"] for entry in entries
    )
    strong_pass_count = sum(
        entry["strong_reduction_support"]["all_strong_criteria_met"] for entry in entries
    )
    required_original = int(
        EXPECTED_MECHANISM_GATE["original_directional_criteria_per_seed"]["required_seed_count"]
    )
    required_strong = int(
        EXPECTED_MECHANISM_GATE["strong_reduction_criteria"]["minimum_seed_count_meeting_both"]
    )
    if invalid:
        decision = "inconclusive"
    elif original_pass_count == required_original and strong_pass_count >= required_strong:
        decision = "supported"
    else:
        decision = "not_supported"

    descriptive_names = (
        "trade_count",
        "gross_price_pnl_usdt",
        "fees_usdt",
        "net_profit_usdt",
        "profit_factor",
        "max_drawdown_abs",
    )
    descriptive: dict[str, Any] = {}
    for name in descriptive_names:
        values = [
            entry["descriptive_metrics"][name]
            for entry in entries
            if name in entry["descriptive_metrics"]
        ]
        descriptive[name] = {
            "values_by_seed": {
                str(entry["seed"]): entry["descriptive_metrics"].get(name) for entry in entries
            },
            "median": round(float(statistics.median(values)), 6) if values else None,
            "gating": False,
        }

    return {
        "schema_version": 1,
        "evidence_id": "rl-v2-lifecycle-seed-robustness-v1",
        "classification": EXPECTED_CLASSIFICATION,
        "strict_oos": False,
        "protected_final_validation": False,
        "profitability_is_non_gating": True,
        "automatic_ranking": False,
        "automatic_promotion": False,
        "ordered_seeds": list(ORDERED_SEEDS),
        "anchor_seed_reused": ANCHOR_SEED,
        "anchor_seed_rerun": False,
        "baseline_rerun": False,
        "new_seed_execution_count": len(NEW_SEEDS),
        "invalid_seed_replacement_allowed": False,
        "per_seed": entries,
        "valid_seed_count": len(entries) - len(invalid),
        "invalid_seeds": invalid,
        "original_directional_pass_count": original_pass_count,
        "strong_reduction_pass_count": strong_pass_count,
        "required_original_directional_pass_count": required_original,
        "required_strong_reduction_pass_count": required_strong,
        "decision": decision,
        "descriptive_only": descriptive,
        "consumed_historical_oos_accessed": False,
        "protected_final_holdout_accessed": False,
        "phase6_authoritative_selected_model": None,
        "interpretation": (
            "Seed robustness on reused historical-development data only. The decision is "
            "mechanism-consistency evidence and cannot establish profitability, statistical proof, "
            "ranking, promotion or deployment readiness."
        ),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser("extract")
    extract.add_argument("archive", type=Path)
    extract.add_argument("--seed", type=int, required=True)
    extract.add_argument("--output", type=Path)

    aggregate = subparsers.add_parser("aggregate")
    aggregate.add_argument("evidence", nargs="+", type=Path)
    aggregate.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def _write_payload(payload: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(rendered, end="")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.command == "extract":
            _write_payload(
                extract_seed_evidence(args.archive.resolve(), args.seed),
                args.output,
            )
            return 0
        _write_payload(
            aggregate_seed_evidence([path.resolve() for path in args.evidence]),
            args.output,
        )
        return 0
    except (
        RLV2SeedRobustnessError,
        RLV2SeedEvidenceError,
        RLV2PairedAttributionError,
        RLV2PairedEvidenceError,
    ) as exc:
        print(f"RL-v2 seed robustness evidence failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
