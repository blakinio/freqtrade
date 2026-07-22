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

EXPECTED_EXCHANGE_CONTRACT = {
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
EXPECTED_DATA_CONTRACT = {
    "timeframe": EXPECTED_TIMEFRAME,
    "semantic_research_window": EXPECTED_SEMANTIC_WINDOW,
    "execution_timerange": EXPECTED_EXECUTION_TIMERANGE,
    "download_timerange": EXPECTED_DOWNLOAD_TIMERANGE,
    "freqtrade_stop_semantics": "end_exclusive",
    "maximum_startup_candle_count": MAXIMUM_STARTUP_CANDLES,
    "minimum_warmup_start_utc": "2026-02-27T18:00:00Z",
}
EXPECTED_HOLDOUT_CONTRACT = {
    "timerange": EXPECTED_FINAL_HOLDOUT,
    "usage": "forbidden",
    "used": False,
    "earliest_final_evaluation_utc": "2026-10-01T00:00:00Z",
}


class TradingViewFuturesPreflightError(RuntimeError):
    """Raised when the TradingView futures preflight contract fails closed."""


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        message = f"Unable to read JSON object {path}: {exc}"
        raise TradingViewFuturesPreflightError(message) from exc
    if not isinstance(payload, dict):
        raise TradingViewFuturesPreflightError(f"Expected a JSON object in {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.write_text(serialized, encoding="utf-8")


def _split_timerange(value: str) -> tuple[datetime, datetime]:
    try:
        start, stop = value.split("-", maxsplit=1)
        startdt = datetime.strptime(start, "%Y%m%d").replace(tzinfo=UTC)
        stopdt = datetime.strptime(stop, "%Y%m%d").replace(tzinfo=UTC)
    except ValueError as exc:
        message = f"Expected bounded YYYYMMDD-YYYYMMDD timerange: {value}"
        raise TradingViewFuturesPreflightError(message) from exc
    return startdt, stopdt


def _validate_no_holdout_overlap(timerange: str) -> None:
    start, stop = _split_timerange(timerange)
    holdout_start, holdout_end = _split_timerange(EXPECTED_FINAL_HOLDOUT)
    holdout_stop = holdout_end + timedelta(days=1)
    if start < holdout_stop and stop > holdout_start:
        message = f"Timerange {timerange} overlaps final holdout {EXPECTED_FINAL_HOLDOUT}"
        raise TradingViewFuturesPreflightError(message)


def _validate_temporal_geometry() -> None:
    semantic_start, semantic_end = _split_timerange(EXPECTED_SEMANTIC_WINDOW)
    execution_start, execution_stop = _split_timerange(EXPECTED_EXECUTION_TIMERANGE)
    expected_stop = semantic_end + timedelta(days=1)
    if execution_start != semantic_start or execution_stop != expected_stop:
        raise TradingViewFuturesPreflightError("Exclusive execution boundary drifted")
    _validate_no_holdout_overlap(EXPECTED_EXECUTION_TIMERANGE)
    _validate_no_holdout_overlap(EXPECTED_DOWNLOAD_TIMERANGE)


def _validate_comparison_assumptions(contract: dict[str, Any]) -> None:
    assumptions = contract.get("comparison_assumptions", {})
    if assumptions.get("fee") != EXPECTED_FEE:
        raise TradingViewFuturesPreflightError("Comparison fee assumption drifted")
    if assumptions.get("ranking_allowed") is not False:
        raise TradingViewFuturesPreflightError("Preflight ranking must remain forbidden")
    fairness_fields = (
        "same_pairs_required",
        "same_timeframe_required",
        "same_timerange_required",
        "same_execution_semantics_required",
    )
    if any(assumptions.get(field) is not True for field in fairness_fields):
        raise TradingViewFuturesPreflightError("A comparison fairness invariant drifted")


def _validate_historical_classification(contract: dict[str, Any]) -> None:
    expected = {
        "consumed_platform_oos": EXPECTED_CONSUMED_OOS,
        "unseen_final_evidence": False,
        "retuning_from_reported_results_allowed": False,
    }
    if contract.get("historical_evidence") != expected:
        raise TradingViewFuturesPreflightError("Historical evidence classification drifted")


def _validate_authorization(contract: dict[str, Any]) -> None:
    authorization = contract.get("authorization", {})
    allowed = (
        "market_discovery_allowed",
        "historical_data_download_allowed",
        "data_coverage_verification_allowed",
        "strategy_loading_check_allowed",
    )
    if any(authorization.get(field) is not True for field in allowed):
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
    """Validate the tracked contract and all research-safety invariants."""
    contract = _read_json_object(path)
    if contract.get("schema_version") != 1:
        raise TradingViewFuturesPreflightError("Preflight schema version drifted")
    if contract.get("preflight_id") != PREFLIGHT_ID:
        raise TradingViewFuturesPreflightError("Preflight identity drifted")
    if contract.get("status") != "preflight_only":
        raise TradingViewFuturesPreflightError("Preflight status drifted")
    if contract.get("research_track") != "tradingview-strategy-research-v1":
        raise TradingViewFuturesPreflightError("Research-track identity drifted")
    if contract.get("candidates") != EXPECTED_CANDIDATES:
        raise TradingViewFuturesPreflightError("Canonical candidate set drifted")
    expected_exclusion = {
        "wickhunter-multi-vwap": "blocked_on_historical_liquidation_feed"
    }
    if contract.get("excluded_candidates") != expected_exclusion:
        raise TradingViewFuturesPreflightError("Wick Hunter exclusion drifted")
    if contract.get("exchange") != EXPECTED_EXCHANGE_CONTRACT:
        raise TradingViewFuturesPreflightError("Kraken Futures market contract drifted")
    if contract.get("data") != EXPECTED_DATA_CONTRACT:
        raise TradingViewFuturesPreflightError("Historical data geometry drifted")
    if contract.get("protected_final_holdout") != EXPECTED_HOLDOUT_CONTRACT:
        raise TradingViewFuturesPreflightError("Protected final holdout contract drifted")
    _validate_temporal_geometry()
    _validate_comparison_assumptions(contract)
    _validate_historical_classification(contract)
    _validate_authorization(contract)
    return contract


def validate_config_template(path: Path = CONFIG_TEMPLATE_PATH) -> dict[str, Any]:
    """Validate the inert futures dry-run config before symbols are inserted."""
    config = _read_json_object(path)
    expected_fields = {
        "trading_mode": "futures",
        "margin_mode": "isolated",
        "stake_currency": "USD",
        "dry_run": True,
        "timeframe": EXPECTED_TIMEFRAME,
    }
    for field, value in expected_fields.items():
        if config.get(field) != value:
            message = f"Research config drifted for {field}: expected {value!r}"
            raise TradingViewFuturesPreflightError(message)
    exchange = config.get("exchange", {})
    if exchange.get("name") != EXPECTED_EXCHANGE:
        raise TradingViewFuturesPreflightError("Research exchange must be krakenfutures")
    if exchange.get("pair_whitelist") != []:
        message = "Tracked pair_whitelist must remain empty until runtime discovery"
        raise TradingViewFuturesPreflightError(message)
    if exchange.get("pair_blacklist") != []:
        raise TradingViewFuturesPreflightError("Research pair_blacklist must remain empty")
    return config


def _class_assignments(node: ast.ClassDef) -> dict[str, Any]:
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
    return assignments


def validate_strategy_classes(path: Path = STRATEGY_PATH) -> dict[str, Any]:
    """Prove the canonical classes remain short-capable 15m strategies."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise TradingViewFuturesPreflightError(f"Unable to parse strategy source: {exc}") from exc
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    evidence: dict[str, Any] = {}
    for class_name in EXPECTED_CANDIDATES:
        node = classes.get(class_name)
        if node is None:
            raise TradingViewFuturesPreflightError(
                f"Missing canonical strategy class: {class_name}"
            )
        assignments = _class_assignments(node)
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
        message = f"Strategy startup requirement exceeds contract: {maximum}"
        raise TradingViewFuturesPreflightError(message)
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
    """Resolve exactly one active USD-settled perpetual for BTC and ETH."""
    validate_contract()
    resolved: dict[str, dict[str, Any]] = {}
    for base in EXPECTED_BASES:
        matches = sorted(
            (market for market in markets if _eligible_market(market, base)),
            key=lambda market: str(market["symbol"]),
        )
        if len(matches) != 1:
            symbols = [str(market.get("symbol")) for market in matches]
            message = (
                f"Expected one eligible {base} USD perpetual; "
                f"found {len(matches)}: {symbols}"
            )
            raise TradingViewFuturesPreflightError(message)
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
    """Load public Kraken Futures markets through the installed CCXT runtime."""
    try:
        import ccxt
    except ImportError as exc:
        raise TradingViewFuturesPreflightError("CCXT is required for market discovery") from exc
    exchange = ccxt.krakenfutures({"enableRateLimit": True})
    markets = exchange.load_markets()
    if not isinstance(markets, dict):
        raise TradingViewFuturesPreflightError("CCXT load_markets returned no market mapping")
    market_list = [market for market in markets.values() if isinstance(market, dict)]
    return discover_markets(market_list)


def _validate_symbol_report(report: dict[str, Any]) -> list[str]:
    if report.get("preflight_id") != PREFLIGHT_ID:
        raise TradingViewFuturesPreflightError("Resolved-market evidence identity drifted")
    if report.get("exchange") != EXPECTED_EXCHANGE:
        raise TradingViewFuturesPreflightError("Resolved-market exchange drifted")
    resolved = report.get("resolved_markets", {})
    expected_pairs: list[str] = []
    for base in EXPECTED_BASES:
        market = resolved.get(base, {})
        if not _eligible_market(market, base):
            message = f"Resolved {base} market no longer meets contract"
            raise TradingViewFuturesPreflightError(message)
        expected_pairs.append(market["symbol"])
    pairs = report.get("pairs")
    if pairs != expected_pairs or len(set(expected_pairs)) != len(expected_pairs):
        raise TradingViewFuturesPreflightError("Resolved pair ordering or uniqueness drifted")
    return expected_pairs


def materialize_config(symbol_report: dict[str, Any]) -> dict[str, Any]:
    """Insert only validated runtime-discovered symbols into the config template."""
    pairs = _validate_symbol_report(symbol_report)
    config = deepcopy(validate_config_template())
    config["exchange"]["pair_whitelist"] = pairs
    if config["dry_run"] is not True:
        raise TradingViewFuturesPreflightError("Materialized config must remain dry_run=true")
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
    """Verify 15m futures candles cover warmup and the research window."""
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
            message = f"Downloaded data starts too late for {pair}: {first_date.isoformat()}"
            raise TradingViewFuturesPreflightError(message)
        if last_date < minimum_last:
            message = f"Downloaded data ends too early for {pair}: {last_date.isoformat()}"
            raise TradingViewFuturesPreflightError(message)
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
