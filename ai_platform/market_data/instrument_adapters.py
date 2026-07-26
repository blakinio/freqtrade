from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any, Protocol, Self
from urllib.parse import urlencode

from ai_platform.market_data.common import (
    SCHEMA_VERSION,
    Exchange,
    MarketType,
    canonical_instrument_id,
    canonical_sha256,
    decimal_value,
    refuse_trading_credentials,
    validate_sha256,
)
from ai_platform.market_data.events import InstrumentSnapshot


ADAPTER_VERSION = "market-data-instrument-adapters-v1"
BINANCE_SPOT_URL = "https://api.binance.com/api/v3/exchangeInfo"
BYBIT_SPOT_URL = "https://api.bybit.com/v5/market/instruments-info?category=spot"
BYBIT_LINEAR_URL = "https://api.bybit.com/v5/market/instruments-info?category=linear&limit=1000"
OKX_SPOT_URL = "https://www.okx.com/api/v5/public/instruments?instType=SPOT"
OKX_SWAP_URL = "https://www.okx.com/api/v5/public/instruments?instType=SWAP"
OKX_FUTURES_URL = "https://www.okx.com/api/v5/public/instruments?instType=FUTURES"

SUPPORTED_ADAPTER_SOURCES = frozenset(
    {
        "binance-spot",
        "bybit-spot",
        "bybit-linear",
        "okx-spot",
        "okx-swap-futures",
    }
)
BLOCKED_ADAPTER_SOURCES = {
    "binance-usdm": "explicit contract value and contract-value unit semantics are unresolved",
}
MAX_BYBIT_LINEAR_PAGES = 10
MAX_INSTRUMENTS_PER_SNAPSHOT = 10_000


class PublicJsonFetcher(Protocol):
    def __call__(self, url: str, /) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True)
