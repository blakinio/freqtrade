from __future__ import annotations

import json

import pytest

from ai_platform.scripts.tradingview_futures_historical_preflight import (
    EXPECTED_CANDIDATES,
    TradingViewFuturesPreflightError,
    build_contract_report,
    discover_markets,
    materialize_config,
    validate_contract,
    validate_strategy_classes,
)


def _market(
    base: str,
    symbol: str,
    *,
    active: bool = True,
    contract: bool = True,
    swap: bool = True,
    quote: str = "USD",
    settle: str = "USD",
) -> dict:
    return {
        "id": symbol.replace("/", "-").replace(":", "-"),
        "symbol": symbol,
        "base": base,
        "quote": quote,
        "settle": settle,
        "active": active,
        "contract": contract,
        "swap": swap,
    }


def test_contract_report_is_preflight_only() -> None:
    report = build_contract_report()

    assert report["candidates"] == EXPECTED_CANDIDATES
    assert report["exchange"] == "krakenfutures"
    assert report["trading_mode"] == "futures"
    assert report["margin_mode"] == "isolated"
    assert report["stake_currency"] == "USD"
    assert report["dry_run"] is True
    assert report["strategy_backtest_executed"] is False
    assert report["ranking_allowed"] is False
    assert report["protected_final_holdout_used"] is False


def test_contract_rejects_backtest_authorization(tmp_path) -> None:
    contract_path = tmp_path / "futures-historical-preflight-v1.json"
    source = validate_contract()
    source["authorization"]["strategy_backtest_allowed"] = True
    contract_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(TradingViewFuturesPreflightError, match="forbidden preflight authorization"):
        validate_contract(contract_path)


def test_market_discovery_resolves_exact_usd_perpetuals() -> None:
    report = discover_markets(
        [
            _market("BTC", "BTC/USD:USD"),
            _market("ETH", "ETH/USD:USD"),
            _market("BTC", "BTC/USD:BTC", settle="BTC"),
            _market("BTC", "BTC/USD-20261231:USD", swap=False),
            _market("ETH", "ETH/USD:USD-INACTIVE", active=False),
        ]
    )

    assert report["pairs"] == ["BTC/USD:USD", "ETH/USD:USD"]
    assert report["resolved_markets"]["BTC"]["settle"] == "USD"
    assert report["resolved_markets"]["ETH"]["swap"] is True


def test_market_discovery_fails_on_ambiguous_perpetual() -> None:
    with pytest.raises(TradingViewFuturesPreflightError, match="exactly one eligible BTC"):
        discover_markets(
            [
                _market("BTC", "BTC/USD:USD"),
                _market("BTC", "BTC/USD:USD-ALT"),
                _market("ETH", "ETH/USD:USD"),
            ]
        )


def test_market_discovery_fails_when_required_base_is_missing() -> None:
    with pytest.raises(TradingViewFuturesPreflightError, match="exactly one eligible ETH"):
        discover_markets([_market("BTC", "BTC/USD:USD")])


def test_materialized_config_uses_only_discovered_pairs() -> None:
    symbols = discover_markets(
        [
            _market("BTC", "BTC/USD:USD"),
            _market("ETH", "ETH/USD:USD"),
        ]
    )

    config = materialize_config(symbols)

    assert config["exchange"]["pair_whitelist"] == ["BTC/USD:USD", "ETH/USD:USD"]
    assert config["exchange"]["name"] == "krakenfutures"
    assert config["trading_mode"] == "futures"
    assert config["margin_mode"] == "isolated"
    assert config["dry_run"] is True


def test_strategy_source_keeps_three_short_capable_15m_candidates() -> None:
    evidence = validate_strategy_classes()

    assert list(evidence) == EXPECTED_CANDIDATES
    assert all(item["can_short"] is True for item in evidence.values())
    assert all(item["timeframe"] == "15m" for item in evidence.values())
    assert max(item["startup_candle_count"] for item in evidence.values()) == 120
