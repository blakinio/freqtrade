from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ai_platform.research.liquidations.contracts import (
    LiquidatedPositionSide,
    LiquidationEvent,
    deterministic_event_id,
    integer_value,
    positive_decimal,
)


OKX_USDT_SWAP_SOURCE = "okx-usdt-swap"


def _require_mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be an object")
    return value


def _require_sequence(value: object, *, field: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a list")
    return value


def _normalized_symbol_set(symbols: Sequence[str] | None) -> set[str] | None:
    if symbols is None:
        return None
    return {symbol.strip().upper() for symbol in symbols if symbol.strip()}


def canonical_symbol_from_inst_id(inst_id: str) -> str:
    parts = inst_id.strip().upper().split("-")
    if len(parts) != 3 or parts[1] != "USDT" or parts[2] != "SWAP":
        raise ValueError(f"unsupported OKX USDT swap instrument: {inst_id}")
    base = parts[0]
    if not base or not base.isalnum():
        raise ValueError(f"invalid OKX base currency in instrument: {inst_id}")
    return f"{base}USDT"


@dataclass(frozen=True, slots=True)
class OkxInstrumentContract:
    inst_id: str
    canonical_symbol: str
    contract_value: Decimal
    contract_multiplier: Decimal
    contract_value_currency: str
    settle_currency: str
    contract_type: str
    state: str

    def __post_init__(self) -> None:
        expected_symbol = canonical_symbol_from_inst_id(self.inst_id)
        if self.canonical_symbol != expected_symbol:
            raise ValueError("canonical_symbol does not match inst_id")
        positive_decimal(self.contract_value, field="contract_value")
        positive_decimal(self.contract_multiplier, field="contract_multiplier")
        if self.contract_type != "linear":
            raise ValueError("only linear OKX swaps are supported")
        if self.settle_currency != "USDT":
            raise ValueError("only USDT-settled OKX swaps are supported")
        expected_base = self.canonical_symbol.removesuffix("USDT")
        if self.contract_value_currency != expected_base:
            raise ValueError("contract value currency must match the base asset")
        if self.contract_multiplier != Decimal(1):
            raise ValueError("OKX contract multiplier must equal 1 for v1 normalization")
        if self.state != "live":
            raise ValueError("OKX instrument state must be live")

    def base_quantity(self, contract_count: Decimal) -> Decimal:
        return positive_decimal(contract_count, field="contract_count") * self.contract_value

    def as_json_dict(self) -> dict[str, str]:
        return {
            "inst_id": self.inst_id,
            "canonical_symbol": self.canonical_symbol,
            "contract_value": str(self.contract_value),
            "contract_multiplier": str(self.contract_multiplier),
            "contract_value_currency": self.contract_value_currency,
            "settle_currency": self.settle_currency,
            "contract_type": self.contract_type,
            "state": self.state,
        }


def _instrument_from_row(
    row: Mapping[str, object],
    *,
    index: int,
) -> OkxInstrumentContract | None:
    if str(row.get("instType", "")).upper() != "SWAP":
        return None
    inst_id = str(row.get("instId", "")).strip().upper()
    try:
        canonical_symbol = canonical_symbol_from_inst_id(inst_id)
    except ValueError:
        return None
    return OkxInstrumentContract(
        inst_id=inst_id,
        canonical_symbol=canonical_symbol,
        contract_value=positive_decimal(row.get("ctVal"), field=f"data[{index}].ctVal"),
        contract_multiplier=positive_decimal(
            row.get("ctMult"),
            field=f"data[{index}].ctMult",
        ),
        contract_value_currency=str(row.get("ctValCcy", "")).strip().upper(),
        settle_currency=str(row.get("settleCcy", "")).strip().upper(),
        contract_type=str(row.get("ctType", "")).strip().lower(),
        state=str(row.get("state", "")).strip().lower(),
    )


def _store_instrument(
    instruments: dict[str, OkxInstrumentContract],
    contract: OkxInstrumentContract,
) -> None:
    previous = instruments.get(contract.inst_id)
    if previous is not None and previous != contract:
        raise ValueError(f"conflicting OKX instrument metadata for {contract.inst_id}")
    instruments[contract.inst_id] = contract


def _require_requested_instruments(
    instruments: Mapping[str, OkxInstrumentContract],
    requested: set[str] | None,
) -> None:
    if requested is None:
        return
    observed = {item.canonical_symbol for item in instruments.values()}
    missing = sorted(requested - observed)
    if missing:
        raise ValueError(f"missing OKX instrument metadata for: {', '.join(missing)}")


def parse_okx_instruments_response(
    payload: Mapping[str, object],
    *,
    requested_symbols: Sequence[str] | None = None,
) -> dict[str, OkxInstrumentContract]:
    if str(payload.get("code", "")) != "0":
        raise ValueError("OKX instruments response code must be 0")
    requested = _normalized_symbol_set(requested_symbols)
    instruments: dict[str, OkxInstrumentContract] = {}
    rows = _require_sequence(payload.get("data"), field="data")
    for index, raw_row in enumerate(rows):
        row = _require_mapping(raw_row, field=f"data[{index}]")
        contract = _instrument_from_row(row, index=index)
        if contract is None:
            continue
        if requested is not None and contract.canonical_symbol not in requested:
            continue
        _store_instrument(instruments, contract)
    _require_requested_instruments(instruments, requested)
    return instruments


def _normalize_position_side(
    *,
    position_side: str,
    order_side: str,
) -> LiquidatedPositionSide:
    normalized_position = position_side.strip().lower()
    normalized_order = order_side.strip().lower()
    if normalized_position == "long":
        return LiquidatedPositionSide.LONG
    if normalized_position == "short":
        return LiquidatedPositionSide.SHORT
    if normalized_position == "net":
        if normalized_order == "sell":
            return LiquidatedPositionSide.LONG
        if normalized_order == "buy":
            return LiquidatedPositionSide.SHORT
    raise ValueError(
        f"unsupported OKX liquidation side combination: side={order_side}, posSide={position_side}"
    )


def _event_from_detail(
    detail: Mapping[str, object],
    *,
    row_index: int,
    detail_index: int,
    contract: OkxInstrumentContract,
    received_at_ms: int,
) -> LiquidationEvent:
    field_prefix = f"data[{row_index}].details[{detail_index}]"
    occurred_at_ms = integer_value(detail.get("ts"), field=f"{field_prefix}.ts")
    order_side = str(detail.get("side", "")).strip().lower()
    position_side = str(detail.get("posSide", "")).strip().lower()
    raw_side = f"{order_side}:{position_side}"
    price = positive_decimal(detail.get("bkPx"), field=f"{field_prefix}.bkPx")
    contract_count = positive_decimal(detail.get("sz"), field=f"{field_prefix}.sz")
    quantity = contract.base_quantity(contract_count)
    notional = quantity * price
    discriminator = ":".join(
        (
            contract.inst_id,
            str(row_index),
            str(detail_index),
            str(detail.get("bkLoss", "")),
            str(detail.get("ccy", "")),
        )
    )
    event_id = deterministic_event_id(
        source=OKX_USDT_SWAP_SOURCE,
        symbol=contract.canonical_symbol,
        occurred_at_ms=occurred_at_ms,
        raw_side=raw_side,
        price=price,
        quantity=quantity,
        source_discriminator=discriminator,
    )
    return LiquidationEvent(
        schema_version=1,
        source=OKX_USDT_SWAP_SOURCE,
        source_event_id=event_id,
        symbol=contract.canonical_symbol,
        liquidated_position_side=_normalize_position_side(
            position_side=position_side,
            order_side=order_side,
        ),
        occurred_at_ms=occurred_at_ms,
        received_at_ms=received_at_ms,
        price=Decimal(price),
        quantity=Decimal(quantity),
        notional_usd=Decimal(notional),
        raw_side=raw_side,
    )


def _events_from_row(
    row: Mapping[str, object],
    *,
    row_index: int,
    received_at_ms: int,
    instruments: Mapping[str, OkxInstrumentContract],
    allowed: set[str] | None,
) -> tuple[LiquidationEvent, ...]:
    if str(row.get("instType", "")).upper() != "SWAP":
        raise ValueError(f"data[{row_index}].instType must be SWAP")
    inst_id = str(row.get("instId", "")).strip().upper()
    try:
        canonical_symbol = canonical_symbol_from_inst_id(inst_id)
    except ValueError:
        return ()
    if allowed is not None and canonical_symbol not in allowed:
        return ()
    contract = instruments.get(inst_id)
    if contract is None:
        raise ValueError(f"missing OKX instrument metadata for {inst_id}")
    details = _require_sequence(row.get("details"), field=f"data[{row_index}].details")
    return tuple(
        _event_from_detail(
            _require_mapping(detail, field=f"data[{row_index}].details[{detail_index}]"),
            row_index=row_index,
            detail_index=detail_index,
            contract=contract,
            received_at_ms=received_at_ms,
        )
        for detail_index, detail in enumerate(details)
    )


def parse_okx_liquidation_orders(
    message: Mapping[str, object],
    *,
    received_at_ms: int,
    instruments: Mapping[str, OkxInstrumentContract],
    allowed_symbols: Sequence[str] | None = None,
) -> tuple[LiquidationEvent, ...]:
    if received_at_ms <= 0:
        raise ValueError("received_at_ms must be > 0")
    arg = _require_mapping(message.get("arg"), field="arg")
    if str(arg.get("channel", "")) != "liquidation-orders":
        raise ValueError("message is not an OKX liquidation-orders event")
    if str(arg.get("instType", "")).upper() != "SWAP":
        raise ValueError("OKX liquidation-orders instType must be SWAP")

    allowed = _normalized_symbol_set(allowed_symbols)
    rows = _require_sequence(message.get("data"), field="data")
    events: list[LiquidationEvent] = []
    for row_index, raw_row in enumerate(rows):
        row = _require_mapping(raw_row, field=f"data[{row_index}]")
        events.extend(
            _events_from_row(
                row,
                row_index=row_index,
                received_at_ms=received_at_ms,
                instruments=instruments,
                allowed=allowed,
            )
        )
    return tuple(events)