class InstrumentCatalogSnapshot:
    schema_version: int
    adapter_version: str
    source_id: str
    captured_at_ms: int
    request_urls: tuple[str, ...]
    raw_payload_sha256s: tuple[str, ...]
    source_snapshot_id: str
    source_snapshot_sha256: str
    instruments: tuple[InstrumentSnapshot, ...]
    snapshot_sha256: str

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        if self.adapter_version != ADAPTER_VERSION:
            raise ValueError("unsupported adapter_version")
        if self.source_id not in SUPPORTED_ADAPTER_SOURCES:
            raise ValueError("unsupported adapter source")
        if self.captured_at_ms <= 0:
            raise ValueError("captured_at_ms must be > 0")
        if not self.request_urls or len(set(self.request_urls)) != len(self.request_urls):
            raise ValueError("request_urls must be non-empty and unique")
        if len(self.raw_payload_sha256s) != len(self.request_urls):
            raise ValueError("raw payload hashes must match request URLs")
        for digest in self.raw_payload_sha256s:
            validate_sha256(digest, field="raw_payload_sha256")
        validate_sha256(self.source_snapshot_sha256, field="source_snapshot_sha256")
        expected_id = f"{self.source_id}:{self.source_snapshot_sha256[:24]}"
        if self.source_snapshot_id != expected_id:
            raise ValueError("source_snapshot_id does not match source snapshot hash")
        if not self.instruments:
            raise ValueError("instrument catalog snapshot must not be empty")
        if len(self.instruments) > MAX_INSTRUMENTS_PER_SNAPSHOT:
            raise ValueError("instrument catalog snapshot exceeds bounded maximum")
        instrument_ids = tuple(item.canonical_instrument_id for item in self.instruments)
        if len(set(instrument_ids)) != len(instrument_ids):
            raise ValueError("instrument catalog contains duplicate canonical IDs")
        if instrument_ids != tuple(sorted(instrument_ids)):
            raise ValueError("instruments must use deterministic canonical ID order")
        for instrument in self.instruments:
            if instrument.source_snapshot_id != self.source_snapshot_id:
                raise ValueError("instrument source_snapshot_id does not match catalog")
            if instrument.source_snapshot_sha256 != self.source_snapshot_sha256:
                raise ValueError("instrument source snapshot hash does not match catalog")
        validate_sha256(self.snapshot_sha256, field="snapshot_sha256")
        if self.snapshot_sha256 != canonical_sha256(self.hash_payload()):
            raise ValueError("snapshot_sha256 does not match catalog snapshot")

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        captured_at_ms: int,
        request_urls: tuple[str, ...],
        raw_payload_sha256s: tuple[str, ...],
        source_snapshot_id: str,
        source_snapshot_sha256: str,
        instruments: tuple[InstrumentSnapshot, ...],
    ) -> Self:
        seed = {
            "schema_version": SCHEMA_VERSION,
            "adapter_version": ADAPTER_VERSION,
            "source_id": source_id,
            "captured_at_ms": captured_at_ms,
            "request_urls": list(request_urls),
            "raw_payload_sha256s": list(raw_payload_sha256s),
            "source_snapshot_id": source_snapshot_id,
            "source_snapshot_sha256": source_snapshot_sha256,
            "instruments": [item.as_json_dict() for item in instruments],
        }
        return cls(
            schema_version=SCHEMA_VERSION,
            adapter_version=ADAPTER_VERSION,
            source_id=source_id,
            captured_at_ms=captured_at_ms,
            request_urls=request_urls,
            raw_payload_sha256s=raw_payload_sha256s,
            source_snapshot_id=source_snapshot_id,
            source_snapshot_sha256=source_snapshot_sha256,
            instruments=instruments,
            snapshot_sha256=canonical_sha256(seed),
        )

    def hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_version": self.adapter_version,
            "source_id": self.source_id,
            "captured_at_ms": self.captured_at_ms,
            "request_urls": list(self.request_urls),
            "raw_payload_sha256s": list(self.raw_payload_sha256s),
            "source_snapshot_id": self.source_snapshot_id,
            "source_snapshot_sha256": self.source_snapshot_sha256,
            "instruments": [item.as_json_dict() for item in self.instruments],
        }

    def as_json_dict(self) -> dict[str, Any]:
        return {**self.hash_payload(), "snapshot_sha256": self.snapshot_sha256}


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _sequence(value: object, *, field: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_ms(value: object, *, field: str) -> int | None:
    if value is None or value in {"", "0", 0}:
        return None
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise ValueError(f"{field} must be an integer timestamp")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer timestamp") from exc
    if parsed <= 0:
        raise ValueError(f"{field} must be > 0")
    return parsed


def _required_ms(value: object, *, field: str) -> int:
    parsed = _optional_ms(value, field=field)
    if parsed is None:
        raise ValueError(f"{field} is required")
    return parsed


def _positive_decimal(value: object, *, field: str) -> Decimal:
    return decimal_value(value, field=field, positive=True)


def _canonical_symbol(base: str, quote: str, settlement: str | None = None) -> str:
    return f"{base}/{quote}" if settlement is None else f"{base}/{quote}:{settlement}"


def _snapshot_identity(
    source_id: str,
    payloads: Sequence[Mapping[str, object]],
) -> tuple[tuple[str, ...], str, str]:
    hashes = tuple(canonical_sha256(payload) for payload in payloads)
    aggregate = canonical_sha256(
        {
            "adapter_version": ADAPTER_VERSION,
            "source_id": source_id,
            "raw_payload_sha256s": list(hashes),
        }
    )
    return hashes, f"{source_id}:{aggregate[:24]}", aggregate


def _build_snapshot(
    *,
    source_id: str,
    captured_at_ms: int,
    request_urls: tuple[str, ...],
    payloads: tuple[Mapping[str, object], ...],
    instruments: Sequence[InstrumentSnapshot],
) -> InstrumentCatalogSnapshot:
    if captured_at_ms <= 0:
        raise ValueError("captured_at_ms must be > 0")
    if len(payloads) != len(request_urls):
        raise ValueError("payloads must match request URLs")
    raw_hashes, snapshot_id, snapshot_hash = _snapshot_identity(source_id, payloads)
    rebound = tuple(
        replace(
            instrument,
            source_snapshot_id=snapshot_id,
            source_snapshot_sha256=snapshot_hash,
        )
        for instrument in instruments
    )
    ordered = tuple(sorted(rebound, key=lambda item: item.canonical_instrument_id))
    return InstrumentCatalogSnapshot.create(
        source_id=source_id,
        captured_at_ms=captured_at_ms,
        request_urls=request_urls,
        raw_payload_sha256s=raw_hashes,
        source_snapshot_id=snapshot_id,
        source_snapshot_sha256=snapshot_hash,
        instruments=ordered,
    )


def _filter_value(item: Mapping[str, object], filter_type: str, field: str) -> object:
    filters = _sequence(item.get("filters"), field="filters")
    matches = [
        _mapping(candidate, field="filter")
        for candidate in filters
        if isinstance(candidate, dict) and candidate.get("filterType") == filter_type
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {filter_type} filter")
    if field not in matches[0]:
        raise ValueError(f"{filter_type}.{field} is required")
    return matches[0][field]


def _unbound_instrument(
    *,
    exchange: Exchange,
    market_type: MarketType,
    native_id: str,
    native_symbol: str,
    canonical_symbol: str,
    base_asset: str,
    quote_asset: str,
    settlement_asset: str | None,
    contract_value: Decimal | None,
    contract_value_unit: str | None,
    tick_size: Decimal,
    quantity_step: Decimal,
    active: bool,
    listed_at_ms: int | None,
    expires_at_ms: int | None,
) -> InstrumentSnapshot:
    return InstrumentSnapshot(
        schema_version=SCHEMA_VERSION,
        exchange=exchange,
        market_type=market_type,
        native_instrument_id=native_id,
        canonical_instrument_id=canonical_instrument_id(exchange, market_type, native_id),
        native_symbol=native_symbol,
        canonical_symbol=canonical_symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        settlement_asset=settlement_asset,
        contract_type=market_type,
        contract_value=contract_value,
        contract_value_unit=contract_value_unit,
        tick_size=tick_size,
        quantity_step=quantity_step,
        active=active,
        listed_at_ms=listed_at_ms,
        expires_at_ms=expires_at_ms,
        source_snapshot_id="unbound",
        source_snapshot_sha256="0" * 64,
    )


def parse_binance_spot_catalog(
    payload: Mapping[str, object],
    *,
    captured_at_ms: int,
    request_url: str = BINANCE_SPOT_URL,
) -> InstrumentCatalogSnapshot:
    instruments: list[InstrumentSnapshot] = []
    for raw in _sequence(payload.get("symbols"), field="symbols"):
        item = _mapping(raw, field="symbol")
        native = _text(item.get("symbol"), field="symbol")
        base = _text(item.get("baseAsset"), field="baseAsset")
        quote = _text(item.get("quoteAsset"), field="quoteAsset")
        instruments.append(
            _unbound_instrument(
                exchange=Exchange.BINANCE,
                market_type=MarketType.SPOT,
                native_id=native,
                native_symbol=native,
                canonical_symbol=_canonical_symbol(base, quote),
                base_asset=base,
                quote_asset=quote,
                settlement_asset=None,
                contract_value=None,
                contract_value_unit=None,
                tick_size=_positive_decimal(
                    _filter_value(item, "PRICE_FILTER", "tickSize"),
                    field="PRICE_FILTER.tickSize",
                ),
                quantity_step=_positive_decimal(
                    _filter_value(item, "LOT_SIZE", "stepSize"),
                    field="LOT_SIZE.stepSize",
                ),
                active=item.get("status") == "TRADING",
                listed_at_ms=None,
                expires_at_ms=None,
            )
        )
    return _build_snapshot(
        source_id="binance-spot",
        captured_at_ms=captured_at_ms,
        request_urls=(request_url,),
        payloads=(payload,),
        instruments=instruments,
    )


def _bybit_result(
    payload: Mapping[str, object],
    *,
    expected_category: str,
) -> tuple[list[object], str]:
    if payload.get("retCode") != 0:
        raise ValueError("Bybit response retCode must be 0")
    result = _mapping(payload.get("result"), field="result")
    if result.get("category") != expected_category:
        raise ValueError("Bybit response category does not match adapter")
    cursor = result.get("nextPageCursor", "")
    if not isinstance(cursor, str):
        raise ValueError("nextPageCursor must be a string")
    return _sequence(result.get("list"), field="result.list"), cursor


def parse_bybit_spot_catalog(
    payload: Mapping[str, object],
    *,
    captured_at_ms: int,
    request_url: str = BYBIT_SPOT_URL,
) -> InstrumentCatalogSnapshot:
    raw_items, cursor = _bybit_result(payload, expected_category="spot")
    if cursor:
        raise ValueError("Bybit Spot catalog must not require pagination")
    instruments: list[InstrumentSnapshot] = []
    for raw in raw_items:
        item = _mapping(raw, field="instrument")
        native = _text(item.get("symbol"), field="symbol")
        base = _text(item.get("baseCoin"), field="baseCoin")
        quote = _text(item.get("quoteCoin"), field="quoteCoin")
        price_filter = _mapping(item.get("priceFilter"), field="priceFilter")
        lot_filter = _mapping(item.get("lotSizeFilter"), field="lotSizeFilter")
        instruments.append(
            _unbound_instrument(
                exchange=Exchange.BYBIT,
                market_type=MarketType.SPOT,
                native_id=native,
                native_symbol=native,
                canonical_symbol=_canonical_symbol(base, quote),
                base_asset=base,
                quote_asset=quote,
                settlement_asset=None,
                contract_value=None,
                contract_value_unit=None,
                tick_size=_positive_decimal(price_filter.get("tickSize"), field="tickSize"),
                quantity_step=_positive_decimal(
                    lot_filter.get("basePrecision"),
                    field="basePrecision",
                ),
                active=item.get("status") == "Trading",
                listed_at_ms=None,
                expires_at_ms=None,
            )
        )
    return _build_snapshot(
        source_id="bybit-spot",
        captured_at_ms=captured_at_ms,
        request_urls=(request_url,),
        payloads=(payload,),
        instruments=instruments,
    )


def parse_bybit_linear_catalog(
    payloads: tuple[Mapping[str, object], ...],
    *,
    captured_at_ms: int,
    request_urls: tuple[str, ...],
) -> InstrumentCatalogSnapshot:
    instruments: list[InstrumentSnapshot] = []
    for payload in payloads:
        raw_items, _ = _bybit_result(payload, expected_category="linear")
        for raw in raw_items:
            item = _mapping(raw, field="instrument")
            contract_type = _text(item.get("contractType"), field="contractType")
            if contract_type == "LinearPerpetual":
                market_type = MarketType.PERPETUAL
                expires_at_ms = None
            elif contract_type == "LinearFutures":
                market_type = MarketType.DATED_FUTURE
                expires_at_ms = _required_ms(item.get("deliveryTime"), field="deliveryTime")
            else:
                raise ValueError(f"unsupported Bybit Linear contractType: {contract_type}")
            native = _text(item.get("symbol"), field="symbol")
            base = _text(item.get("baseCoin"), field="baseCoin")
            quote = _text(item.get("quoteCoin"), field="quoteCoin")
            settlement = _text(item.get("settleCoin"), field="settleCoin")
            price_filter = _mapping(item.get("priceFilter"), field="priceFilter")
            lot_filter = _mapping(item.get("lotSizeFilter"), field="lotSizeFilter")
            instruments.append(
                _unbound_instrument(
                    exchange=Exchange.BYBIT,
                    market_type=market_type,
                    native_id=native,
                    native_symbol=native,
                    canonical_symbol=_canonical_symbol(base, quote, settlement),
                    base_asset=base,
                    quote_asset=quote,
                    settlement_asset=settlement,
                    contract_value=Decimal("1"),
                    contract_value_unit="base_asset",
                    tick_size=_positive_decimal(
                        price_filter.get("tickSize"),
                        field="tickSize",
                    ),
                    quantity_step=_positive_decimal(
                        lot_filter.get("qtyStep"),
                        field="qtyStep",
                    ),
                    active=item.get("status") == "Trading",
                    listed_at_ms=_optional_ms(item.get("launchTime"), field="launchTime"),
                    expires_at_ms=expires_at_ms,
                )
            )
    return _build_snapshot(
        source_id="bybit-linear",
        captured_at_ms=captured_at_ms,
        request_urls=request_urls,
        payloads=payloads,
        instruments=instruments,
    )


def _okx_data(
    payload: Mapping[str, object],
    *,
    expected_type: str,
) -> list[object]:
    if payload.get("code") != "0":
        raise ValueError("OKX response code must be 0")
    data = _sequence(payload.get("data"), field="data")
    for raw in data:
        item = _mapping(raw, field="instrument")
        if item.get("instType") != expected_type:
            raise ValueError("OKX instrument type does not match adapter request")
    return data


def parse_okx_spot_catalog(
    payload: Mapping[str, object],
    *,
    captured_at_ms: int,
    request_url: str = OKX_SPOT_URL,
) -> InstrumentCatalogSnapshot:
    instruments: list[InstrumentSnapshot] = []
    for raw in _okx_data(payload, expected_type="SPOT"):
        item = _mapping(raw, field="instrument")
        if _optional_ms(item.get("expTime"), field="expTime") is not None:
            raise ValueError("OKX Spot instrument must not define expiry")
        native = _text(item.get("instId"), field="instId")
        base = _text(item.get("baseCcy"), field="baseCcy")
        quote = _text(item.get("quoteCcy"), field="quoteCcy")
        instruments.append(
            _unbound_instrument(
                exchange=Exchange.OKX,
                market_type=MarketType.SPOT,
                native_id=native,
                native_symbol=native,
                canonical_symbol=_canonical_symbol(base, quote),
                base_asset=base,
                quote_asset=quote,
                settlement_asset=None,
                contract_value=None,
                contract_value_unit=None,
                tick_size=_positive_decimal(item.get("tickSz"), field="tickSz"),
                quantity_step=_positive_decimal(item.get("lotSz"), field="lotSz"),
                active=item.get("state") == "live",
                listed_at_ms=_optional_ms(item.get("listTime"), field="listTime"),
                expires_at_ms=None,
            )
        )
    return _build_snapshot(
        source_id="okx-spot",
        captured_at_ms=captured_at_ms,
        request_urls=(request_url,),
        payloads=(payload,),
        instruments=instruments,
    )


def _okx_pair(item: Mapping[str, object]) -> tuple[str, str]:
    text = _text(item.get("uly") or item.get("instFamily"), field="uly_or_instFamily")
    parts = text.split("-")
    if len(parts) != 2 or not all(parts):
        raise ValueError("OKX underlying must be BASE-QUOTE")
    return parts[0], parts[1]


def parse_okx_derivatives_catalog(
    payloads: tuple[Mapping[str, object], Mapping[str, object]],
    *,
    captured_at_ms: int,
    request_urls: tuple[str, str] = (OKX_SWAP_URL, OKX_FUTURES_URL),
) -> InstrumentCatalogSnapshot:
    instruments: list[InstrumentSnapshot] = []
    for payload, expected_type in zip(payloads, ("SWAP", "FUTURES"), strict=True):
        for raw in _okx_data(payload, expected_type=expected_type):
            item = _mapping(raw, field="instrument")
            multiplier = item.get("ctMult")
            if multiplier is not None and multiplier != "":
                parsed_multiplier = decimal_value(multiplier, field="ctMult", positive=True)
                if parsed_multiplier != Decimal("1"):
                    raise ValueError("non-unit OKX ctMult is not representable by foundation v1")
            market_type = (
                MarketType.PERPETUAL if expected_type == "SWAP" else MarketType.DATED_FUTURE
            )
            expires_at_ms = (
                None
                if market_type is MarketType.PERPETUAL
                else _required_ms(item.get("expTime"), field="expTime")
            )
            native = _text(item.get("instId"), field="instId")
            base, quote = _okx_pair(item)
            settlement = _text(item.get("settleCcy"), field="settleCcy")
            instruments.append(
                _unbound_instrument(
                    exchange=Exchange.OKX,
                    market_type=market_type,
                    native_id=native,
                    native_symbol=native,
                    canonical_symbol=_canonical_symbol(base, quote, settlement),
                    base_asset=base,
                    quote_asset=quote,
                    settlement_asset=settlement,
                    contract_value=_positive_decimal(item.get("ctVal"), field="ctVal"),
                    contract_value_unit=_text(item.get("ctValCcy"), field="ctValCcy"),
                    tick_size=_positive_decimal(item.get("tickSz"), field="tickSz"),
                    quantity_step=_positive_decimal(item.get("lotSz"), field="lotSz"),
                    active=item.get("state") == "live",
                    listed_at_ms=_optional_ms(item.get("listTime"), field="listTime"),
                    expires_at_ms=expires_at_ms,
                )
            )
    return _build_snapshot(
        source_id="okx-swap-futures",
        captured_at_ms=captured_at_ms,
        request_urls=request_urls,
        payloads=payloads,
        instruments=instruments,
    )


def _collect_bybit_linear(
    *,
    fetch_json: PublicJsonFetcher,
    captured_at_ms: int,
) -> InstrumentCatalogSnapshot:
    payloads: list[Mapping[str, object]] = []
    urls: list[str] = []
    cursor = ""
    seen_cursors: set[str] = set()
    for _ in range(MAX_BYBIT_LINEAR_PAGES):
        url = BYBIT_LINEAR_URL
        if cursor:
            url += "&" + urlencode({"cursor": cursor})
        payload = fetch_json(url)
        payloads.append(payload)
        urls.append(url)
        _, next_cursor = _bybit_result(payload, expected_category="linear")
        if not next_cursor:
            return parse_bybit_linear_catalog(
                tuple(payloads),
                captured_at_ms=captured_at_ms,
                request_urls=tuple(urls),
            )
        if next_cursor in seen_cursors:
            raise RuntimeError("Bybit Linear pagination cursor repeated")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    raise RuntimeError("Bybit Linear pagination exceeded bounded page limit")


def collect_instrument_catalog(
    *,
    source_id: str,
    fetch_json: PublicJsonFetcher,
    captured_at_ms: int,
    environment: Mapping[str, str] | None = None,
) -> InstrumentCatalogSnapshot:
    refuse_trading_credentials(environment or {})
    if source_id in BLOCKED_ADAPTER_SOURCES:
        reason = BLOCKED_ADAPTER_SOURCES[source_id]
        raise RuntimeError(f"{source_id} is blocked: {reason}")
    if source_id == "binance-spot":
        return parse_binance_spot_catalog(
            fetch_json(BINANCE_SPOT_URL),
            captured_at_ms=captured_at_ms,
        )
    if source_id == "bybit-spot":
        return parse_bybit_spot_catalog(
            fetch_json(BYBIT_SPOT_URL),
            captured_at_ms=captured_at_ms,
        )
    if source_id == "bybit-linear":
        return _collect_bybit_linear(
            fetch_json=fetch_json,
            captured_at_ms=captured_at_ms,
        )
    if source_id == "okx-spot":
        return parse_okx_spot_catalog(
            fetch_json(OKX_SPOT_URL),
            captured_at_ms=captured_at_ms,
        )
    if source_id == "okx-swap-futures":
        return parse_okx_derivatives_catalog(
            (fetch_json(OKX_SWAP_URL), fetch_json(OKX_FUTURES_URL)),
            captured_at_ms=captured_at_ms,
        )
    raise ValueError(f"unsupported instrument adapter source: {source_id}")
