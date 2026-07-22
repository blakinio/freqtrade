#!/usr/bin/env python3
"""Fail-closed contract and evidence helpers for the TradingView futures benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "ai_platform/research/tradingview/futures-historical-benchmark-v1.json"
BENCHMARK_ID = "tradingview-futures-historical-benchmark-v1"
PREFLIGHT_ID = "tradingview-futures-historical-preflight-v1"
EXPECTED_CANDIDATES = [
    "TVDonchianBreakoutStrategy",
    "TVSupertrendStrategy",
    "TVBollingerMeanReversionStrategy",
]
EXPECTED_PAIRS = ["BTC/USD:USD", "ETH/USD:USD"]
EXPECTED_MARKET_IDS = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD"}
EXPECTED_TIMERANGE = "20260301-20260701"
EXPECTED_DOWNLOAD_TIMERANGE = "20260201-20260701"
EXPECTED_TIMEFRAME = "15m"
EXPECTED_FEE = 0.002
EXPECTED_FINAL_HOLDOUT = "20260801-20260930"
EXPECTED_REQUEST_PATH = (
    "ai_platform/research/tradingview/run-requests/futures-historical-benchmark-v1.json"
)


class TradingViewHistoricalBenchmarkError(RuntimeError):
    """Raised when the benchmark contract or evidence fails closed."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        message = f"Unable to read {label} {path}: {exc}"
        raise TradingViewHistoricalBenchmarkError(message) from exc
    if not isinstance(payload, dict):
        raise TradingViewHistoricalBenchmarkError(f"{label} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git_blob_sha(path: str) -> str:
    candidate = (REPO_ROOT / path).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise TradingViewHistoricalBenchmarkError(
            f"Source path escapes repository root: {path}"
        ) from exc
    if not candidate.is_file():
        raise TradingViewHistoricalBenchmarkError(f"Frozen source file is missing: {path}")
    try:
        payload = candidate.read_bytes()
    except OSError as exc:
        raise TradingViewHistoricalBenchmarkError(
            f"Unable to read frozen source {path}"
        ) from exc
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload, usedforsecurity=False).hexdigest()


def _validate_source_identity(contract: dict[str, Any]) -> None:
    identity = contract.get("source_identity")
    expected = {
        "strategy_path": "ai_platform/strategies/TradingViewResearchStrategies.py",
        "strategy_git_blob_sha": "e6deee3f9f8832745c66933dc639e5b7c9cffe53",
        "signal_path": "ai_platform/research/tradingview/signals.py",
        "signal_git_blob_sha": "7d9f8360166d8f8fc2ffa238f0ad3385af111a31",
    }
    if identity != expected:
        raise TradingViewHistoricalBenchmarkError(
            "Frozen TradingView source identity contract drifted"
        )
    for path_field, sha_field in (
        ("strategy_path", "strategy_git_blob_sha"),
        ("signal_path", "signal_git_blob_sha"),
    ):
        actual = _git_blob_sha(identity[path_field])
        if actual != identity[sha_field]:
            raise TradingViewHistoricalBenchmarkError(
                f"Frozen source identity changed for {identity[path_field]}: {actual}"
            )


