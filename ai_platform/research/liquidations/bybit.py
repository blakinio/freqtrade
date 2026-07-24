from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from ai_platform.research.liquidations.contracts import (
    LiquidatedPositionSide,
    LiquidationEvent,
    deterministic_event_id,
    positive_decimal,
)


BYBIT_SOURCE = "bybit-linear"


def _require_sequence(value: object, *, field: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def _require_mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _normalize_position_side(raw_side: str) -> LiquidatedPositionSide:
    normalized = raw_side.strip().lower()
    # Bybit's allLiquidation feed documents S=Buy as a liquidated long
    # position and S=Sell as a liquidated short position.
    if normalized == "buy":
        return LiquidatedPositionSide.LONG
    if normalized == "sell":
        return LiquidatedPositionSide.SHORT
    raise ValueError(f"unsupported Bybit liquidation side: {raw_side}")


def parse_bybit_all_liquidation(
    message: Mapping[str, object],
    *,
    received_at_ms: int,
) -> tuple[LiquidationEvent, ...]:
    topic = str(message.get("topic", ""))
    if not topic.startswith("allLiquidation."):
        raise ValueError("message is not a Bybit allLiquidation topic")
    if received_at_ms <= 0:
        raise ValueError("received_at_ms must be > 0")

    rows = _require_sequence(message.get("data"), field="data")
    try:
        source_message_at_ms = int(message["ts"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Bybit message ts must be an integer timestamp") from exc
    events: list[LiquidationEvent] = []
    for index, raw_row in enumerate(rows):
        row = _require_mapping(raw_row, field=f"data[{index}]")
        try:
            occurred_at_ms = int(row["T"])
            symbol = str(row["s"]).strip().upper()
            raw_side = str(row["S"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid Bybit liquidation row at index {index}") from exc

        price = positive_decimal(row.get("p"), field="price")
        quantity = positive_decimal(row.get("v"), field="quantity")
        notional = price * quantity
        event_id = deterministic_event_id(
            source=BYBIT_SOURCE,
            symbol=symbol,
            occurred_at_ms=occurred_at_ms,
            raw_side=raw_side,
            price=price,
            quantity=quantity,
            source_discriminator=f"{source_message_at_ms}:{index}",
        )
        events.append(
            LiquidationEvent(
                schema_version=1,
                source=BYBIT_SOURCE,
                source_event_id=event_id,
                symbol=symbol,
                liquidated_position_side=_normalize_position_side(raw_side),
                occurred_at_ms=occurred_at_ms,
                received_at_ms=received_at_ms,
                price=Decimal(price),
                quantity=Decimal(quantity),
                notional_usd=Decimal(notional),
                raw_side=raw_side,
            )
        )
    return tuple(events)
