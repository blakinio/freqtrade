from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from ai_platform.research.liquidations.contracts import LiquidatedPositionSide
from ai_platform.research.liquidations.okx import (
    canonical_symbol_from_inst_id,
    parse_okx_instruments_response,
    parse_okx_liquidation_orders,
)
from ai_platform.research.liquidations.staging import CollectorRunStats
from ai_platform.scripts.liquidation_collector import RecentEventIds
from ai_platform.scripts.liquidation_okx_collector import (
    _process_payload,
    _subscription,
    build_instrument_snapshot,
    parse_okx_server_time_response,
)


def _instrument_payload(
    *,
    inst_id: str = "BTC-USDT-SWAP",
    ct_val: str = "0.01",
    ct_mult: str = "1",
    state: str = "live",
) -> dict[str, object]:
    return {
        "code": "0",
        "data": [
            {
                "instType": "SWAP",
                "instId": inst_id,
                "ctVal": ct_val,
                "ctMult": ct_mult,
                "ctValCcy": inst_id.split("-")[0],
                "settleCcy": "USDT",
                "ctType": "linear",
                "state": state,
            }
        ],
    }


def _liquidation_payload(
    *,
    inst_id: str = "BTC-USDT-SWAP",
    side: str = "sell",
    position_side: str = "long",
    size: str = "25",
    bankruptcy_price: str = "70000",
) -> dict[str, object]:
    return {
        "arg": {"channel": "liquidation-orders", "instType": "SWAP"},
        "data": [
            {
                "instType": "SWAP",
                "instId": inst_id,
                "details": [
                    {
                        "side": side,
                        "posSide": position_side,
                        "bkPx": bankruptcy_price,
                        "sz": size,
                        "bkLoss": "125",
                        "ccy": "USDT",
                        "ts": "1750000000000",
                    }
                ],
            }
        ],
    }


def test_okx_symbol_mapping_is_explicit() -> None:
    assert canonical_symbol_from_inst_id("btc-usdt-swap") == "BTCUSDT"
    with pytest.raises(ValueError, match="unsupported OKX USDT swap"):
        canonical_symbol_from_inst_id("BTC-USD-SWAP")


def test_okx_instruments_freeze_contract_normalization() -> None:
    instruments = parse_okx_instruments_response(
        _instrument_payload(),
        requested_symbols=("BTCUSDT",),
    )
    contract = instruments["BTC-USDT-SWAP"]

    assert contract.canonical_symbol == "BTCUSDT"
    assert contract.contract_value == Decimal("0.01")
    assert contract.base_quantity(Decimal("25")) == Decimal("0.25")


def test_okx_instruments_reject_unsupported_contract_metadata() -> None:
    with pytest.raises(ValueError, match="multiplier"):
        parse_okx_instruments_response(
            _instrument_payload(ct_mult="10"),
            requested_symbols=("BTCUSDT",),
        )
    with pytest.raises(ValueError, match="state must be live"):
        parse_okx_instruments_response(
            _instrument_payload(state="suspend"),
            requested_symbols=("BTCUSDT",),
        )
    with pytest.raises(ValueError, match="missing OKX instrument metadata"):
        parse_okx_instruments_response(
            _instrument_payload(),
            requested_symbols=("ETHUSDT",),
        )


def test_okx_liquidation_converts_contracts_to_base_quantity() -> None:
    instruments = parse_okx_instruments_response(
        _instrument_payload(),
        requested_symbols=("BTCUSDT",),
    )
    event = parse_okx_liquidation_orders(
        _liquidation_payload(),
        received_at_ms=1_750_000_000_250,
        instruments=instruments,
        allowed_symbols=("BTCUSDT",),
    )[0]

    assert event.source == "okx-usdt-swap"
    assert event.symbol == "BTCUSDT"
    assert event.liquidated_position_side is LiquidatedPositionSide.LONG
    assert event.price == Decimal("70000")
    assert event.quantity == Decimal("0.25")
    assert event.notional_usd == Decimal("17500.00")
    assert event.ingest_latency_ms == 250


