from __future__ import annotations

from decimal import Decimal

import pytest

from ai_platform.research.liquidations.alignment import (
    align_event_to_closed_candles,
    timeframe_to_ms,
)
from ai_platform.research.liquidations.bybit import parse_bybit_all_liquidation
from ai_platform.research.liquidations.contracts import (
    CounterTradeAction,
    LiquidatedPositionSide,
    event_from_json_dict,
)
from ai_platform.research.liquidations.signals import (
    LiquidationSignalPolicy,
    decide_counter_trade,
)
from ai_platform.scripts.liquidation_collector import RecentEventIds, _subscription


def _bybit_message(*, side: str, price: str = "70000", size: str = "2") -> dict:
    return {
        "topic": "allLiquidation.BTCUSDT",
        "type": "snapshot",
        "ts": 1_750_000_000_500,
        "data": [
            {
                "T": 1_750_000_000_000,
                "s": "BTCUSDT",
                "S": side,
                "v": size,
                "p": price,
            }
        ],
    }


def _policy() -> LiquidationSignalPolicy:
    return LiquidationSignalPolicy.create(
        allowed_sources=["bybit-linear"],
        allowed_symbols=["BTCUSDT"],
        minimum_notional_usd="75000",
        long_distance_ratio="0.015",
        short_distance_ratio="0.015",
        maximum_event_age_ms=2_000,
    )


def test_bybit_buy_side_is_normalized_as_liquidated_long() -> None:
    event = parse_bybit_all_liquidation(
        _bybit_message(side="Buy"),
        received_at_ms=1_750_000_000_500,
    )[0]

    assert event.liquidated_position_side is LiquidatedPositionSide.LONG
    assert event.notional_usd == Decimal(140000)
    assert event.ingest_latency_ms == 500


def test_bybit_sell_side_is_normalized_as_liquidated_short() -> None:
    event = parse_bybit_all_liquidation(
        _bybit_message(side="Sell"),
        received_at_ms=1_750_000_000_500,
    )[0]

    assert event.liquidated_position_side is LiquidatedPositionSide.SHORT


def test_identical_rows_in_one_message_have_distinct_event_ids() -> None:
    message = _bybit_message(side="Buy")
    message["data"] = [message["data"][0], dict(message["data"][0])]

    events = parse_bybit_all_liquidation(
        message,
        received_at_ms=1_750_000_000_500,
    )

    assert len(events) == 2
    assert events[0].source_event_id != events[1].source_event_id


def test_canonical_event_round_trip_preserves_decimal_values() -> None:
    event = parse_bybit_all_liquidation(
        _bybit_message(side="Buy"),
        received_at_ms=1_750_000_000_500,
    )[0]

    restored = event_from_json_dict(event.as_json_dict())

    assert restored == event


def test_alignment_uses_only_the_last_completed_candle() -> None:
    event = parse_bybit_all_liquidation(
        _bybit_message(side="Buy"),
        received_at_ms=1_750_000_000_500,
    )[0]

    alignment = align_event_to_closed_candles(event, timeframe="1m")

    assert alignment.timeframe_ms == 60_000
    assert alignment.containing_candle_open_ms <= event.occurred_at_ms
    assert event.occurred_at_ms < alignment.containing_candle_close_ms
    assert alignment.last_completed_candle_open_ms == (
        alignment.containing_candle_open_ms - 60_000
    )


def test_liquidated_long_below_lower_band_enters_long() -> None:
    event = parse_bybit_all_liquidation(
        _bybit_message(side="Buy", price="98", size="1000"),
        received_at_ms=1_750_000_000_500,
    )[0]

    decision = decide_counter_trade(
        event,
        completed_candle_vwap="100",
        decision_time_ms=1_750_000_000_500,
        policy=_policy(),
    )

    assert decision.action is CounterTradeAction.ENTER_LONG


def test_liquidated_short_above_upper_band_enters_short() -> None:
    event = parse_bybit_all_liquidation(
        _bybit_message(side="Sell", price="102", size="1000"),
        received_at_ms=1_750_000_000_500,
    )[0]

    decision = decide_counter_trade(
        event,
        completed_candle_vwap="100",
        decision_time_ms=1_750_000_000_500,
        policy=_policy(),
    )

    assert decision.action is CounterTradeAction.ENTER_SHORT


def test_stale_event_is_rejected() -> None:
    event = parse_bybit_all_liquidation(
        _bybit_message(side="Buy", price="98", size="1000"),
        received_at_ms=1_750_000_000_500,
    )[0]

    decision = decide_counter_trade(
        event,
        completed_candle_vwap="100",
        decision_time_ms=1_750_000_003_000,
        policy=_policy(),
    )

    assert decision.action is CounterTradeAction.IGNORE
    assert decision.reason == "stale_event"


def test_recent_event_ids_deduplicate_with_bounded_memory() -> None:
    event_ids = RecentEventIds(maximum_size=2)

    assert event_ids.add_if_new("a") is True
    assert event_ids.add_if_new("a") is False
    assert event_ids.add_if_new("b") is True
    assert event_ids.add_if_new("c") is True
    assert event_ids.add_if_new("a") is True


def test_subscription_is_explicit_per_symbol() -> None:
    assert _subscription(("BTCUSDT", "ETHUSDT")) == (
        '{"op":"subscribe","args":'
        '["allLiquidation.BTCUSDT","allLiquidation.ETHUSDT"]}'
    )


def test_invalid_timeframe_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported timeframe unit"):
        timeframe_to_ms("5x")
