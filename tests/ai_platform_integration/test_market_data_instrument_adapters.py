from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import Any

import pytest

from ai_platform.market_data import Exchange, MarketType
from ai_platform.market_data.instrument_adapters import (
    BINANCE_SPOT_URL,
    BYBIT_LINEAR_URL,
    BYBIT_SPOT_URL,
    OKX_FUTURES_URL,
    OKX_SPOT_URL,
    OKX_SWAP_URL,
    InstrumentCatalogSnapshot,
    collect_instrument_catalog,
    parse_binance_spot_catalog,
    parse_okx_derivatives_catalog,
)


CAPTURED_AT_MS = 1_800_000_000_000


def binance_spot_payload() -> dict[str, Any]:
    return {
        "timezone": "UTC",
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.10"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.00001"},
                ],
            },
            {
                "symbol": "OLDUSDT",
                "status": "BREAK",
                "baseAsset": "OLD",
                "quoteAsset": "USDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                    {"filterType": "LOT_SIZE", "stepSize": "1"},
                ],
            },
        ],
    }


def bybit_spot_payload() -> dict[str, Any]:
    return {
        "retCode": 0,
        "result": {
            "category": "spot",
            "nextPageCursor": "",
            "list": [
                {
                    "symbol": "ETHUSDT",
                    "status": "Trading",
                    "baseCoin": "ETH",
                    "quoteCoin": "USDT",
                    "priceFilter": {"tickSize": "0.01"},
                    "lotSizeFilter": {"basePrecision": "0.0001"},
                },
            ],
        },
    }


def bybit_linear_pages() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        {
            "retCode": 0,
            "result": {
                "category": "linear",
                "nextPageCursor": "page-2",
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "status": "Trading",
                        "contractType": "LinearPerpetual",
                        "baseCoin": "BTC",
                        "quoteCoin": "USDT",
                        "settleCoin": "USDT",
                        "launchTime": "1700000000000",
                        "deliveryTime": "0",
                        "priceFilter": {"tickSize": "0.10"},
                        "lotSizeFilter": {"qtyStep": "0.001"},
                    },
                ],
            },
        },
        {
            "retCode": 0,
            "result": {
                "category": "linear",
                "nextPageCursor": "",
                "list": [
                    {
                        "symbol": "BTCUSDT-26SEP26",
                        "status": "Trading",
                        "contractType": "LinearFutures",
                        "baseCoin": "BTC",
                        "quoteCoin": "USDT",
                        "settleCoin": "USDT",
                        "launchTime": "1700000000000",
                        "deliveryTime": "1800000000000",
                        "priceFilter": {"tickSize": "0.10"},
                        "lotSizeFilter": {"qtyStep": "0.001"},
                    },
                ],
            },
        },
    )


def okx_spot_payload() -> dict[str, Any]:
    return {
        "code": "0",
        "data": [
            {
                "instType": "SPOT",
                "instId": "SOL-USDT",
                "baseCcy": "SOL",
                "quoteCcy": "USDT",
                "state": "live",
                "tickSz": "0.001",
                "lotSz": "0.01",
                "listTime": "1700000000000",
                "expTime": "",
            },
        ],
    }


def okx_swap_payload(*, ct_mult: str = "1") -> dict[str, Any]:
    return {
        "code": "0",
        "data": [
            {
                "instType": "SWAP",
                "instId": "BTC-USDT-SWAP",
                "uly": "BTC-USDT",
                "instFamily": "BTC-USDT",
                "settleCcy": "USDT",
                "state": "live",
                "ctVal": "0.01",
                "ctValCcy": "BTC",
                "ctMult": ct_mult,
                "tickSz": "0.1",
                "lotSz": "1",
                "listTime": "1700000000000",
                "expTime": "",
            },
        ],
    }


def okx_futures_payload() -> dict[str, Any]:
    return {
        "code": "0",
        "data": [
            {
                "instType": "FUTURES",
                "instId": "ETH-USDT-260925",
                "uly": "ETH-USDT",
                "instFamily": "ETH-USDT",
                "settleCcy": "USDT",
                "state": "live",
                "ctVal": "0.1",
                "ctValCcy": "ETH",
                "ctMult": "1",
                "tickSz": "0.01",
                "lotSz": "1",
                "listTime": "1700000000000",
                "expTime": "1800000000000",
            },
        ],
    }


class FakeFetcher:
    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses
        self.urls: list[str] = []

    def __call__(self, url: str) -> dict[str, Any]:
        self.urls.append(url)
        try:
            return self.responses[url]
        except KeyError as exc:
            raise AssertionError(f"unexpected URL: {url}") from exc


