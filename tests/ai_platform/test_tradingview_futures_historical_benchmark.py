from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_platform.scripts.tradingview_futures_historical_benchmark import (
    EXPECTED_CANDIDATES,
    TradingViewHistoricalBenchmarkError,
    build_contract_report,
    canonical_request,
    extract_backtest,
    validate_contract,
    validate_materialized_config,
    validate_request,
    validate_runtime_markets,
)


def _market_report(*, btc_id: str = "PF_XBTUSD") -> dict:
    return {
        "schema_version": 1,
        "preflight_id": "tradingview-futures-historical-preflight-v1",
        "exchange": "krakenfutures",
        "resolved_markets": {
            "BTC": {
                "symbol": "BTC/USD:USD",
                "id": btc_id,
                "base": "BTC",
                "quote": "USD",
                "settle": "USD",
                "active": True,
                "contract": True,
                "swap": True,
            },
            "ETH": {
                "symbol": "ETH/USD:USD",
                "id": "PF_ETHUSD",
                "base": "ETH",
                "quote": "USD",
                "settle": "USD",
                "active": True,
                "contract": True,
                "swap": True,
            },
        },
        "pairs": ["BTC/USD:USD", "ETH/USD:USD"],
    }


def _materialized_config() -> dict:
    return {
        "trading_mode": "futures",
        "margin_mode": "isolated",
        "max_open_trades": 2,
        "stake_currency": "USD",
        "stake_amount": 100,
        "dry_run": True,
        "dry_run_wallet": 10000,
        "timeframe": "15m",
        "exchange": {
            "name": "krakenfutures",
            "pair_whitelist": ["BTC/USD:USD", "ETH/USD:USD"],
        },
    }


def _stats(strategy: str, *, pair: str = "BTC/USD:USD") -> dict:
    trades = [
        {
            "pair": pair,
            "profit_abs": 10.0,
            "exit_reason": "exit_signal",
            "is_short": False,
        },
        {
            "pair": "ETH/USD:USD",
            "profit_abs": -2.0,
            "exit_reason": "stop_loss",
            "is_short": True,
        },
    ]
    return {
        "strategy": {
            strategy: {
                "strategy_name": strategy,
                "timerange": "20260301-20260701",
                "trades": trades,
                "total_trades": 2,
                "starting_balance": 10000.0,
                "profit_total": 0.0008,
                "profit_total_abs": 8.0,
                "max_drawdown": 0.001,
                "max_drawdown_abs": 10.0,
            }
        },
        "strategy_comparison": [],
    }


def test_contract_report_freezes_common_benchmark_inputs() -> None:
    report = build_contract_report()

    assert report["candidates"] == EXPECTED_CANDIDATES
    assert report["pairs"] == ["BTC/USD:USD", "ETH/USD:USD"]
    assert report["timeframe"] == "15m"
    assert report["execution_timerange"] == "20260301-20260701"
    assert report["fee"] == 0.002
    assert report["protected_final_holdout_used"] is False
    assert report["retuning_allowed"] is False
    assert report["automatic_promotion_allowed"] is False


def test_contract_rejects_promotion_authorization(tmp_path: Path) -> None:
    contract = validate_contract()
    contract["authorization"]["promotion_allowed"] = True
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(TradingViewHistoricalBenchmarkError, match="authorization boundary"):
        validate_contract(path)


def test_canonical_request_is_evidence_only() -> None:
    request = canonical_request()

    assert request["requested_action"] == "execute_one_shot_historical_benchmark"
    assert request["evidence_classification"] == "historical_research_evidence_only"
    assert all(value is False for value in request["acknowledgements"].values())


def test_request_rejects_any_semantic_mutation(tmp_path: Path) -> None:
    request = canonical_request()
    request["acknowledgements"]["retuning_allowed"] = True
    path = tmp_path / "request.json"
    path.write_text(json.dumps(request), encoding="utf-8")

    with pytest.raises(TradingViewHistoricalBenchmarkError, match="canonical one-shot request"):
        validate_request(path)


def test_runtime_market_validation_binds_exact_preflight_ids(tmp_path: Path) -> None:
    path = tmp_path / "markets.json"
    path.write_text(json.dumps(_market_report()), encoding="utf-8")

    report = validate_runtime_markets(path)

    assert report["pairs"] == ["BTC/USD:USD", "ETH/USD:USD"]


def test_runtime_market_validation_rejects_market_id_drift(tmp_path: Path) -> None:
    path = tmp_path / "markets.json"
    path.write_text(json.dumps(_market_report(btc_id="PF_OTHER")), encoding="utf-8")

    with pytest.raises(TradingViewHistoricalBenchmarkError, match="BTC market identity drifted"):
        validate_runtime_markets(path)


def test_materialized_config_freezes_common_execution_semantics(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(_materialized_config()), encoding="utf-8")

    config = validate_materialized_config(path)

    assert config["exchange"]["pair_whitelist"] == ["BTC/USD:USD", "ETH/USD:USD"]
    assert config["dry_run"] is True
    assert config["max_open_trades"] == 2
    assert config["stake_amount"] == 100
    assert config["dry_run_wallet"] == 10000


def test_extract_backtest_emits_common_evidence_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    strategy = EXPECTED_CANDIDATES[0]

    def fake_loader(_path: Path):
        return _stats(strategy), "backtest-result.json", "a" * 64

    monkeypatch.setattr(
        "ai_platform.scripts.model_comparison_oos_result_extractor._load_backtest_stats",
        fake_loader,
    )

    result = extract_backtest(Path("unused.zip"), strategy)

    assert result["strategy"] == strategy
    assert result["metrics"]["total_trades"] == 2
    assert result["metrics"]["trade_profit_abs_sum"] == 8.0
    assert result["pair_breakdown"] == [
        {"pair": "BTC/USD:USD", "trades": 1, "profit_abs_sum": 10.0},
        {"pair": "ETH/USD:USD", "trades": 1, "profit_abs_sum": -2.0},
    ]
    assert result["direction_breakdown"]["long"]["trades"] == 1
    assert result["direction_breakdown"]["short"]["trades"] == 1
    assert result["authorization"]["automatic_promotion_allowed"] is False


def test_extract_backtest_rejects_trade_from_unfrozen_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strategy = EXPECTED_CANDIDATES[1]

    def fake_loader(_path: Path):
        return _stats(strategy, pair="SOL/USD:USD"), "backtest-result.json", "b" * 64

    monkeypatch.setattr(
        "ai_platform.scripts.model_comparison_oos_result_extractor._load_backtest_stats",
        fake_loader,
    )

    with pytest.raises(TradingViewHistoricalBenchmarkError, match="unexpected pair"):
        extract_backtest(Path("unused.zip"), strategy)
