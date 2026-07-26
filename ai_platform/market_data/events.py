from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Self

from ai_platform.market_data.common import (
    SCHEMA_VERSION,
    AvailabilityTimestampKind,
    EventType,
    Exchange,
    FrozenJsonObject,
    MarketType,
    _json_compatible,
    _require_int,
    _require_text,
    canonical_instrument_id,
    canonical_sha256,
    decimal_text,
    decimal_value,
    raw_payload_sha256,
    validate_sha256,
)


@dataclass(frozen=True, slots=True)
class RawMarketEventEnvelope:
    schema_version: int
    event_type: EventType
    exchange: Exchange
    market_type: MarketType
    instrument_id: str
    native_instrument_id: str
    native_symbol: str
    canonical_symbol: str
    exchange_timestamp_ms: int
    availability_timestamp_ms: int
    availability_timestamp_kind: AvailabilityTimestampKind
    ingestion_timestamp_ms: int
    connection_id: str
    capture_run_id: str
    sequence: int | None
    previous_sequence: int | None
    snapshot: bool
    raw_payload_sha256: str
    raw_payload: object | None = None
    raw_payload_ref: str | None = None

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        expected_id = canonical_instrument_id(
            self.exchange,
            self.market_type,
            self.native_instrument_id,
        )
        if self.instrument_id != expected_id:
            raise ValueError("instrument_id does not match exchange, market and native ID")
        _require_text(self.native_symbol, field="native_symbol")
        _require_text(self.canonical_symbol, field="canonical_symbol")
        _require_int(self.exchange_timestamp_ms, field="exchange_timestamp_ms", minimum=1)
        _require_int(
            self.availability_timestamp_ms,
            field="availability_timestamp_ms",
            minimum=1,
        )
        _require_int(self.ingestion_timestamp_ms, field="ingestion_timestamp_ms", minimum=1)
        if self.ingestion_timestamp_ms < self.availability_timestamp_ms:
            raise ValueError("ingestion_timestamp_ms must be >= availability_timestamp_ms")
        _require_text(self.connection_id, field="connection_id")
        _require_text(self.capture_run_id, field="capture_run_id")
        if self.sequence is not None:
            _require_int(self.sequence, field="sequence")
        if self.previous_sequence is not None:
            _require_int(self.previous_sequence, field="previous_sequence")
        if self.sequence is None and self.previous_sequence is not None:
            raise ValueError("previous_sequence requires sequence")
        if (
            self.sequence is not None
            and self.previous_sequence is not None
            and self.previous_sequence >= self.sequence
        ):
            raise ValueError("previous_sequence must be less than sequence")
        if self.event_type is EventType.ORDER_BOOK_SNAPSHOT and not self.snapshot:
            raise ValueError("order-book snapshot events require snapshot=true")
        if self.event_type is EventType.ORDER_BOOK_DELTA and self.snapshot:
            raise ValueError("order-book delta events require snapshot=false")
        if self.snapshot and self.event_type is not EventType.ORDER_BOOK_SNAPSHOT:
            raise ValueError("snapshot=true is reserved for order-book snapshots")
        validate_sha256(self.raw_payload_sha256, field="raw_payload_sha256")
        if (self.raw_payload is None) == (self.raw_payload_ref is None):
            raise ValueError("exactly one of raw_payload or raw_payload_ref is required")
        if self.raw_payload_ref is not None:
            _require_text(self.raw_payload_ref, field="raw_payload_ref")
        if self.raw_payload is not None:
            expected_hash = raw_payload_sha256(self.raw_payload)
            if self.raw_payload_sha256 != expected_hash:
                raise ValueError("raw_payload_sha256 does not match raw_payload")

    @property
    def event_id(self) -> str:
        return canonical_sha256(self.identity_payload())

    def identity_payload(self) -> dict[str, Any]:
        return self.as_json_dict(include_raw_payload=False, include_event_id=False)

    def as_json_dict(
        self,
        *,
        include_raw_payload: bool = True,
        include_event_id: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "event_type": self.event_type.value,
            "exchange": self.exchange.value,
            "market_type": self.market_type.value,
            "instrument_id": self.instrument_id,
            "native_instrument_id": self.native_instrument_id,
            "native_symbol": self.native_symbol,
            "canonical_symbol": self.canonical_symbol,
            "exchange_timestamp_ms": self.exchange_timestamp_ms,
            "availability_timestamp_ms": self.availability_timestamp_ms,
            "availability_timestamp_kind": self.availability_timestamp_kind.value,
            "ingestion_timestamp_ms": self.ingestion_timestamp_ms,
            "connection_id": self.connection_id,
            "capture_run_id": self.capture_run_id,
            "sequence": self.sequence,
            "previous_sequence": self.previous_sequence,
            "snapshot": self.snapshot,
            "raw_payload_sha256": self.raw_payload_sha256,
            "raw_payload_ref": self.raw_payload_ref,
        }
        if include_raw_payload:
            payload["raw_payload"] = _json_compatible(self.raw_payload)
        if include_event_id:
            payload["event_id"] = self.event_id
        return payload


