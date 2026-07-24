from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from ai_platform.research.liquidations.contracts import (
    LiquidatedPositionSide,
    LiquidationEvent,
    deterministic_event_id,
    integer_value,
    positive_decimal,
)


BINANCE_USDM_SOURCE = "binance-usdm"


def _require_mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be an object")
    return value


def _unwrap_payload(message: Mapping[str, object]) -> Mapping[str, object]:
    if "stream" not in message:
        return message
    return _require_mapping(message.get("data"), field="data")


def _normalize_position_side(order_side: str) -> LiquidatedPositionSide:
    normalized = order_side.strip().upper()
    # Binance publishes the side of the forced close order. SELL closes a long;
    # BUY closes a short.
    if normalized == "SELL":
        return LiquidatedPositionSide.LONG
    if normalized == "BUY":
        return LiquidatedPositionSide.SHORT
    raise ValueError(f"unsupported Binance liquidation order side: {order_side}")


def _first_positive_decimal(
    order: Mapping[str, object],
    fields: tuple[str, ...],
    *,
    semantic_name: str,
) -> Decimal:
    last_error: Exception | None = None
    for field in fields:
        try:
            return positive_decimal(order.get(field), field=field)
        except (TypeError, ValueError) as exc:
            last_error = exc
    raise ValueError(
        f"Binance liquidation {semantic_name} must be present and positive in one of {fields}"
    ) from last_error


def parse_binance_force_order(
    message: Mapping[str, object],
    *,
    received_at_ms: int,
) -> tuple[LiquidationEvent, ...]:
    payload = _unwrap_payload(message)
    if str(payload.get("e", "")) != "forceOrder":
        raise ValueError("message is not a Binance forceOrder event")
    if received_at_ms <= 0:
        raise ValueError("received_at_ms must be > 0")

    order = _require_mapping(payload.get("o"), field="o")
    try:
        event_time_ms = integer_value(payload["E"], field="E")
        occurred_at_ms = integer_value(order["T"], field="o.T")
        symbol = str(order["s"]).strip().upper()
        raw_side = str(order["S"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid Binance forceOrder payload") from exc

    if not symbol:
        raise ValueError("Binance forceOrder symbol must be non-empty")

    # Prefer actually executed accumulated quantity and average fill price. Fall
    # back to the last fill and then original order values for older payloads.
    quantity = _first_positive_decimal(
        order,
        ("z", "l", "q"),
        semantic_name="quantity",
    )
    price = _first_positive_decimal(
        order,
        ("ap", "p"),
        semantic_name="price",
    )
    notional = price * quantity
    status = str(order.get("X", ""))
    event_id = deterministic_event_id(
        source=BINANCE_USDM_SOURCE,
        symbol=symbol,
        occurred_at_ms=occurred_at_ms,
        raw_side=raw_side,
        price=price,
        quantity=quantity,
        source_discriminator=f"{event_time_ms}:{status}",
    )

    return (
        LiquidationEvent(
            schema_version=1,
            source=BINANCE_USDM_SOURCE,
            source_event_id=event_id,
            symbol=symbol,
            liquidated_position_side=_normalize_position_side(raw_side),
            occurred_at_ms=occurred_at_ms,
            received_at_ms=received_at_ms,
            price=Decimal(price),
            quantity=Decimal(quantity),
            notional_usd=Decimal(notional),
            raw_side=raw_side,
        ),
    )
