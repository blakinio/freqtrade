from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from typing import Any

from ai_platform.research.liquidations.contracts import LiquidatedPositionSide


_HEX_DIGITS = frozenset("0123456789abcdef")


class DatasetOrigin(StrEnum):
    HISTORICAL_VENDOR = "historical_vendor"
    SYNTHETIC_FIXTURE = "synthetic_fixture"


class AvailableAtSemantics(StrEnum):
    VENDOR_CAPTURE_TIMESTAMP = "vendor_capture_timestamp"
    EXCHANGE_TIMESTAMP_FALLBACK = "exchange_timestamp_fallback"
    COMPLETED_INTERVAL = "completed_interval"


def canonical_decimal(value: object, *, field: str, positive: bool = False) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")
    if positive and parsed <= 0:
        raise ValueError(f"{field} must be > 0")
    return parsed


def decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("decimal must be finite")
    normalized = format(value, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return "0" if normalized in {"", "-0"} else normalized


def integer_value(value: object, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise TypeError(f"{field} must be an integer or integer string")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer or integer string") from exc
    if parsed < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return parsed


def microseconds_to_milliseconds(value: object, *, field: str) -> int:
    return integer_value(value, field=field, minimum=1) // 1000


def validate_sha256(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in _HEX_DIGITS for char in normalized):
        raise ValueError(f"{field} must be a lowercase SHA-256 hex digest")
    return normalized


def _require_text(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must be non-empty")
    return normalized


def _digest(parts: tuple[str, ...]) -> str:
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def historical_event_fingerprint(
    *,
    historical_provider: str,
    provider_exchange: str,
    symbol: str,
    provider_timestamp_us: int,
    provider_local_timestamp_us: int | None,
    liquidated_position_side: LiquidatedPositionSide,
    price: Decimal,
    quantity: Decimal,
    raw_side: str,
    provider_event_id: str | None,
) -> str:
    return _digest(
        (
            historical_provider.strip().lower(),
            provider_exchange.strip().lower(),
            symbol.strip().upper(),
            str(provider_timestamp_us),
            "" if provider_local_timestamp_us is None else str(provider_local_timestamp_us),
            liquidated_position_side.value,
            decimal_text(price),
            decimal_text(quantity),
            raw_side.strip(),
            "" if provider_event_id is None else provider_event_id.strip(),
        )
    )


def deterministic_historical_event_id(
    *,
    historical_provider: str,
    raw_file_sha256: str,
    raw_row_number: int,
    event_fingerprint_sha256: str,
) -> str:
    return _digest(
        (
            historical_provider.strip().lower(),
            validate_sha256(raw_file_sha256, field="raw_file_sha256"),
            str(integer_value(raw_row_number, field="raw_row_number", minimum=1)),
            validate_sha256(event_fingerprint_sha256, field="event_fingerprint_sha256"),
        )
    )


@dataclass(frozen=True, slots=True)
class HistoricalLiquidationEvent:
    schema_version: int
    source: str
    symbol: str
    liquidated_position_side: LiquidatedPositionSide
    occurred_at_ms: int
    available_at_ms: int
    available_at_semantics: AvailableAtSemantics
    price: Decimal
    quantity: Decimal
    notional_usd: Decimal
    source_event_id: str
    provider_event_id: str | None
    dataset_origin: DatasetOrigin
    historical_provider: str
    provider_exchange: str
    provider_timestamp_us: int
    provider_local_timestamp_us: int | None
    native_channel: str
    semantic_era: str
    import_run_id: str
    raw_file_sha256: str
    raw_row_number: int
    raw_side: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        for field_name in (
            "source",
            "symbol",
            "historical_provider",
            "provider_exchange",
            "native_channel",
            "semantic_era",
            "import_run_id",
            "raw_side",
        ):
            _require_text(str(getattr(self, field_name)), field=field_name)
        integer_value(self.occurred_at_ms, field="occurred_at_ms", minimum=1)
        integer_value(self.available_at_ms, field="available_at_ms", minimum=1)
        integer_value(self.provider_timestamp_us, field="provider_timestamp_us", minimum=1)
        integer_value(self.raw_row_number, field="raw_row_number", minimum=1)
        if self.provider_local_timestamp_us is not None:
            integer_value(
                self.provider_local_timestamp_us,
                field="provider_local_timestamp_us",
                minimum=1,
            )
        price = canonical_decimal(self.price, field="price", positive=True)
        quantity = canonical_decimal(self.quantity, field="quantity", positive=True)
        notional = canonical_decimal(self.notional_usd, field="notional_usd", positive=True)
        if notional != price * quantity:
            raise ValueError("notional_usd must equal price * quantity exactly")
        validate_sha256(self.source_event_id, field="source_event_id")
        validate_sha256(self.raw_file_sha256, field="raw_file_sha256")
        if self.occurred_at_ms != self.provider_timestamp_us // 1000:
            raise ValueError("occurred_at_ms must be derived from provider_timestamp_us")
        if self.available_at_semantics is AvailableAtSemantics.VENDOR_CAPTURE_TIMESTAMP:
            if self.provider_local_timestamp_us is None:
                raise ValueError("vendor capture semantics require provider_local_timestamp_us")
            if self.available_at_ms != self.provider_local_timestamp_us // 1000:
                raise ValueError("available_at_ms must be derived from provider_local_timestamp_us")
        elif self.provider_local_timestamp_us is not None:
            if self.available_at_ms != self.provider_local_timestamp_us // 1000:
                raise ValueError("available_at_ms must preserve provider local timestamp")
        elif self.available_at_ms != self.occurred_at_ms:
            raise ValueError("fallback availability must equal occurred_at_ms")

    @property
    def availability_latency_ms(self) -> int:
        return self.available_at_ms - self.occurred_at_ms

    @property
    def event_fingerprint_sha256(self) -> str:
        return historical_event_fingerprint(
            historical_provider=self.historical_provider,
            provider_exchange=self.provider_exchange,
            symbol=self.symbol,
            provider_timestamp_us=self.provider_timestamp_us,
            provider_local_timestamp_us=self.provider_local_timestamp_us,
            liquidated_position_side=self.liquidated_position_side,
            price=self.price,
            quantity=self.quantity,
            raw_side=self.raw_side,
            provider_event_id=self.provider_event_id,
        )

    def as_json_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["liquidated_position_side"] = self.liquidated_position_side.value
        payload["available_at_semantics"] = self.available_at_semantics.value
        payload["dataset_origin"] = self.dataset_origin.value
        payload["price"] = decimal_text(self.price)
        payload["quantity"] = decimal_text(self.quantity)
        payload["notional_usd"] = decimal_text(self.notional_usd)
        payload["event_fingerprint_sha256"] = self.event_fingerprint_sha256
        return payload


def historical_event_from_json_dict(
    payload: Mapping[str, object],
) -> HistoricalLiquidationEvent:
    try:
        event = HistoricalLiquidationEvent(
            schema_version=integer_value(
                payload["schema_version"], field="schema_version", minimum=1
            ),
            source=str(payload["source"]),
            symbol=str(payload["symbol"]),
            liquidated_position_side=LiquidatedPositionSide(
                str(payload["liquidated_position_side"])
            ),
            occurred_at_ms=integer_value(
                payload["occurred_at_ms"], field="occurred_at_ms", minimum=1
            ),
            available_at_ms=integer_value(
                payload["available_at_ms"], field="available_at_ms", minimum=1
            ),
            available_at_semantics=AvailableAtSemantics(str(payload["available_at_semantics"])),
            price=canonical_decimal(payload["price"], field="price", positive=True),
            quantity=canonical_decimal(payload["quantity"], field="quantity", positive=True),
            notional_usd=canonical_decimal(
                payload["notional_usd"], field="notional_usd", positive=True
            ),
            source_event_id=str(payload["source_event_id"]),
            provider_event_id=(
                None
                if payload.get("provider_event_id") is None
                else str(payload["provider_event_id"])
            ),
            dataset_origin=DatasetOrigin(str(payload["dataset_origin"])),
            historical_provider=str(payload["historical_provider"]),
            provider_exchange=str(payload["provider_exchange"]),
            provider_timestamp_us=integer_value(
                payload["provider_timestamp_us"],
                field="provider_timestamp_us",
                minimum=1,
            ),
            provider_local_timestamp_us=(
                None
                if payload.get("provider_local_timestamp_us") is None
                else integer_value(
                    payload["provider_local_timestamp_us"],
                    field="provider_local_timestamp_us",
                    minimum=1,
                )
            ),
            native_channel=str(payload["native_channel"]),
            semantic_era=str(payload["semantic_era"]),
            import_run_id=str(payload["import_run_id"]),
            raw_file_sha256=str(payload["raw_file_sha256"]),
            raw_row_number=integer_value(
                payload["raw_row_number"], field="raw_row_number", minimum=1
            ),
            raw_side=str(payload["raw_side"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid historical liquidation event") from exc

    expected_fingerprint = payload.get("event_fingerprint_sha256")
    if expected_fingerprint is not None and expected_fingerprint != event.event_fingerprint_sha256:
        raise ValueError("event_fingerprint_sha256 does not match event content")
    return event