@dataclass(frozen=True, slots=True)
class InstrumentSnapshot:
    schema_version: int
    exchange: Exchange
    market_type: MarketType
    native_instrument_id: str
    canonical_instrument_id: str
    native_symbol: str
    canonical_symbol: str
    base_asset: str
    quote_asset: str
    settlement_asset: str | None
    contract_type: MarketType
    contract_value: Decimal | None
    contract_value_unit: str | None
    tick_size: Decimal
    quantity_step: Decimal
    active: bool
    listed_at_ms: int | None
    expires_at_ms: int | None
    source_snapshot_id: str
    source_snapshot_sha256: str

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        expected_id = canonical_instrument_id(
            self.exchange,
            self.market_type,
            self.native_instrument_id,
        )
        if self.canonical_instrument_id != expected_id:
            raise ValueError("canonical_instrument_id does not match instrument identity")
        for field_name in (
            "native_symbol",
            "canonical_symbol",
            "base_asset",
            "quote_asset",
            "source_snapshot_id",
        ):
            _require_text(str(getattr(self, field_name)), field=field_name)
        if self.contract_type is not self.market_type:
            raise ValueError("contract_type must match market_type")
        decimal_value(self.tick_size, field="tick_size", positive=True)
        decimal_value(self.quantity_step, field="quantity_step", positive=True)
        validate_sha256(self.source_snapshot_sha256, field="source_snapshot_sha256")
        if self.listed_at_ms is not None:
            _require_int(self.listed_at_ms, field="listed_at_ms", minimum=1)
        if self.expires_at_ms is not None:
            _require_int(self.expires_at_ms, field="expires_at_ms", minimum=1)
        if (
            self.listed_at_ms is not None
            and self.expires_at_ms is not None
            and self.expires_at_ms <= self.listed_at_ms
        ):
            raise ValueError("expires_at_ms must be after listed_at_ms")
        if self.market_type is MarketType.SPOT:
            if self.settlement_asset is not None:
                raise ValueError("spot instruments must not define settlement_asset")
            if self.contract_value is not None or self.contract_value_unit is not None:
                raise ValueError("spot instruments must not define contract metadata")
            if self.expires_at_ms is not None:
                raise ValueError("spot instruments must not define expires_at_ms")
        else:
            _require_text(self.settlement_asset or "", field="settlement_asset")
            if self.contract_value is None or self.contract_value_unit is None:
                raise ValueError("derivatives require contract_value and contract_value_unit")
            decimal_value(self.contract_value, field="contract_value", positive=True)
            _require_text(self.contract_value_unit, field="contract_value_unit")
            if self.market_type is MarketType.PERPETUAL and self.expires_at_ms is not None:
                raise ValueError("perpetual instruments must not define expires_at_ms")
            if self.market_type is MarketType.DATED_FUTURE and self.expires_at_ms is None:
                raise ValueError("dated futures require expires_at_ms")

    @property
    def content_sha256(self) -> str:
        return canonical_sha256(self.as_json_dict())

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "exchange": self.exchange.value,
            "market_type": self.market_type.value,
            "native_instrument_id": self.native_instrument_id,
            "canonical_instrument_id": self.canonical_instrument_id,
            "native_symbol": self.native_symbol,
            "canonical_symbol": self.canonical_symbol,
            "base_asset": self.base_asset,
            "quote_asset": self.quote_asset,
            "settlement_asset": self.settlement_asset,
            "contract_type": self.contract_type.value,
            "contract_value": (
                None if self.contract_value is None else decimal_text(self.contract_value)
            ),
            "contract_value_unit": self.contract_value_unit,
            "tick_size": decimal_text(self.tick_size),
            "quantity_step": decimal_text(self.quantity_step),
            "active": self.active,
            "listed_at_ms": self.listed_at_ms,
            "expires_at_ms": self.expires_at_ms,
            "source_snapshot_id": self.source_snapshot_id,
            "source_snapshot_sha256": self.source_snapshot_sha256,
        }


@dataclass(frozen=True, slots=True)
class UniverseDecision:
    canonical_instrument_id: str
    included: bool
    rank: int | None
    market_bucket: str
    ranking_components: FrozenJsonObject
    inclusion_reasons: tuple[str, ...]
    exclusion_reasons: tuple[str, ...]
    stable_tie_breaker: str

    def __post_init__(self) -> None:
        _require_text(self.canonical_instrument_id, field="canonical_instrument_id")
        if self.included != (self.rank is not None):
            raise ValueError("included decisions require rank; excluded decisions forbid rank")
        if self.rank is not None and self.rank < 1:
            raise ValueError("rank must be >= 1")
        if self.market_bucket not in {"spot", "derivatives"}:
            raise ValueError("market_bucket must be spot or derivatives")
        _require_text(self.stable_tie_breaker, field="stable_tie_breaker")
        if self.included and not self.inclusion_reasons:
            raise ValueError("included decisions require inclusion_reasons")
        if not self.included and not self.exclusion_reasons:
            raise ValueError("excluded decisions require exclusion_reasons")

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "included": self.included,
            "rank": self.rank,
            "market_bucket": self.market_bucket,
            "ranking_components": self.ranking_components.to_dict(),
            "inclusion_reasons": list(self.inclusion_reasons),
            "exclusion_reasons": list(self.exclusion_reasons),
            "stable_tie_breaker": self.stable_tie_breaker,
        }