def validate_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:  # noqa: C901
    """Validate all frozen benchmark inputs and research-safety boundaries."""
    contract = _read_json(path.resolve(), "TradingView historical benchmark contract")
    if contract.get("schema_version") != 1 or contract.get("benchmark_id") != BENCHMARK_ID:
        raise TradingViewHistoricalBenchmarkError("TradingView benchmark identity drifted")
    if contract.get("status") != "execution_contract_ready":
        raise TradingViewHistoricalBenchmarkError("Benchmark contract status drifted")
    if contract.get("research_track") != "tradingview-strategy-research-v1":
        raise TradingViewHistoricalBenchmarkError("TradingView research track drifted")
    if contract.get("preflight_id") != PREFLIGHT_ID:
        raise TradingViewHistoricalBenchmarkError("Required preflight identity drifted")
    if contract.get("candidates") != EXPECTED_CANDIDATES:
        raise TradingViewHistoricalBenchmarkError(
            "Canonical TradingView candidate set or order drifted"
        )
    if contract.get("excluded_candidates") != {
        "wickhunter-multi-vwap": "blocked_on_historical_liquidation_feed"
    }:
        raise TradingViewHistoricalBenchmarkError("Wick Hunter exclusion boundary drifted")
    _validate_source_identity(contract)

    if contract.get("exchange") != {
        "name": "krakenfutures",
        "trading_mode": "futures",
        "margin_mode": "isolated",
        "stake_currency": "USD",
        "pairs": [
            {"base": "BTC", "symbol": "BTC/USD:USD", "market_id": "PF_XBTUSD"},
            {"base": "ETH", "symbol": "ETH/USD:USD", "market_id": "PF_ETHUSD"},
        ],
    }:
        raise TradingViewHistoricalBenchmarkError(
            "Frozen Kraken Futures benchmark market contract drifted"
        )

    if contract.get("data") != {
        "timeframe": EXPECTED_TIMEFRAME,
        "semantic_research_window": "20260301-20260630",
        "execution_timerange": EXPECTED_TIMERANGE,
        "download_timerange": EXPECTED_DOWNLOAD_TIMERANGE,
        "freqtrade_stop_semantics": "end_exclusive",
        "maximum_startup_candle_count": 120,
    }:
        raise TradingViewHistoricalBenchmarkError("Frozen benchmark data geometry drifted")

    if contract.get("execution_assumptions") != {
        "fee": EXPECTED_FEE,
        "max_open_trades": 2,
        "stake_amount": 100,
        "dry_run_wallet": 10000,
        "dry_run": True,
        "same_pairs_required": True,
        "same_timeframe_required": True,
        "same_timerange_required": True,
        "same_fee_required": True,
        "same_wallet_and_stake_required": True,
        "same_execution_semantics_required": True,
    }:
        raise TradingViewHistoricalBenchmarkError("Frozen common execution assumptions drifted")

    if contract.get("validation_analyses") != {
        "lookahead": {
            "required": True,
            "minimum_trade_amount": 1,
            "targeted_trade_amount": 20,
            "allow_limit_orders": False,
            "failure_policy": "record_incomplete_and_block_validation_claim",
        },
        "recursive": {
            "required": True,
            "pair": "BTC/USD:USD",
            "startup_candles": [49, 99, 119, 199, 499, 999],
            "failure_policy": "record_incomplete_and_block_validation_claim",
        },
    }:
        raise TradingViewHistoricalBenchmarkError("Benchmark validation-analysis contract drifted")

    if contract.get("run_request") != {
        "path": EXPECTED_REQUEST_PATH,
        "requested_action": "execute_one_shot_historical_benchmark",
        "pull_request_scope": "add_exactly_one_canonical_run_request_file",
    }:
        raise TradingViewHistoricalBenchmarkError("One-shot run-request contract drifted")

    if contract.get("historical_evidence") != {
        "consumed_platform_oos": "20260501-20260630",
        "classification": "historical_research_evidence_only",
        "unseen_final_evidence": False,
        "retuning_from_reported_results_allowed": False,
        "automatic_promotion_allowed": False,
        "historical_ordering_allowed": True,
    }:
        raise TradingViewHistoricalBenchmarkError("Historical evidence classification drifted")

    if contract.get("protected_final_holdout") != {
        "timerange": EXPECTED_FINAL_HOLDOUT,
        "usage": "forbidden",
        "used": False,
        "earliest_final_evaluation_utc": "2026-10-01T00:00:00Z",
    }:
        raise TradingViewHistoricalBenchmarkError("Protected final holdout contract drifted")

    if contract.get("phase6_isolation") != {
        "member": False,
        "selection_policy_may_consume_results": False,
        "authoritative_selected_model_remains": None,
    }:
        raise TradingViewHistoricalBenchmarkError("Phase 6 isolation contract drifted")

    if contract.get("authorization") != {
        "canonical_one_shot_backtest_allowed": True,
        "market_discovery_allowed": True,
        "historical_data_download_allowed": True,
        "lookahead_analysis_allowed": True,
        "recursive_analysis_allowed": True,
        "hyperopt_allowed": False,
        "parameter_search_allowed": False,
        "strategy_mutation_allowed": False,
        "retuning_allowed": False,
        "automatic_winner_selection_allowed": False,
        "promotion_allowed": False,
        "live_trading_allowed": False,
        "profitability_claim_allowed": False,
        "superiority_claim_allowed": False,
        "final_holdout_access_allowed": False,
    }:
        raise TradingViewHistoricalBenchmarkError("Benchmark authorization boundary drifted")
    return contract