def test_binance_spot_snapshot_is_deterministic_and_source_bound() -> None:
    payload = binance_spot_payload()
    first = parse_binance_spot_catalog(payload, captured_at_ms=CAPTURED_AT_MS)
    second = parse_binance_spot_catalog(payload, captured_at_ms=CAPTURED_AT_MS)
    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.source_snapshot_id == second.source_snapshot_id
    assert len(first.instruments) == 2
    btc = next(item for item in first.instruments if item.native_symbol == "BTCUSDT")
    old = next(item for item in first.instruments if item.native_symbol == "OLDUSDT")
    assert btc.exchange is Exchange.BINANCE
    assert btc.market_type is MarketType.SPOT
    assert btc.tick_size == Decimal("0.1")
    assert btc.quantity_step == Decimal("0.00001")
    assert btc.active is True
    assert old.active is False
    assert btc.source_snapshot_sha256 == first.source_snapshot_sha256
    with pytest.raises(ValueError, match="snapshot_sha256"):
        replace(first, captured_at_ms=CAPTURED_AT_MS + 1)


def test_collect_bybit_linear_is_bounded_and_follows_cursor() -> None:
    first, second = bybit_linear_pages()
    second_url = BYBIT_LINEAR_URL + "&cursor=page-2"
    fetcher = FakeFetcher({BYBIT_LINEAR_URL: first, second_url: second})
    snapshot = collect_instrument_catalog(
        source_id="bybit-linear",
        fetch_json=fetcher,
        captured_at_ms=CAPTURED_AT_MS,
    )
    assert fetcher.urls == [BYBIT_LINEAR_URL, second_url]
    assert len(snapshot.request_urls) == 2
    assert [item.market_type for item in snapshot.instruments] == [
        MarketType.DATED_FUTURE,
        MarketType.PERPETUAL,
    ]
    assert all(item.contract_value == Decimal("1") for item in snapshot.instruments)
    assert all(item.contract_value_unit == "base_asset" for item in snapshot.instruments)


def test_collect_all_five_ready_sources_without_default_network() -> None:
    linear_first, linear_second = bybit_linear_pages()
    second_url = BYBIT_LINEAR_URL + "&cursor=page-2"
    responses = {
        BINANCE_SPOT_URL: binance_spot_payload(),
        BYBIT_SPOT_URL: bybit_spot_payload(),
        BYBIT_LINEAR_URL: linear_first,
        second_url: linear_second,
        OKX_SPOT_URL: okx_spot_payload(),
        OKX_SWAP_URL: okx_swap_payload(),
        OKX_FUTURES_URL: okx_futures_payload(),
    }
    expected_counts = {
        "binance-spot": 2,
        "bybit-spot": 1,
        "bybit-linear": 2,
        "okx-spot": 1,
        "okx-swap-futures": 2,
    }
    for source_id, expected_count in expected_counts.items():
        fetcher = FakeFetcher(responses)
        snapshot = collect_instrument_catalog(
            source_id=source_id,
            fetch_json=fetcher,
            captured_at_ms=CAPTURED_AT_MS,
        )
        assert isinstance(snapshot, InstrumentCatalogSnapshot)
        assert snapshot.source_id == source_id
        assert len(snapshot.instruments) == expected_count
        assert all(url.startswith("https://") for url in fetcher.urls)


def test_okx_derivatives_reject_non_unit_multiplier() -> None:
    with pytest.raises(ValueError, match="non-unit OKX ctMult"):
        parse_okx_derivatives_catalog(
            (okx_swap_payload(ct_mult="100"), okx_futures_payload()),
            captured_at_ms=CAPTURED_AT_MS,
        )


def test_blocked_credentials_unknown_sources_and_repeated_cursor_fail_closed() -> None:
    fetcher = FakeFetcher({BINANCE_SPOT_URL: binance_spot_payload()})
    with pytest.raises(RuntimeError, match="binance-usdm is blocked"):
        collect_instrument_catalog(
            source_id="binance-usdm",
            fetch_json=fetcher,
            captured_at_ms=CAPTURED_AT_MS,
        )
    with pytest.raises(RuntimeError, match="BINANCE_API_KEY"):
        collect_instrument_catalog(
            source_id="binance-spot",
            fetch_json=fetcher,
            captured_at_ms=CAPTURED_AT_MS,
            environment={"BINANCE_API_KEY": "secret"},
        )
    with pytest.raises(ValueError, match="unsupported instrument adapter"):
        collect_instrument_catalog(
            source_id="unknown",
            fetch_json=fetcher,
            captured_at_ms=CAPTURED_AT_MS,
        )
    repeated = bybit_linear_pages()[0]
    repeated_fetcher = FakeFetcher(
        {
            BYBIT_LINEAR_URL: repeated,
            BYBIT_LINEAR_URL + "&cursor=page-2": repeated,
        },
    )
    with pytest.raises(RuntimeError, match="pagination cursor repeated"):
        collect_instrument_catalog(
            source_id="bybit-linear",
            fetch_json=repeated_fetcher,
            captured_at_ms=CAPTURED_AT_MS,
        )
