#!/usr/bin/env python3
"""Fail-closed historical futures preflight for TradingView research strategies."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "ai_platform/research/tradingview/futures-historical-preflight-v1.json"
CONFIG_TEMPLATE_PATH = REPO_ROOT / "ai_platform/configs/tradingview-futures-research.example.json"
STRATEGY_PATH = REPO_ROOT / "ai_platform/strategies/TradingViewResearchStrategies.py"

PREFLIGHT_ID = "tradingview-futures-historical-preflight-v1"
EXPECTED_CANDIDATES = [
    "TVDonchianBreakoutStrategy",
    "TVSupertrendStrategy",
    "TVBollingerMeanReversionStrategy",
]
EXPECTED_BASES = ["BTC", "ETH"]
EXPECTED_EXCHANGE = "krakenfutures"
EXPECTED_TIMEFRAME = "15m"
EXPECTED_SEMANTIC_WINDOW = "20260301-20260630"
EXPECTED_EXECUTION_TIMERANGE = "20260301-20260701"
EXPECTED_DOWNLOAD_TIMERANGE = "20260201-20260701"
EXPECTED_FINAL_HOLDOUT = "20260801-20260930"
EXPECTED_CONSUMED_OOS = "20260501-20260630"
EXPECTED_FEE = 0.002
MAXIMUM_STARTUP_CANDLES = 120


class TradingViewFuturesPreflightError(RuntimeError):
    """Raised when the TradingView futures preflight contract fails closed."""


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TradingViewFuturesPreflightError(f"Unable to read JSON object {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise TradingViewFuturesPreflightError(f"Expected a JSON object in {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _split_timerange(value: str) -> tuple[datetime, datetime]:
    try:
        start, stop = value.split("-", maxsplit=1)
        return (
            datetime.strptime(start, "%Y%m%d").replace(tzinfo=UTC),
            datetime.strptime(stop, "%Y%m%d").replace(tzinfo=UTC),
        )
    except ValueError as exc:
        raise TradingViewFuturesPreflightError(
            f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}"
        ) from exc


def _validate_no_holdout_overlap(timerange: str) -> None:
    start, stop = _split_timerange(timerange)
    holdout_start, holdout_end = _split_timerange(EXPECTED_FINAL_HOLDOUT)
    holdout_stop = holdout_end + timedelta(days=1)
    if start < holdout_stop and stop > holdout_start:
        raise TradingViewFuturesPreflightError(
            f"Timerange {timerange} overlaps protected final holdout {EXPECTED_FINAL_HOLDOUT}"
        )


def _validate_exchange_contract(contract: dict[str, Any]) -> None:
    expected = {
        "name": EXPECTED_EXCHANGE,
        "trading_mode": "futures",
        "margin_mode": "isolated",
        "stake_currency": "USD",
        "required_market_bases": EXPECTED_BASES,
        "market_contract": {
            "active": True,
            "contract": True,
            "swap": True,
            "quote": "USD",
            "settle": "USD",
        },
        "resolved_symbols": "runtime_preflight_required",
    }
    if contract.get("exchange") != expected:
        raise TradingViewFuturesPreflightError("Kraken Futures market contract drifted")


def _validate_data_contract(contract: dict[str, Any]) -> None:
    expected = {
        "timeframe": EXPECTED_TIMEFRAME,
        "semantic_research_window": EXPECTED_SEMANTIC_WINDOW,
        "execution_timerange": EXPECTED_EXECUTION_TIMERANGE,
        "download_timerange": EXPECTED_DOWNLOAD_TIMERANGE,
        "freqtrade_stop_semantics": "end_exclusive",
        "maximum_startup_candle_count": MAXIMUM_STARTUP_CANDLES,
        "minimum_warmup_start_utc": "2026-02-27T18:00:00Z",
    }
    if contract.get("data") != expected:
        raise TradingViewFuturesPreflightError("Historical data geometry drifted")
    semantic_start, semantic_end = _split_timerange(EXPECTED_SEMANTIC_WINDOW)
    execution_start, execution_stop = _split_timerange(EXPECTED_EXECUTION_TIMERANGE)
    if execution_start != semantic_start or execution_stop != semantic_end + timedelta(days=1):
        raise TradingViewFuturesPreflightError("Exclusive Freqtrade execution boundary drifted")
    _validate_no_holdout_overlap(EXPECTED_EXECUTION_TIMERANGE)
    _validate_no_holdout_overlap(EXPECTED_DOWNLOAD_TIMERANGE)


def _validate_comparison_contract(contract: dict[str, Any]) -> None:
    assumptions = contract.get("comparison_assumptions", {})
    if assumptions.get("fee") != EXPECTED_FEE or assumptions.get("ranking_allowed") is not False:
        raise TradingViewFuturesPreflightError("Comparison fee or ranking boundary drifted")
    required_true = (
        "same_pairs_required",
        "same_timeframe_required",
        "same_timerange_required",
        "same_execution_semantics_required",
    )
    if any(assumptions.get(field) is not True for field in required_true):
        raise TradingViewFuturesPreflightError("A comparison fairness invariant drifted")
    expected_historical = {
        "consumed_platform_oos": EXPECTED_CONSUMED_OOS,
        "unseen_final_evidence": False,
        "retuning_from_reported_results_allowed": False,
    }
    if contract.get("historical_evidence") != expected_historical:
        raise TradingViewFuturesPreflightError("Historical evidence classification drifted")


def _validate_safety_contract(contract: dict[str, Any]) -> None:
    expected_holdout = {
        "timerange": EXPECTED_FINAL_HOLDOUT,
        "usage": "forbidden",
        "used": False,
        "earliest_final_evaluation_utc": "2026-10-01T00:00:00Z",
    }
    if contract.get("protected_final_holdout") != expected_holdout:
        raise TradingViewFuturesPreflightError("Protected final holdout contract drifted")
    authorization = contract.get("authorization", {})
    required_true = (
        "market_discovery_allowed",
        "historical_data_download_allowed",
        "data_coverage_verification_allowed",
        "strategy_loading_check_allowed",
    )
    if any(authorization.get(field) is not True for field in required_true):
        raise TradingViewFuturesPreflightError("A required preflight authorization drifted")
    forbidden = (
        "strategy_backtest_allowed",
        "hyperopt_allowed",
        "parameter_search_allowed",
        "strategy_mutation_allowed",
        "winner_selection_allowed",
        "promotion_allowed",
        "live_trading_allowed",
        "profitability_claim_allowed",
        "superiority_claim_allowed",
        "final_holdout_access_allowed",
    )
    if any(authorization.get(field) is not False for field in forbidden):
        raise TradingViewFuturesPreflightError("A forbidden preflight authorization became enabled")


def validate_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    """Validate the tracked preflight contract and all research-safety invariants."""
    contract = _read_json_object(path)
    if contract.get("schema_version") != 1 or contract.get("preflight_id") != PREFLIGHT_ID:
        raise TradingViewFuturesPreflightError("TradingView futures preflight identity drifted")
    if contract.get("status") != "preflight_only":
        raise TradingViewFuturesPreflightError("Preflight status must remain preflight_only")
    if contract.get("research_track") != "tradingview-strategy-research-v1":
        raise TradingViewFuturesPreflightError("TradingView research-track identity drifted")
    if contract.get("candidates") != EXPECTED_CANDIDATES:
        raise TradingViewFuturesPreflightError("Canonical TradingView candidate set drifted")
    if contract.get("excluded_candidates") != {
        "wickhunter-multi-vwap": "blocked_on_historical_liquidation_feed"
    }:
        raise TradingViewFuturesPreflightError("Wick Hunter exclusion boundary drifted")
    _validate_exchange_contract(contract)
    _validate_data_contract(contract)
    _validate_comparison_contract(contract)
    _validate_safety_contract(contract)
    return contract


def validate_config_template(path: Path = CONFIG_TEMPLATE_PATH) -> dict[str, Any]:
    """Validate the inert futures dry-run config before runtime symbols are inserted."""
    config = _read_json_object(path)
    expected = {
        "trading_mode": "futures",
        "margin_mode": "isolated",
        "stake_currency": "USD",
        "dry_run": True,
        "timeframe": EXPECTED_TIMEFRAME,
    }
    for field, value in expected.items():
        if config.get(field) != value:
            raise TradingViewFuturesPreflightError(
                f"Research config template drifted for {field}: expected {value!r}"
            )
    exchange = config.get("exchange", {})
    if exchange.get("name") != EXPECTED_EXCHANGE:
        raise TradingViewFuturesPreflightError("Research config exchange must be krakenfutures")
    if exchange.get("pair_whitelist") != []:
        raise TradingViewFuturesPreflightError(
            "Tracked config template must keep pair_whitelist empty until runtime discovery"
        )
    if exchange.get("pair_blacklist") != []:
        raise TradingViewFuturesPreflightError("Research config pair_blacklist must remain empty")
    return config


def validate_strategy_classes(path: Path = STRATEGY_PATH) -> dict[str, Any]:
    """Statically prove the canonical classes remain short-capable 15m strategies."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise TradingViewFuturesPreflightError(f"Unable to parse strategy source: {exc}") from exc
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    evidence: dict[str, Any] = {}
    for class_name in EXPECTED_CANDIDATES:
        node = classes.get(class_name)
        if node is None:
            raise TradingViewFuturesPreflightError(f"Missing canonical strategy class: {class_name}")
        assignments: dict[str, Any] = {}
        for statement in node.body:
            if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                continue
            target = statement.targets[0]
            if not isinstance(target, ast.Name):
                continue
            try:
                assignments[target.id] = ast.literal_eval(statement.value)
            except (ValueError, TypeError):
                continue
        if assignments.get("can_short") is not True:
            raise TradingViewFuturesPreflightError(f"{class_name} must remain can_short=True")
        if assignments.get("timeframe") != EXPECTED_TIMEFRAME:
            raise TradingViewFuturesPreflightError(f"{class_name} timeframe drifted from 15m")
        evidence[class_name] = {
            "can_short": True,
            "timeframe": EXPECTED_TIMEFRAME,
            "startup_candle_count": assignments.get("startup_candle_count"),
        }
    maximum = max(int(item["startup_candle_count"] or 0) for item in evidence.values())
    if maximum > MAXIMUM_STARTUP_CANDLES:
        raise TradingViewFuturesPreflightError(
            f"Strategy startup requirement increased beyond contract: {maximum}"
        )
    return evidence