def test_okx_position_side_and_net_mode_are_normalized() -> None:
    instruments = parse_okx_instruments_response(
        _instrument_payload(),
        requested_symbols=("BTCUSDT",),
    )
    short_event = parse_okx_liquidation_orders(
        _liquidation_payload(side="buy", position_side="short"),
        received_at_ms=1_750_000_000_250,
        instruments=instruments,
    )[0]
    net_short_event = parse_okx_liquidation_orders(
        _liquidation_payload(side="buy", position_side="net"),
        received_at_ms=1_750_000_000_250,
        instruments=instruments,
    )[0]

    assert short_event.liquidated_position_side is LiquidatedPositionSide.SHORT
    assert net_short_event.liquidated_position_side is LiquidatedPositionSide.SHORT


def test_okx_global_channel_filters_unrequested_instruments_before_metadata_lookup() -> None:
    instruments = parse_okx_instruments_response(
        _instrument_payload(),
        requested_symbols=("BTCUSDT",),
    )
    events = parse_okx_liquidation_orders(
        _liquidation_payload(inst_id="ETH-USDT-SWAP"),
        received_at_ms=1_750_000_000_250,
        instruments=instruments,
        allowed_symbols=("BTCUSDT",),
    )

    assert events == ()


def test_okx_subscription_is_public_global_swap_channel() -> None:
    assert _subscription() == (
        '{"op":"subscribe","args":[{"channel":"liquidation-orders","instType":"SWAP"}]}'
    )


def test_okx_process_payload_tracks_control_and_duplicates() -> None:
    instruments = parse_okx_instruments_response(
        _instrument_payload(),
        requested_symbols=("BTCUSDT",),
    )
    stats = CollectorRunStats(started_at_ms=1_750_000_000_000)
    recent_ids = RecentEventIds()

    control = _process_payload(
        {"event": "subscribe", "arg": {"channel": "liquidation-orders"}},
        received_at_ms=1_750_000_000_100,
        instruments=instruments,
        allowed_symbols=("BTCUSDT",),
        recent_ids=recent_ids,
        stats=stats,
    )
    first = _process_payload(
        _liquidation_payload(),
        received_at_ms=1_750_000_000_250,
        instruments=instruments,
        allowed_symbols=("BTCUSDT",),
        recent_ids=recent_ids,
        stats=stats,
    )
    duplicate = _process_payload(
        _liquidation_payload(),
        received_at_ms=1_750_000_000_250,
        instruments=instruments,
        allowed_symbols=("BTCUSDT",),
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


def test_okx_clock_probe_uses_request_midpoint() -> None:
    result = parse_okx_server_time_response(
        {"code": "0", "data": [{"ts": "1750000000000"}]},
        request_started_at_ms=1_749_999_999_900,
        request_ended_at_ms=1_750_000_000_100,
        tolerance_ms=500,
    )

    assert result.round_trip_ms == 200
    assert result.absolute_skew_ms == 0
    assert result.synchronized is True


def test_okx_instrument_snapshot_records_normalization_formula() -> None:
    instruments = parse_okx_instruments_response(
        _instrument_payload(),
        requested_symbols=("BTCUSDT",),
    )
    snapshot = build_instrument_snapshot(
        instruments=instruments,
        instruments_url="https://www.okx.com/api/v5/public/instruments?instType=SWAP",
        fetched_at_ms=1_750_000_000_000,
    )

    assert snapshot["source"] == "okx-usdt-swap"
    policy = snapshot["normalization_policy"]
    assert isinstance(policy, dict)
    assert policy["quantity_formula"] == "base_quantity = contracts * ctVal"


def test_source_catalog_marks_okx_as_shadow_only() -> None:
    catalog_path = (
        Path(__file__).parents[2]
        / "ai_platform"
        / "research"
        / "liquidations"
        / "source-catalog-v1.json"
    )
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    sources = {item["source"]: item for item in payload["sources"]}

    assert set(sources) == {"bybit-linear", "binance-usdm", "okx-usdt-swap"}
    assert sources["okx-usdt-swap"]["included_in_liquid20_v1"] is False
    assert "ctVal" in sources["okx-usdt-swap"]["quantity_semantics"]
