# ruff: noqa
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from typing import Any, Self

SCHEMA_VERSION = 1
_HEX_DIGITS = frozenset("0123456789abcdef")


class Exchange(StrEnum):
    BINANCE = "binance"
    BYBIT = "bybit"
    OKX = "okx"


class MarketType(StrEnum):
    SPOT = "spot"
    PERPETUAL = "perpetual"
    DATED_FUTURE = "dated_future"


class EventType(StrEnum):
    TRADE = "trade"
    ORDER_BOOK_SNAPSHOT = "order_book_snapshot"
    ORDER_BOOK_DELTA = "order_book_delta"
    TICKER = "ticker"
    MARK_PRICE = "mark_price"
    FUNDING_RATE = "funding_rate"
    OPEN_INTEREST = "open_interest"
    LIQUIDATION = "liquidation"
    INSTRUMENT_STATUS = "instrument_status"
    SOURCE_MARKER = "source_marker"


class ChannelFamily(StrEnum):
    INSTRUMENT_CATALOG = "instrument_catalog"
    TRADES = "trades"
    ORDER_BOOK_SNAPSHOT = "order_book_snapshot"
    ORDER_BOOK_DELTA = "order_book_delta"
    TICKER_24H = "ticker_24h"
    MARK_PRICE = "mark_price"
    FUNDING_RATE = "funding_rate"
    OPEN_INTEREST = "open_interest"
    LIQUIDATIONS = "liquidations"


class AvailabilityTimestampKind(StrEnum):
    LIVE_COLLECTOR_RECEIVE = "live_collector_receive"
    PROVIDER_CAPTURE = "provider_capture"


class CompressionPolicy(StrEnum):
    NONE = "none"
    GZIP = "gzip"
    ZSTD = "zstd"


class GapReason(StrEnum):
    SEQUENCE_GAP = "sequence_gap"
    DISCONNECT = "disconnect"
    RECONNECT_WITHOUT_RESYNC = "reconnect_without_resync"
    PROVIDER_MISSING_INTERVAL = "provider_missing_interval"


class OutputImmutabilityState(StrEnum):
    OPEN = "open"
    CLOSED_IMMUTABLE = "closed_immutable"
    QUARANTINED = "quarantined"


TRADING_CREDENTIAL_ENV_NAMES = frozenset(
    {
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "BINANCE_SECRET_KEY",
        "BYBIT_API_KEY",
        "BYBIT_API_SECRET",
        "OKX_API_KEY",
        "OKX_API_SECRET",
        "OKX_SECRET_KEY",
        "OKX_PASSPHRASE",
        "EXCHANGE_API_KEY",
        "EXCHANGE_API_SECRET",
        "FREQTRADE__EXCHANGE__KEY",
        "FREQTRADE__EXCHANGE__SECRET",
    }
)


def _require_text(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must be non-empty")
    return normalized


def _require_int(value: int, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return value


def decimal_value(value: object, *, field: str, positive: bool = False) -> Decimal:
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


def validate_sha256(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in _HEX_DIGITS for char in normalized):
        raise ValueError(f"{field} must be a lowercase SHA-256 hex digest")
    return normalized


def validate_commit(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 40 or any(char not in _HEX_DIGITS for char in normalized):
        raise ValueError(f"{field} must be a 40-character lowercase Git commit")
    return normalized


def _json_compatible(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Decimal):
        return decimal_text(value)
    if isinstance(value, FrozenJsonObject):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_compatible(item) for item in value]
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise TypeError(f"value is not JSON-compatible: {type(value).__name__}")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        _json_compatible(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def raw_payload_sha256(value: object) -> str:
    if isinstance(value, str):
        return sha256(value.encode("utf-8")).hexdigest()
    return canonical_sha256(value)


def canonical_instrument_id(
    exchange: Exchange,
    market_type: MarketType,
    native_instrument_id: str,
) -> str:
    native_id = _require_text(native_instrument_id, field="native_instrument_id")
    if ":" in native_id:
        raise ValueError("native_instrument_id must not contain ':'")
    return f"{exchange.value}:{market_type.value}:{native_id}"


def refuse_trading_credentials(environment: Mapping[str, str]) -> None:
    present = sorted(
        name for name in TRADING_CREDENTIAL_ENV_NAMES if environment.get(name, "").strip()
    )
    if present:
        raise RuntimeError(
            "market-data capture refuses trading credential environment variables: "
            + ", ".join(present)
        )


@dataclass(frozen=True, slots=True)
class FrozenJsonObject:
    canonical_json: str

    def __post_init__(self) -> None:
        try:
            value = json.loads(self.canonical_json)
        except json.JSONDecodeError as exc:
            raise ValueError("canonical_json must contain valid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("canonical_json must contain a JSON object")
        if self.canonical_json != canonical_json_bytes(value).decode("utf-8"):
            raise ValueError("canonical_json must use canonical ordering and separators")

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> Self:
        return cls(canonical_json_bytes(value).decode("utf-8"))

    def to_dict(self) -> dict[str, Any]:
        value = json.loads(self.canonical_json)
        if not isinstance(value, dict):
            raise AssertionError("validated FrozenJsonObject decoded to a non-object")
        return value