def _eligible_market(market: dict[str, Any], base: str) -> bool:
    return (
        market.get("active") is True
        and market.get("contract") is True
        and market.get("swap") is True
        and market.get("base") == base
        and market.get("quote") == "USD"
        and market.get("settle") == "USD"
        and isinstance(market.get("symbol"), str)
        and bool(market["symbol"])
    )


def discover_markets(markets: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve exactly one active USD-settled perpetual market for BTC and ETH."""
    validate_contract()
    resolved: dict[str, dict[str, Any]] = {}
    for base in EXPECTED_BASES:
        matches = sorted(
            (market for market in markets if _eligible_market(market, base)),
            key=lambda market: str(market["symbol"]),
        )
        if len(matches) != 1:
            symbols = [str(market.get("symbol")) for market in matches]
            raise TradingViewFuturesPreflightError(
                f"Expected exactly one eligible {base} USD perpetual, found {len(matches)}: {symbols}"
            )
        market = matches[0]
        resolved[base] = {
            "symbol": market["symbol"],
            "id": market.get("id"),
            "base": market.get("base"),
            "quote": market.get("quote"),
            "settle": market.get("settle"),
            "active": market.get("active"),
            "contract": market.get("contract"),
            "swap": market.get("swap"),
        }
    return {
        "schema_version": 1,
        "preflight_id": PREFLIGHT_ID,
        "exchange": EXPECTED_EXCHANGE,
        "resolved_markets": resolved,
        "pairs": [resolved[base]["symbol"] for base in EXPECTED_BASES],
    }


def discover_live_markets() -> dict[str, Any]:
    """Load public Kraken Futures markets through the runtime CCXT version and resolve symbols."""
    try:
        import ccxt
    except ImportError as exc:
        raise TradingViewFuturesPreflightError("CCXT is required for live market discovery") from exc
    exchange = ccxt.krakenfutures({"enableRateLimit": True})
    markets = exchange.load_markets()
    if not isinstance(markets, dict):
        raise TradingViewFuturesPreflightError("CCXT load_markets did not return a market mapping")
    return discover_markets([market for market in markets.values() if isinstance(market, dict)])


def _validate_symbol_report(report: dict[str, Any]) -> list[str]:
    if report.get("preflight_id") != PREFLIGHT_ID or report.get("exchange") != EXPECTED_EXCHANGE:
        raise TradingViewFuturesPreflightError("Resolved-market evidence identity drifted")
    resolved = report.get("resolved_markets", {})
    pairs = report.get("pairs")
    expected_pairs: list[str] = []
    for base in EXPECTED_BASES:
        market = resolved.get(base, {})
        if not _eligible_market(market, base):
            raise TradingViewFuturesPreflightError(f"Resolved {base} market no longer meets contract")
        expected_pairs.append(market["symbol"])
    if pairs != expected_pairs or len(set(pairs)) != len(pairs):
        raise TradingViewFuturesPreflightError("Resolved pair ordering or uniqueness drifted")
    return expected_pairs


def materialize_config(symbol_report: dict[str, Any]) -> dict[str, Any]:
    """Insert only validated runtime-discovered symbols into the inert config template."""
    pairs = _validate_symbol_report(symbol_report)
    config = deepcopy(validate_config_template())
    config["exchange"]["pair_whitelist"] = pairs
    if config["dry_run"] is not True:
        raise TradingViewFuturesPreflightError("Materialized research config must remain dry_run=true")
    return config


def build_contract_report() -> dict[str, Any]:
    """Return static preflight evidence without touching network or market data."""
    contract = validate_contract()
    config = validate_config_template()
    strategies = validate_strategy_classes()
    return {
        "schema_version": 1,
        "preflight_id": PREFLIGHT_ID,
        "status": "contract_ready_runtime_unverified",
        "exchange": EXPECTED_EXCHANGE,
        "trading_mode": config["trading_mode"],
        "margin_mode": config["margin_mode"],
        "stake_currency": config["stake_currency"],
        "dry_run": config["dry_run"],
        "candidates": contract["candidates"],
        "strategies": strategies,
        "timeframe": EXPECTED_TIMEFRAME,
        "semantic_research_window": EXPECTED_SEMANTIC_WINDOW,
        "execution_timerange": EXPECTED_EXECUTION_TIMERANGE,
        "download_timerange": EXPECTED_DOWNLOAD_TIMERANGE,
        "fee": EXPECTED_FEE,
        "protected_final_holdout": EXPECTED_FINAL_HOLDOUT,
        "protected_final_holdout_used": False,
        "strategy_backtest_executed": False,
        "ranking_allowed": False,
        "promotion_allowed": False,
        "profitability_claim_allowed": False,
    }


def verify_downloaded_data(datadir: Path, symbol_report: dict[str, Any]) -> dict[str, Any]:
    """Verify 15m futures candles cover warmup and the complete research window."""
    from freqtrade.configuration import TimeRange
    from freqtrade.data.history.history_utils import load_pair_history
    from freqtrade.enums import CandleType

    pairs = _validate_symbol_report(symbol_report)
    timerange = TimeRange.parse_timerange(EXPECTED_DOWNLOAD_TIMERANGE)
    if timerange.stopdt != datetime(2026, 7, 1, tzinfo=UTC):
        raise TradingViewFuturesPreflightError("Freqtrade exclusive stop boundary drifted")
    warmup_start = datetime(2026, 2, 27, 18, 0, tzinfo=UTC)
    minimum_last = datetime(2026, 6, 30, 23, 45, tzinfo=UTC)
    coverage: dict[str, Any] = {}
    for pair in pairs:
        frame = load_pair_history(
            pair=pair,
            timeframe=EXPECTED_TIMEFRAME,
            datadir=datadir,
            timerange=timerange,
            fill_up_missing=False,
            drop_incomplete=False,
            candle_type=CandleType.FUTURES,
        )
        if frame.empty:
            raise TradingViewFuturesPreflightError(f"No downloaded futures data for {pair}")
        first_date = frame["date"].min().to_pydatetime()
        last_date = frame["date"].max().to_pydatetime()
        if first_date > warmup_start:
            raise TradingViewFuturesPreflightError(
                f"Downloaded data starts too late for {pair}: {first_date.isoformat()}"
            )
        if last_date < minimum_last:
            raise TradingViewFuturesPreflightError(
                f"Downloaded data ends too early for {pair}: {last_date.isoformat()}"
            )
        date_diffs = frame["date"].sort_values().diff().dropna().dt.total_seconds()
        maximum_gap = int(date_diffs.max()) if not date_diffs.empty else 0
        coverage[pair] = {
            "rows": len(frame),
            "first": first_date.isoformat(),
            "last": last_date.isoformat(),
            "maximum_observed_gap_seconds": maximum_gap,
        }
    report = build_contract_report()
    report.update(
        {
            "status": "ready_for_separate_historical_benchmark_task",
            "market_data_available": True,
            "market_data_directory": str(datadir),
            "resolved_pairs": pairs,
            "coverage": coverage,
            "strategy_backtest_executed": False,
        }
    )
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=False)
    subparsers.add_parser("contract")
    discover = subparsers.add_parser("discover-markets")
    discover.add_argument("--output", type=Path)
    materialize = subparsers.add_parser("materialize-config")
    materialize.add_argument("--symbols", type=Path, required=True)
    materialize.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify-data")
    verify.add_argument("--symbols", type=Path, required=True)
    verify.add_argument("--datadir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    mode = args.mode or "contract"
    try:
        if mode == "contract":
            payload = build_contract_report()
        elif mode == "discover-markets":
            payload = discover_live_markets()
            if args.output:
                _write_json(args.output, payload)
        elif mode == "materialize-config":
            payload = materialize_config(_read_json_object(args.symbols))
            _write_json(args.output, payload)
        elif mode == "verify-data":
            payload = verify_downloaded_data(args.datadir, _read_json_object(args.symbols))
        else:
            raise TradingViewFuturesPreflightError(f"Unsupported mode: {mode}")
    except TradingViewFuturesPreflightError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