def canonical_request() -> dict[str, Any]:
    """Return the only run-request payload authorized to trigger the one-shot benchmark."""
    return {
        "schema_version": 1,
        "request_id": "tradingview-futures-historical-benchmark-v1-one-shot",
        "benchmark_id": BENCHMARK_ID,
        "requested_action": "execute_one_shot_historical_benchmark",
        "evidence_classification": "historical_research_evidence_only",
        "acknowledgements": {
            "protected_final_holdout_used": False,
            "retuning_allowed": False,
            "strategy_mutation_allowed": False,
            "automatic_promotion_allowed": False,
            "live_trading_allowed": False,
            "profitability_claim_allowed": False,
            "superiority_claim_allowed": False,
        },
    }


def validate_request(path: Path) -> dict[str, Any]:
    """Validate that a trigger file is semantically equal to the canonical request object."""
    validate_contract()
    request = _read_json(path.resolve(), "TradingView historical benchmark run request")
    if request != canonical_request():
        raise TradingViewHistoricalBenchmarkError(
            "Run request differs from the canonical one-shot request"
        )
    return request


def validate_runtime_markets(path: Path) -> dict[str, Any]:
    """Bind runtime discovery evidence to exact preflight-proven symbols and market IDs."""
    validate_contract()
    report = _read_json(path.resolve(), "runtime market discovery report")
    if report.get("preflight_id") != PREFLIGHT_ID or report.get("exchange") != "krakenfutures":
        raise TradingViewHistoricalBenchmarkError("Runtime discovery report identity drifted")
    if report.get("pairs") != EXPECTED_PAIRS:
        raise TradingViewHistoricalBenchmarkError("Runtime-discovered pair set or order drifted")
    resolved = report.get("resolved_markets")
    if not isinstance(resolved, dict):
        raise TradingViewHistoricalBenchmarkError("Runtime discovery report lacks resolved markets")
    for base, pair in zip(("BTC", "ETH"), EXPECTED_PAIRS, strict=True):
        market = resolved.get(base)
        if not isinstance(market, dict):
            raise TradingViewHistoricalBenchmarkError(f"Runtime discovery lacks {base} market")
        expected = {
            "symbol": pair,
            "id": EXPECTED_MARKET_IDS[base],
            "base": base,
            "quote": "USD",
            "settle": "USD",
            "active": True,
            "contract": True,
            "swap": True,
        }
        if market != expected:
            raise TradingViewHistoricalBenchmarkError(f"Runtime {base} market identity drifted")
    return report


def validate_materialized_config(path: Path) -> dict[str, Any]:
    """Validate common execution settings after runtime pair materialization."""
    contract = validate_contract()
    config = _read_json(path.resolve(), "materialized TradingView futures config")
    assumptions = contract["execution_assumptions"]
    expected = {
        "trading_mode": "futures",
        "margin_mode": "isolated",
        "stake_currency": "USD",
        "max_open_trades": assumptions["max_open_trades"],
        "stake_amount": assumptions["stake_amount"],
        "dry_run_wallet": assumptions["dry_run_wallet"],
        "dry_run": True,
        "timeframe": EXPECTED_TIMEFRAME,
    }
    for field, value in expected.items():
        if config.get(field) != value:
            raise TradingViewHistoricalBenchmarkError(
                f"Materialized config field {field} drifted: expected {value!r}"
            )
    exchange = config.get("exchange")
    if not isinstance(exchange, dict) or exchange.get("name") != "krakenfutures":
        raise TradingViewHistoricalBenchmarkError("Materialized config exchange drifted")
    if exchange.get("pair_whitelist") != EXPECTED_PAIRS:
        raise TradingViewHistoricalBenchmarkError("Materialized config pair whitelist drifted")
    return config


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TradingViewHistoricalBenchmarkError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise TradingViewHistoricalBenchmarkError(f"{label} must be a finite number")
    return result


def _relative_drawdown(strategy_stats: dict[str, Any]) -> float:
    """Normalize current and legacy Freqtrade relative drawdown fields fail-closed."""
    values: list[tuple[str, float]] = []
    for field in ("max_drawdown_account", "max_relative_drawdown", "max_drawdown"):
        raw = strategy_stats.get(field)
        if raw is not None:
            values.append((field, _finite_number(raw, field)))
    if not values:
        raise TradingViewHistoricalBenchmarkError(
            "Backtest archive contains no finite relative drawdown field"
        )
    canonical = values[0][1]
    for _field, value in values[1:]:
        if not math.isclose(value, canonical, rel_tol=1e-12, abs_tol=1e-12):
            details = ", ".join(f"{name}={number}" for name, number in values)
            raise TradingViewHistoricalBenchmarkError(
                f"Backtest relative drawdown fields disagree: {details}"
            )
    return canonical


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise TradingViewHistoricalBenchmarkError(
            f"Unable to hash backtest archive: {exc}"
        ) from exc
    return digest.hexdigest()


