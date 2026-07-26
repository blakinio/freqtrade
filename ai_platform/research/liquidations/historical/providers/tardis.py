from __future__ import annotations

import csv
import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from ai_platform.research.liquidations.contracts import LiquidatedPositionSide
from ai_platform.research.liquidations.historical.contracts import (
    AvailableAtSemantics,
    HistoricalLiquidationEvent,
    canonical_decimal,
    deterministic_historical_event_id,
    historical_event_fingerprint,
    integer_value,
)
from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.research.liquidations.historical.providers.base import (
    HistoricalProviderAdapter,
    ProviderParseContext,
    ProviderParseResult,
    ProviderRowRejection,
)


EXPECTED_HEADER = (
    "exchange",
    "symbol",
    "timestamp",
    "local_timestamp",
    "id",
    "side",
    "price",
    "amount",
)


@dataclass(frozen=True, slots=True)
class TardisExchangeSpec:
    source: str
    native_channel: str


EXCHANGE_SPECS = {
    "bybit": TardisExchangeSpec(source="bybit-linear", native_channel="allLiquidation"),
    "binance-futures": TardisExchangeSpec(source="binance-usdm", native_channel="forceOrder"),
}


class TardisLiquidationsAdapter(HistoricalProviderAdapter):
    provider_id = "tardis"

    def parse_file(self, path: Path, *, context: ProviderParseContext) -> ProviderParseResult:
        self._validate_file(path, context=context)
        events: list[HistoricalLiquidationEvent] = []
        rejections: list[ProviderRowRejection] = []

        with self._open_text(path, context=context) as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != EXPECTED_HEADER:
                return ProviderParseResult(
                    events=(),
                    rejections=(
                        ProviderRowRejection(
                            row_number=1,
                            reason="invalid_header",
                            detail="expected canonical Tardis liquidations CSV header",
                        ),
                    ),
                )
            for row_number, row in enumerate(reader, start=2):
                try:
                    events.append(self._parse_row(row, row_number=row_number, context=context))
                except (KeyError, LookupError, TypeError, ValueError) as exc:
                    rejections.append(
                        ProviderRowRejection(
                            row_number=row_number,
                            reason="invalid_row",
                            detail=str(exc),
                        )
                    )

        return ProviderParseResult(events=tuple(events), rejections=tuple(rejections))

    def _validate_file(self, path: Path, *, context: ProviderParseContext) -> None:
        descriptor = context.raw_file
        if descriptor.provider_id != self.provider_id:
            raise ValueError("raw file descriptor provider must be tardis")
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size != descriptor.size_bytes:
            raise ValueError("raw file size does not match manifest")
        if sha256_file(path) != descriptor.sha256:
            raise ValueError("raw file SHA-256 does not match manifest")
        if descriptor.provider_exchange not in EXCHANGE_SPECS:
            raise ValueError("unsupported Tardis exchange")

    def _open_text(self, path: Path, *, context: ProviderParseContext) -> TextIO:
        encoding = context.raw_file.content_encoding.lower()
        if encoding == "gzip":
            return gzip.open(path, mode="rt", encoding="utf-8", newline="")
        if encoding in {"identity", "plain", "none"}:
            return path.open(mode="rt", encoding="utf-8", newline="")
        raise ValueError("unsupported content encoding")

    def _parse_row(
        self,
        row: dict[str | None, str | list[str] | None],
        *,
        row_number: int,
        context: ProviderParseContext,
    ) -> HistoricalLiquidationEvent:
        if None in row or any(value is None or isinstance(value, list) for value in row.values()):
            raise ValueError("row shape does not match canonical header")
        typed_row = {str(key): str(value) for key, value in row.items()}
        descriptor = context.raw_file
        exchange = typed_row["exchange"].strip().lower()
        if exchange != descriptor.provider_exchange:
            raise ValueError("row exchange does not match manifest")
        symbol = typed_row["symbol"].strip().upper()
        if symbol != descriptor.symbol.upper():
            raise ValueError("row symbol does not match manifest")

        timestamp_us = integer_value(typed_row["timestamp"], field="timestamp", minimum=1)
        local_timestamp_us = integer_value(
            typed_row["local_timestamp"], field="local_timestamp", minimum=1
        )
        raw_side = typed_row["side"].strip().lower()
        side = self._liquidated_position_side(raw_side)
        price = canonical_decimal(typed_row["price"], field="price", positive=True)
        quantity = canonical_decimal(typed_row["amount"], field="amount", positive=True)
        provider_event_id = typed_row["id"].strip() or None
        spec = EXCHANGE_SPECS[exchange]
        occurred_at_ms = timestamp_us // 1000
        era = context.semantic_eras.resolve(
            provider_id=self.provider_id,
            source=spec.source,
            timestamp_ms=occurred_at_ms,
        )
        fingerprint = historical_event_fingerprint(
            historical_provider=self.provider_id,
            provider_exchange=exchange,
            symbol=symbol,
            provider_timestamp_us=timestamp_us,
            provider_local_timestamp_us=local_timestamp_us,
            liquidated_position_side=side,
            price=price,
            quantity=quantity,
            raw_side=raw_side,
            provider_event_id=provider_event_id,
        )
        source_event_id = deterministic_historical_event_id(
            historical_provider=self.provider_id,
            raw_file_sha256=descriptor.sha256,
            raw_row_number=row_number,
            event_fingerprint_sha256=fingerprint,
        )
        return HistoricalLiquidationEvent(
            schema_version=1,
            source=spec.source,
            symbol=symbol,
            liquidated_position_side=side,
            occurred_at_ms=occurred_at_ms,
            available_at_ms=local_timestamp_us // 1000,
            available_at_semantics=AvailableAtSemantics.VENDOR_CAPTURE_TIMESTAMP,
            price=price,
            quantity=quantity,
            notional_usd=price * quantity,
            source_event_id=source_event_id,
            provider_event_id=provider_event_id,
            dataset_origin=context.dataset_origin,
            historical_provider=self.provider_id,
            provider_exchange=exchange,
            provider_timestamp_us=timestamp_us,
            provider_local_timestamp_us=local_timestamp_us,
            native_channel=spec.native_channel,
            semantic_era=era.era_id,
            import_run_id=context.import_run_id,
            raw_file_sha256=descriptor.sha256,
            raw_row_number=row_number,
            raw_side=raw_side,
        )

    @staticmethod
    def _liquidated_position_side(raw_side: str) -> LiquidatedPositionSide:
        if raw_side == "buy":
            return LiquidatedPositionSide.SHORT
        if raw_side == "sell":
            return LiquidatedPositionSide.LONG
        raise ValueError("side must be buy or sell")
