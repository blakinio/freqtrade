#!/usr/bin/env python3
"""Extract deterministic RL-v2 lifecycle paired-attribution evidence."""

from __future__ import annotations

import argparse
import json
import math
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_run_request import (
    EXPECTED_BASELINE_METRICS,
    EXPECTED_CLASSIFICATION,
    EXPECTED_EXECUTION,
    EXPECTED_RUNTIME_IDENTIFIER,
    RLV2PairedAttributionError,
    _validate_contract,
)


EXPECTED_STRATEGY = "AiDesiredPositionRLLifecycleAlignedResearchStrategy"
EXPECTED_MODEL = "DesiredPositionReinforcementLearner"
IMMEDIATE_REENTRY_MILLISECONDS = 15 * 60 * 1000
EXTERNAL_EXIT_REASONS = {"roi", "stop_loss"}


class RLV2PairedEvidenceError(RuntimeError):
    """Raised when raw paired-attribution evidence is malformed or drifts."""


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise RLV2PairedEvidenceError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise RLV2PairedEvidenceError(f"{label} must be finite")
    return result


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RLV2PairedEvidenceError(f"{label} must be an integer")
    return value


def _load_backtest_result(archive: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(archive) as bundle:
            result_names = sorted(
                name
                for name in bundle.namelist()
                if name.endswith(".json") and not name.endswith("_config.json")
            )
            if len(result_names) != 1:
                raise RLV2PairedEvidenceError(
                    "Expected exactly one non-config backtest result JSON, "
                    f"found {len(result_names)}"
                )
            payload = json.loads(bundle.read(result_names[0]))
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        raise RLV2PairedEvidenceError(
            f"Unable to read raw backtest archive {archive}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RLV2PairedEvidenceError("Backtest result root must be an object")
    return payload


def _strategy_result(payload: dict[str, Any]) -> dict[str, Any]:
    strategies = payload.get("strategy")
    if not isinstance(strategies, dict):
        raise RLV2PairedEvidenceError("Backtest result is missing strategy mapping")
    if set(strategies) != {EXPECTED_STRATEGY}:
        raise RLV2PairedEvidenceError(
            "Backtest archive must contain only the lifecycle-aligned strategy"
        )
    result = strategies[EXPECTED_STRATEGY]
    if not isinstance(result, dict):
        raise RLV2PairedEvidenceError("Strategy result must be an object")
    return result


def _validate_summary(result: dict[str, Any]) -> None:
    if result.get("strategy_name") != EXPECTED_STRATEGY:
        raise RLV2PairedEvidenceError("Strategy name drifted")
    if result.get("freqaimodel") != EXPECTED_MODEL:
        raise RLV2PairedEvidenceError("FreqAI model drifted")
    if result.get("freqai_identifier") != EXPECTED_RUNTIME_IDENTIFIER:
        raise RLV2PairedEvidenceError("Isolated FreqAI identifier drifted")
    if result.get("ignore_roi_if_entry_signal") is not True:
        raise RLV2PairedEvidenceError(
            "Lifecycle-aligned strategy flag is not present in backtest result"
        )
    if result.get("timerange") != EXPECTED_EXECUTION["execution_timerange"]:
        raise RLV2PairedEvidenceError("Execution timerange drifted")
    if result.get("timeframe") != "15m":
        raise RLV2PairedEvidenceError("Base timeframe drifted")
    if result.get("trading_mode") != "spot":
        raise RLV2PairedEvidenceError("Trading mode drifted")
    if result.get("trade_count_short") not in (0, None):
        raise RLV2PairedEvidenceError("Short trades are forbidden")
    if result.get("minimal_roi") != {"0": 0.03, "240": 0.015, "720": 0.0}:
        raise RLV2PairedEvidenceError("Inherited ROI schedule drifted")
    if _finite_number(result.get("stoploss"), "stoploss") != -0.05:
        raise RLV2PairedEvidenceError("Hard stop-loss drifted")
    if result.get("use_exit_signal") is not True:
        raise RLV2PairedEvidenceError("Exit-signal behavior drifted")


def _fee_amount(trade: dict[str, Any], side: str) -> float:
    amount = _finite_number(trade.get("amount"), "trade amount")
    rate = _finite_number(trade.get(f"{side}_rate"), f"{side} rate")
    fee = _finite_number(trade.get(f"fee_{side}"), f"{side} fee")
    if amount < 0 or rate < 0 or fee < 0:
        raise RLV2PairedEvidenceError("Trade amount, rate and fees must be non-negative")
    return amount * rate * fee


def _validated_trades(result: dict[str, Any]) -> list[dict[str, Any]]:
    trades = result.get("trades")
    if not isinstance(trades, list):
        raise RLV2PairedEvidenceError("Strategy result trades must be a list")
    validated: list[dict[str, Any]] = []
    for index, trade in enumerate(trades):
        if not isinstance(trade, dict):
            raise RLV2PairedEvidenceError(f"Trade {index} must be an object")
        pair = trade.get("pair")
        if pair not in {"BTC/USDT", "ETH/USDT"}:
            raise RLV2PairedEvidenceError(f"Trade {index} pair drifted: {pair}")
        if trade.get("is_short") is not False:
            raise RLV2PairedEvidenceError(f"Trade {index} violates long-only scope")
        open_ts = _integer(trade.get("open_timestamp"), f"trade {index} open timestamp")
        close_ts = _integer(trade.get("close_timestamp"), f"trade {index} close timestamp")
        if close_ts < open_ts:
            raise RLV2PairedEvidenceError(f"Trade {index} closes before it opens")
        open_rate = _finite_number(trade.get("open_rate"), f"trade {index} open rate")
        close_rate = _finite_number(trade.get("close_rate"), f"trade {index} close rate")
        amount = _finite_number(trade.get("amount"), f"trade {index} amount")
        gross = amount * (close_rate - open_rate)
        fees = _fee_amount(trade, "open") + _fee_amount(trade, "close")
        net = _finite_number(trade.get("profit_abs"), f"trade {index} profit_abs")
        if not math.isclose(gross - fees, net, rel_tol=1e-8, abs_tol=1e-6):
            raise RLV2PairedEvidenceError(f"Trade {index} accounting does not reconcile")
        if not isinstance(trade.get("exit_reason"), str):
            raise RLV2PairedEvidenceError(f"Trade {index} exit reason is missing")
        validated.append(trade)
    if _integer(result.get("total_trades"), "total_trades") != len(validated):
        raise RLV2PairedEvidenceError("Trade count summary does not match raw trades")
    return validated


def _next_same_pair_trade(
    trades_by_pair: dict[str, list[dict[str, Any]]],
    pair: str,
    current_index: int,
) -> dict[str, Any] | None:
    current = trades_by_pair[pair][current_index]
    close_ts = int(current["close_timestamp"])
    for candidate in trades_by_pair[pair][current_index + 1 :]:
        if int(candidate["open_timestamp"]) > close_ts:
            return candidate
    return None


def _trade_metrics(trades: list[dict[str, Any]], result: dict[str, Any]) -> dict[str, Any]:
    gross_price_pnl = 0.0
    fees = 0.0
    net_profit = 0.0
    exit_counts: Counter[str] = Counter()
    trades_by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for trade in trades:
        amount = float(trade["amount"])
        gross_price_pnl += amount * (float(trade["close_rate"]) - float(trade["open_rate"]))
        fees += _fee_amount(trade, "open") + _fee_amount(trade, "close")
        net_profit += float(trade["profit_abs"])
        exit_counts[str(trade["exit_reason"])] += 1
        trades_by_pair[str(trade["pair"])].append(trade)

    for pair in trades_by_pair:
        trades_by_pair[pair].sort(key=lambda trade: int(trade["open_timestamp"]))

    roi_15m_reentries = 0
    immediate_external_boundaries = 0
    boundary_fees = 0.0
    for pair, pair_trades in trades_by_pair.items():
        for index, trade in enumerate(pair_trades):
            next_trade = _next_same_pair_trade(trades_by_pair, pair, index)
            if next_trade is None:
                continue
            gap = int(next_trade["open_timestamp"]) - int(trade["close_timestamp"])
            if gap != IMMEDIATE_REENTRY_MILLISECONDS:
                continue
            exit_reason = str(trade["exit_reason"])
            if exit_reason == "roi":
                roi_15m_reentries += 1
            if exit_reason in EXTERNAL_EXIT_REASONS:
                immediate_external_boundaries += 1
                boundary_fees += _fee_amount(trade, "close")
                boundary_fees += _fee_amount(next_trade, "open")

    rounded_boundary_fees = round(boundary_fees, 6)
    primary = {
        "roi_exit_followed_by_same_pair_15m_reentry_count": roi_15m_reentries,
        "immediate_external_exit_reentry_boundary_count": immediate_external_boundaries,
        "external_exit_reentry_boundary_fee_usdt": rounded_boundary_fees,
    }
    primary_support = {
        "roi_15m_reentry_count_reduced": (
            roi_15m_reentries
            < int(EXPECTED_BASELINE_METRICS["roi_exit_followed_by_same_pair_15m_reentry_count"])
        ),
        "boundary_fee_reduced": (
            rounded_boundary_fees
            < float(EXPECTED_BASELINE_METRICS["external_exit_reentry_boundary_fee_usdt"])
        ),
    }
    primary_support["all_required_criteria_met"] = all(primary_support.values())

    return {
        "trade_count": len(trades),
        "gross_price_pnl_usdt": round(gross_price_pnl, 6),
        "fees_usdt": round(fees, 6),
        "net_profit_usdt": round(net_profit, 6),
        "profit_factor": round(_finite_number(result.get("profit_factor"), "profit factor"), 6),
        "max_drawdown_abs": round(
            _finite_number(result.get("max_drawdown_abs"), "max drawdown abs"),
            6,
        ),
        "roi_exit_count": exit_counts["roi"],
        "target_flat_exit_count": exit_counts["freqai_rl_v2_target_flat"],
        "stop_loss_exit_count": exit_counts["stop_loss"],
        "force_exit_count": exit_counts["force_exit"],
        "primary_mechanism_metrics": primary,
        "primary_directional_support": primary_support,
    }


def extract_paired_attribution(archive: Path) -> dict[str, Any]:
    """Extract the only prospectively defined paired-attribution payload."""
    contract, diagnosis, _, _ = _validate_contract()
    result = _strategy_result(_load_backtest_result(archive))
    _validate_summary(result)
    trades = _validated_trades(result)
    variant_metrics = _trade_metrics(trades, result)

    baseline_metrics = dict(EXPECTED_BASELINE_METRICS)
    baseline_descriptive = {
        "trade_count": diagnosis["overall"]["trades"],
        "gross_price_pnl_usdt": diagnosis["overall"]["gross_price_pnl_usdt"],
        "fees_usdt": diagnosis["overall"]["fees_usdt"],
        "net_profit_usdt": diagnosis["overall"]["net_profit_usdt"],
        "roi_exit_count": diagnosis["by_exit_reason"]["roi"]["trades"],
        "target_flat_exit_count": diagnosis["by_exit_reason"]["freqai_rl_v2_target_flat"]["trades"],
        "stop_loss_exit_count": diagnosis["by_exit_reason"]["stop_loss"]["trades"],
    }
    variant_primary = variant_metrics["primary_mechanism_metrics"]
    comparison = {
        "roi_exit_followed_by_same_pair_15m_reentry_count_delta": (
            variant_primary["roi_exit_followed_by_same_pair_15m_reentry_count"]
            - int(baseline_metrics["roi_exit_followed_by_same_pair_15m_reentry_count"])
        ),
        "immediate_external_exit_reentry_boundary_count_delta": (
            variant_primary["immediate_external_exit_reentry_boundary_count"]
            - int(baseline_metrics["immediate_external_exit_reentry_boundary_count"])
        ),
        "external_exit_reentry_boundary_fee_usdt_delta": round(
            float(variant_primary["external_exit_reentry_boundary_fee_usdt"])
            - float(baseline_metrics["external_exit_reentry_boundary_fee_usdt"]),
            6,
        ),
    }

    return {
        "schema_version": 1,
        "evidence_id": "rl-v2-roi-lifecycle-paired-attribution-v1",
        "classification": EXPECTED_CLASSIFICATION,
        "strict_oos": False,
        "protected_final_validation": False,
        "profitability_is_non_gating": True,
        "automatic_ranking": False,
        "automatic_promotion": False,
        "baseline_rerun": False,
        "baseline": {
            "artifact_name": contract["baseline_evidence"]["artifact_name"],
            "artifact_digest": contract["baseline_evidence"]["artifact_digest"],
            "diagnosis_path": contract["baseline_evidence"]["diagnosis_path"],
            "primary_mechanism_metrics": baseline_metrics,
            "secondary_descriptive_metrics": baseline_descriptive,
        },
        "variant": {
            "strategy": EXPECTED_STRATEGY,
            "strategy_sha256": contract["runtime_binding"]["strategy_sha256"],
            "runtime_identifier": EXPECTED_RUNTIME_IDENTIFIER,
            "only_semantic_delta": {"ignore_roi_if_entry_signal": True},
            "execution_timerange": EXPECTED_EXECUTION["execution_timerange"],
            "semantic_evidence_window": EXPECTED_EXECUTION["semantic_evidence_window"],
            **variant_metrics,
        },
        "comparison": comparison,
        "directional_hypothesis_supported": variant_metrics["primary_directional_support"][
            "all_required_criteria_met"
        ],
        "interpretation": (
            "Mechanistic paired historical-development attribution only. "
            "Directional support is based exclusively on both prospectively frozen "
            "churn criteria; net profitability is descriptive and non-gating."
        ),
        "consumed_historical_oos_accessed": False,
        "protected_final_holdout_accessed": False,
        "frozen_entry_prediction_threshold": 0.006,
        "frozen_exit_prediction_threshold": -0.009,
        "phase6_authoritative_selected_model": None,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        payload = extract_paired_attribution(args.archive.resolve())
        rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.output is None:
            print(rendered, end="")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        return 0
    except (RLV2PairedAttributionError, RLV2PairedEvidenceError) as exc:
        print(f"RL-v2 paired evidence extraction failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