@dataclass(frozen=True, slots=True)
class UniverseSnapshot:
    schema_version: int
    profile_identity: str
    snapshot_id: str
    selection_timestamp_ms: int
    source_instrument_snapshot_sha256: str
    selection_policy_version: str
    source_mode: str
    required_exchanges: tuple[Exchange, ...]
    ordered_instruments: tuple[str, ...]
    decisions: tuple[UniverseDecision, ...]
    snapshot_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        if self.profile_identity not in {
            "all-active-lite-v1",
            "top100-microstructure-v1",
            "top20-high-frequency-v1",
        }:
            raise ValueError("unsupported universe profile_identity")
        _require_int(self.selection_timestamp_ms, field="selection_timestamp_ms", minimum=1)
        validate_sha256(
            self.source_instrument_snapshot_sha256,
            field="source_instrument_snapshot_sha256",
        )
        _require_text(self.selection_policy_version, field="selection_policy_version")
        if self.source_mode not in {"intersection", "union"}:
            raise ValueError("source_mode must be intersection or union")
        if not self.required_exchanges or len(set(self.required_exchanges)) != len(
            self.required_exchanges
        ):
            raise ValueError("required_exchanges must be non-empty and unique")
        if len(set(self.ordered_instruments)) != len(self.ordered_instruments):
            raise ValueError("ordered_instruments must not contain duplicates")
        included = tuple(
            item.canonical_instrument_id
            for item in sorted(
                (decision for decision in self.decisions if decision.included),
                key=lambda decision: decision.rank or 0,
            )
        )
        if included != self.ordered_instruments:
            raise ValueError("ordered_instruments must match included decisions by rank")
        decision_ids = [item.canonical_instrument_id for item in self.decisions]
        if len(set(decision_ids)) != len(decision_ids):
            raise ValueError("decisions must not contain duplicate instruments")
        validate_sha256(self.snapshot_sha256, field="snapshot_sha256")
        if self.snapshot_sha256 != canonical_sha256(self.hash_payload()):
            raise ValueError("snapshot_sha256 does not match snapshot content")
        if self.snapshot_id != f"{self.profile_identity}:{self.snapshot_sha256[:24]}":
            raise ValueError("snapshot_id does not match profile and snapshot hash")

    @classmethod
    def create(
        cls,
        *,
        profile_identity: str,
        selection_timestamp_ms: int,
        source_instrument_snapshot_sha256: str,
        selection_policy_version: str,
        source_mode: str,
        required_exchanges: tuple[Exchange, ...],
        ordered_instruments: tuple[str, ...],
        decisions: tuple[UniverseDecision, ...],
    ) -> Self:
        seed = {
            "schema_version": SCHEMA_VERSION,
            "profile_identity": profile_identity,
            "selection_timestamp_ms": selection_timestamp_ms,
            "source_instrument_snapshot_sha256": source_instrument_snapshot_sha256,
            "selection_policy_version": selection_policy_version,
            "source_mode": source_mode,
            "required_exchanges": [item.value for item in required_exchanges],
            "ordered_instruments": list(ordered_instruments),
            "decisions": [item.as_json_dict() for item in decisions],
        }
        digest = canonical_sha256(seed)
        return cls(
            schema_version=SCHEMA_VERSION,
            profile_identity=profile_identity,
            snapshot_id=f"{profile_identity}:{digest[:24]}",
            selection_timestamp_ms=selection_timestamp_ms,
            source_instrument_snapshot_sha256=source_instrument_snapshot_sha256,
            selection_policy_version=selection_policy_version,
            source_mode=source_mode,
            required_exchanges=required_exchanges,
            ordered_instruments=ordered_instruments,
            decisions=decisions,
            snapshot_sha256=digest,
        )

    def hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "profile_identity": self.profile_identity,
            "selection_timestamp_ms": self.selection_timestamp_ms,
            "source_instrument_snapshot_sha256": self.source_instrument_snapshot_sha256,
            "selection_policy_version": self.selection_policy_version,
            "source_mode": self.source_mode,
            "required_exchanges": [item.value for item in self.required_exchanges],
            "ordered_instruments": list(self.ordered_instruments),
            "decisions": [item.as_json_dict() for item in self.decisions],
        }

    def as_json_dict(self) -> dict[str, Any]:
        return {
            **self.hash_payload(),
            "snapshot_id": self.snapshot_id,
            "snapshot_sha256": self.snapshot_sha256,
        }