def extract_backtest(archive_path: Path, strategy: str) -> dict[str, Any]:  # noqa: C901
    """Extract a common immutable evidence schema from one frozen Freqtrade archive."""
    contract = validate_contract()
    if strategy not in EXPECTED_CANDIDATES:
        raise TradingViewHistoricalBenchmarkError(f"Unsupported benchmark strategy: {strategy}")
    try:
        from ai_platform.scripts.model_comparison_oos_result_extractor import (
            ModelComparisonOosExtractorError,
            _load_backtest_stats,
        )
    except ImportError as exc:
        raise TradingViewHistoricalBenchmarkError(
            "Freqtrade backtest extraction helpers unavailable"
        ) from exc
    try:
        stats, stats_member, archive_sha256 = _load_backtest_stats(archive_path.resolve())
    except ModelComparisonOosExtractorError as exc:
        raise TradingViewHistoricalBenchmarkError(str(exc)) from exc

    strategies = stats.get("strategy")
    if not isinstance(strategies, dict) or set(strategies) != {strategy}:
        raise TradingViewHistoricalBenchmarkError(
            "Backtest archive must contain exactly the requested TradingView strategy"
        )
    strategy_stats = strategies[strategy]
    if not isinstance(strategy_stats, dict):
        raise TradingViewHistoricalBenchmarkError("Backtest strategy stats must be a JSON object")
    if strategy_stats.get("strategy_name") != strategy:
        raise TradingViewHistoricalBenchmarkError("Backtest strategy identity drifted")
    if strategy_stats.get("timerange") != EXPECTED_TIMERANGE:
        raise TradingViewHistoricalBenchmarkError("Backtest execution timerange drifted")

    raw_trades = strategy_stats.get("trades")
    if not isinstance(raw_trades, list):
        raise TradingViewHistoricalBenchmarkError("Backtest trades must be a list")
    pair_counts: Counter[str] = Counter()
    pair_profit_abs: defaultdict[str, float] = defaultdict(float)
    exit_counts: Counter[str] = Counter()
    exit_profit_abs: defaultdict[str, float] = defaultdict(float)
    long_count = 0
    short_count = 0
    long_profit_abs = 0.0
    short_profit_abs = 0.0
    trade_profit_abs = 0.0

    for index, trade in enumerate(raw_trades):
        if not isinstance(trade, dict):
            raise TradingViewHistoricalBenchmarkError(f"Trade {index} must be a JSON object")
        pair = trade.get("pair")
        if pair not in EXPECTED_PAIRS:
            raise TradingViewHistoricalBenchmarkError(
                f"Trade {index} uses unexpected pair {pair!r}"
            )
        profit_abs = _finite_number(trade.get("profit_abs"), f"trade[{index}].profit_abs")
        exit_reason = trade.get("exit_reason")
        if not isinstance(exit_reason, str) or not exit_reason:
            raise TradingViewHistoricalBenchmarkError(
                f"trade[{index}].exit_reason must be a non-empty string"
            )
        is_short = trade.get("is_short")
        if not isinstance(is_short, bool):
            raise TradingViewHistoricalBenchmarkError(f"trade[{index}].is_short must be boolean")
        pair_counts[pair] += 1
        pair_profit_abs[pair] += profit_abs
        exit_counts[exit_reason] += 1
        exit_profit_abs[exit_reason] += profit_abs
        trade_profit_abs += profit_abs
        if is_short:
            short_count += 1
            short_profit_abs += profit_abs
        else:
            long_count += 1
            long_profit_abs += profit_abs

    reported_total_trades = strategy_stats.get("total_trades")
    if reported_total_trades != len(raw_trades):
        raise TradingViewHistoricalBenchmarkError(
            "Reported total_trades differs from archived trade list"
        )

    starting_balance = _finite_number(strategy_stats.get("starting_balance"), "starting_balance")
    if starting_balance <= 0:
        raise TradingViewHistoricalBenchmarkError("starting_balance must be positive")

    result = {
        "schema_version": 1,
        "benchmark_id": BENCHMARK_ID,
        "strategy": strategy,
        "source": {
            "archive_sha256": archive_sha256 or _sha256(archive_path.resolve()),
            "stats_member": stats_member,
        },
        "execution": {
            "exchange": "krakenfutures",
            "trading_mode": "futures",
            "margin_mode": "isolated",
            "pairs": EXPECTED_PAIRS,
            "timeframe": EXPECTED_TIMEFRAME,
            "timerange": EXPECTED_TIMERANGE,
            "fee": EXPECTED_FEE,
            "max_open_trades": contract["execution_assumptions"]["max_open_trades"],
            "stake_amount": contract["execution_assumptions"]["stake_amount"],
            "dry_run_wallet": contract["execution_assumptions"]["dry_run_wallet"],
        },
        "metrics": {
            "total_trades": len(raw_trades),
            "profit_total": _finite_number(strategy_stats.get("profit_total"), "profit_total"),
            "profit_total_abs": _finite_number(
                strategy_stats.get("profit_total_abs"), "profit_total_abs"
            ),
            "max_drawdown": _relative_drawdown(strategy_stats),
            "max_drawdown_abs": _finite_number(
                strategy_stats.get("max_drawdown_abs"), "max_drawdown_abs"
            ),
            "starting_balance": starting_balance,
            "trade_profit_abs_sum": trade_profit_abs,
        },
        "pair_breakdown": [
            {
                "pair": pair,
                "trades": pair_counts[pair],
                "profit_abs_sum": pair_profit_abs[pair],
            }
            for pair in EXPECTED_PAIRS
        ],
        "exit_reason_breakdown": [
            {
                "exit_reason": reason,
                "trades": exit_counts[reason],
                "profit_abs_sum": exit_profit_abs[reason],
            }
            for reason in sorted(exit_counts)
        ],
        "direction_breakdown": {
            "long": {"trades": long_count, "profit_abs_sum": long_profit_abs},
            "short": {"trades": short_count, "profit_abs_sum": short_profit_abs},
        },
        "evidence_classification": "historical_research_evidence_only",
        "authorization": {
            "final_holdout_used": False,
            "retuning_allowed": False,
            "automatic_promotion_allowed": False,
            "profitability_claim_allowed": False,
            "superiority_claim_allowed": False,
        },
    }
    return result


