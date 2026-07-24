from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from ai_platform.research.liquidations.binance import parse_binance_force_order
from ai_platform.research.liquidations.contracts import LiquidatedPositionSide
from ai_platform.research.liquidations.staging import CollectorRunStats
from ai_platform.scripts.liquidation_binance_collector import (
    _process_payload,
    _subscription,
    parse_binance_server_time_response,
)
from ai_platform.scripts.liquidation_collector import RecentEventIds


def _force_order(
    *,
    side: str = "SELL",
    average_price: str = "70000",
    order_price: str = "69900",
    accumulated_quantity: str = "1.5",
    last_quantity: str = "1",
    original_quantity: str = "2",
) -> dict[str, object]:
    return {
        "e": "forceOrder",
        "E": 1_750_000_000_500,
        "o": {
            "s": "BTCUSDT",
            "S": side,
            "q": original_quantity,
            "p": order_price,
            "ap": average_price,
            "X": "FILLED",
            "l": last_quantity,
            "z": accumulated_quantity,
            "T": 1_750_000_000_000,
        },
    }


def test_binance_sell_force_order_is_liquidated_long() -> None:
    event = parse_binance_force_order(
        _force_order(side="SELL"),
        received_at_ms=1_750_000_000_600,
    )[0]

    assert event.source == "binance-usdm"
    assert event.liquidated_position_side is LiquidatedPositionSide.LONG
    assert event.price == Decimal("70000")
    assert event.quantity == Decimal("1.5")
    assert event.notional_usd == Decimal("105000.0")
    assert event.ingest_latency_ms == 600


def test_binance_buy_force_order_is_liquidated_short() -> None:
    event = parse_binance_force_order(
        _force_order(side="BUY"),
        received_at_ms=1_750_000_000_600,
    )[0]

    assert event.liquidated_position_side is LiquidatedPositionSide.SHORT


def test_binance_parser_prefers_executed_values_and_falls_back() -> None:
    event = parse_binance_force_order(
        _force_order(
            average_price="0",
            order_price="68000",
            accumulated_quantity="0",
            last_quantity="0.25",
            original_quantity="1",
        ),
        received_at_ms=1_750_000_000_600,
    )[0]

    assert event.price == Decimal("68000")
    assert event.quantity == Decimal("0.25")
    assert event.notional_usd == Decimal("17000.00")


def test_binance_combined_stream_wrapper_is_supported() -> None:
    event = parse_binance_force_order(
        {"stream": "btcusdt@forceOrder", "data": _force_order()},
        received_at_ms=1_750_000_000_600,
    )[0]

    assert event.symbol == "BTCUSDT"


def test_binance_subscription_is_explicit_per_symbol() -> None:
    assert _subscription(("BTCUSDT", "ETHUSDT")) == (
        '{"method":"SUBSCRIBE","params":["btcusdt@forceOrder",'
        '"ethusdt@forceOrder"],"id":1}'
    )


def test_binance_process_payload_tracks_control_and_duplicates() -> None:
    stats = CollectorRunStats(started_at_ms=1_750_000_000_000)
    recent_ids = RecentEventIds()

    control = _process_payload(
        {"result": None, "id": 1},
        received_at_ms=1_750_000_000_100,
        recent_ids=recent_ids,
        stats=stats,
    )
    first = _process_payload(
        _force_order(),
        received_at_ms=1_750_000_000_600,
        recent_ids=recent_ids,
        stats=stats,
    )
    duplicate = _process_payload(
        _force_order(),
        received_at_ms=1_750_000_000_600,
        recent_ids=recent_ids,
        stats=stats,
    )

    assert control == ()
    assert len(first) == 1
    assert duplicate == ()
    assert stats.control_messages == 1
    assert stats.liquidation_messages == 2
    assert stats.events_written == 1
    assert stats.duplicates == 1


def test_binance_clock_probe_uses_request_midpoint() -> None:
    result = parse_binance_server_time_response(
        {"serverTime": 1_750_000_000_000},
        request_started_at_ms=1_749_999_999_900,
        request_ended_at_ms=1_750_000_000_100,
        tolerance_ms=500,
    )

    assert result.round_trip_ms == 200
    assert result.absolute_skew_ms == 0
    assert result.synchronized is True


def test_non_force_order_payload_fails_closed() -> None:
    with pytest.raises(ValueError, match="not a Binance forceOrder"):
        parse_binance_force_order(
            {"e": "aggTrade"},
            received_at_ms=1_750_000_000_600,
        )


def test_source_catalog_preserves_feed_semantics() -> None:
    catalog_path = (
        Path(__file__).parents[2]
        / "ai_platform"
        / "research"
        / "liquidations"
        / "source-catalog-v1.json"
    )
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    sources = {item["source"]: item for item in payload["sources"]}

    assert set(sources) == {"bybit-linear", "binance-usdm"}
    assert "all liquidation events" in sources["bybit-linear"]["coverage_semantics"]
    assert "latest liquidation order" in sources["binance-usdm"]["coverage_semantics"]
    assert payload["cross_source_policy"]["deduplicate_between_exchanges"] is False
