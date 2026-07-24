from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from typing import Any, Mapping


class LiquidatedPositionSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class CounterTradeAction(StrEnum):
    ENTER_LONG = "enter_long"
    ENTER_SHORT = "enter_short"
    IGNORE = "ignore"


def positive_decimal(value: object, *, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be a decimal-compatible value") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError(f"{field} must be finite and > 0")
    return parsed


def non_negative_decimal(value: object, *, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be a decimal-compatible value") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{field} must be finite and >= 0")
    return parsed


@dataclass(frozen=True, slots=True)
class LiquidationEvent:
    schema_version: int
    source: str
    source_event_id: str
    symbol: str
    liquidated_position_side: LiquidatedPositionSide
    occurred_at_ms: int
    received_at_ms: int
    price: Decimal
    quantity: Decimal
    notional_usd: Decimal
    raw_side: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        if not self.source.strip():
            raise ValueError("source must be non-empty")
        if not self.source_event_id.strip():
            raise ValueError("source_event_id must be non-empty")
        if not self.symbol.strip():
            raise ValueError("symbol must be non-empty")
        if self.occurred_at_ms <= 0:
            raise ValueError("occurred_at_ms must be > 0")
        if self.received_at_ms < self.occurred_at_ms:
            raise ValueError("received_at_ms must be >= occurred_at_ms")
        positive_decimal(self.price, field="price")
        positive_decimal(self.quantity, field="quantity")
        positive_decimal(self.notional_usd, field="notional_usd")
        if not self.raw_side.strip():
            raise ValueError("raw_side must be non-empty")

    @property
    def ingest_latency_ms(self) -> int:
        return self.received_at_ms - self.occurred_at_ms

    def as_json_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["liquidated_position_side"] = self.liquidated_position_side.value
        result["price"] = str(self.price)
        result["quantity"] = str(self.quantity)
        result["notional_usd"] = str(self.notional_usd)
        return result


def deterministic_event_id(
    *,
    source: str,
    symbol: str,
    occurred_at_ms: int,
    raw_side: str,
    price: Decimal,
    quantity: Decimal,
    source_discriminator: str = "",
) -> str:
    canonical = "|".join(
        (
            source.strip().lower(),
            symbol.strip().upper(),
            str(occurred_at_ms),
            raw_side.strip().lower(),
            format(price, "f"),
            format(quantity, "f"),
            source_discriminator.strip(),
        )
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def event_from_json_dict(payload: Mapping[str, object]) -> LiquidationEvent:
    try:
        side = LiquidatedPositionSide(str(payload["liquidated_position_side"]))
        occurred_at_ms = int(payload["occurred_at_ms"])
        received_at_ms = int(payload["received_at_ms"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid canonical liquidation event") from exc

    return LiquidationEvent(
        schema_version=int(payload.get("schema_version", 0)),
        source=str(payload.get("source", "")),
        source_event_id=str(payload.get("source_event_id", "")),
        symbol=str(payload.get("symbol", "")),
        liquidated_position_side=side,
        occurred_at_ms=occurred_at_ms,
        received_at_ms=received_at_ms,
        price=positive_decimal(payload.get("price"), field="price"),
        quantity=positive_decimal(payload.get("quantity"), field="quantity"),
        notional_usd=positive_decimal(payload.get("notional_usd"), field="notional_usd"),
        raw_side=str(payload.get("raw_side", "")),
    )