def build_contract_report() -> dict[str, Any]:
    contract = validate_contract()
    return {
        "schema_version": 1,
        "benchmark_id": BENCHMARK_ID,
        "status": "contract_ready_request_not_present",
        "candidates": contract["candidates"],
        "pairs": EXPECTED_PAIRS,
        "timeframe": EXPECTED_TIMEFRAME,
        "execution_timerange": EXPECTED_TIMERANGE,
        "download_timerange": EXPECTED_DOWNLOAD_TIMERANGE,
        "fee": EXPECTED_FEE,
        "protected_final_holdout": EXPECTED_FINAL_HOLDOUT,
        "protected_final_holdout_used": False,
        "retuning_allowed": False,
        "automatic_promotion_allowed": False,
        "run_request_path": EXPECTED_REQUEST_PATH,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=False)
    subparsers.add_parser("contract")
    subparsers.add_parser("print-canonical-request")

    request = subparsers.add_parser("validate-request")
    request.add_argument("path", type=Path)

    markets = subparsers.add_parser("validate-markets")
    markets.add_argument("path", type=Path)

    config = subparsers.add_parser("validate-config")
    config.add_argument("path", type=Path)

    extract = subparsers.add_parser("extract-backtest")
    extract.add_argument("archive", type=Path)
    extract.add_argument("--strategy", required=True, choices=EXPECTED_CANDIDATES)
    extract.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    mode = args.mode or "contract"
    try:
        if mode == "contract":
            payload = build_contract_report()
        elif mode == "print-canonical-request":
            validate_contract()
            payload = canonical_request()
        elif mode == "validate-request":
            payload = validate_request(args.path)
        elif mode == "validate-markets":
            payload = validate_runtime_markets(args.path)
        elif mode == "validate-config":
            payload = validate_materialized_config(args.path)
        elif mode == "extract-backtest":
            payload = extract_backtest(args.archive, args.strategy)
            if args.output:
                _write_json(args.output, payload)
        else:
            raise TradingViewHistoricalBenchmarkError(f"Unsupported mode: {mode}")
    except TradingViewHistoricalBenchmarkError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
