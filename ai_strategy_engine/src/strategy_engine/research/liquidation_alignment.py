"""Point-in-time research alignment for liquidation context.

The module consumes the terminal liquidation source shape structurally and keeps
open-interest and funding observations source-separated. Alignment is based on
when an observation became available, never on later-arriving data.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from typing import Protocol


class ObservationKind(StrEnum):
    OPEN_INTEREST = "open_interest"
    FUNDING_RATE = "funding_rate"


class AlignmentStatus(StrEnum):
    ALIGNED = "aligned"
    MISSING = "missing"
    DELAYED = "delayed"
    STALE = "stale"
    CONFLICT = "conflict"


class ObservationConflictError(ValueError):
    """Raised when one deterministic identity carries incompatible payloads."""


class LiquidationEventLike(Protocol):
    @property
    def schema_version(self) -> int: ...

    @property
    def source(self) -> str: ...

    @property
    def source_event_id(self) -> str: ...

    @property
    def symbol(self) -> str: ...

    @property
    def occurred_at_ms(self) -> int: ...

    @property
    def received_at_ms(self) -> int: ...


@dataclass(frozen=True, slots=True)
class MarketObservation:
    schema_version: int
    data_version: str
    source: str
    source_event_id: str
    symbol: str
    kind: ObservationKind
    event_time_ms: int
    received_at_ms: int
    available_at_ms: int
    value: Decimal

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        if not isinstance(self.kind, ObservationKind):
            raise TypeError("kind must be an ObservationKind")
        for name, value in (
            ("data_version", self.data_version),
            ("source", self.source),
            ("source_event_id", self.source_event_id),
            ("symbol", self.symbol),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.event_time_ms <= 0:
            raise ValueError("event_time_ms must be > 0")
        if self.received_at_ms < self.event_time_ms:
            raise ValueError("received_at_ms must be >= event_time_ms")
        if self.available_at_ms < self.received_at_ms:
            raise ValueError("available_at_ms must be >= received_at_ms")
        try:
            parsed = Decimal(str(self.value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("value must be decimal-compatible") from exc
        if not parsed.is_finite():
            raise ValueError("value must be finite")
        if self.kind is ObservationKind.OPEN_INTEREST and parsed < 0:
            raise ValueError("open_interest value must be >= 0")
        object.__setattr__(self, "value", parsed)

    @property
    def deterministic_id(self) -> str:
        canonical = "|".join(
            (
                self.source.strip().lower(),
                self.source_event_id.strip(),
                self.symbol.strip().upper(),
                self.kind.value,
            )
        )
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AlignedObservation:
    source: str
    kind: ObservationKind
    status: AlignmentStatus
    value: Decimal | None
    observation_id: str | None
    source_event_id: str | None
    schema_version: int | None
    data_version: str | None
    event_time_ms: int | None
    received_at_ms: int | None
    available_at_ms: int | None
    age_ms: int | None
    delay_ms: int | None


@dataclass(frozen=True, slots=True)
class LiquidationAlignment:
    liquidation_schema_version: int
    liquidation_id: str
    liquidation_source: str
    liquidation_source_event_id: str
    symbol: str
    event_time_ms: int
    received_at_ms: int
    as_of_ms: int
    observations: tuple[AlignedObservation, ...]


def deduplicate_observations(
    observations: Iterable[MarketObservation],
) -> tuple[MarketObservation, ...]:
    """Return deterministic unique observations and fail on identity conflicts."""

    unique: dict[str, MarketObservation] = {}
    for observation in observations:
        identity = observation.deterministic_id
        previous = unique.get(identity)
        if previous is None:
            unique[identity] = observation
            continue
        if previous != observation:
            raise ObservationConflictError(
                f"conflicting payloads for observation identity {identity}"
            )
    return tuple(
        sorted(
            unique.values(),
            key=lambda item: (
                item.source.lower(),
                item.kind.value,
                item.event_time_ms,
                item.available_at_ms,
                item.deterministic_id,
            ),
        )
    )


def align_liquidation_context(
    liquidation: LiquidationEventLike,
    observations: Iterable[MarketObservation],
    *,
    expected_sources: Iterable[str],
    as_of_ms: int | None = None,
    max_age_ms: int,
) -> LiquidationAlignment:
    """Align source-separated OI and funding observations without lookahead.

    For each expected source and metric, the latest observation with
    ``event_time_ms <= liquidation.occurred_at_ms`` is considered. It is usable
    only when ``available_at_ms <= as_of_ms``. A historical observation that
    exists but was not yet available is ``DELAYED``; absence is ``MISSING``;
    an available observation older than ``max_age_ms`` is ``STALE``.
    """

    if liquidation.schema_version != 1:
        raise ValueError("liquidation schema_version must be 1")
    for name, value in (
        ("source", liquidation.source),
        ("source_event_id", liquidation.source_event_id),
        ("symbol", liquidation.symbol),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"liquidation {name} must be a non-empty string")
    if liquidation.occurred_at_ms <= 0:
        raise ValueError("liquidation occurred_at_ms must be > 0")
    if liquidation.received_at_ms < liquidation.occurred_at_ms:
        raise ValueError("liquidation received_at_ms must be >= occurred_at_ms")
    if max_age_ms < 0:
        raise ValueError("max_age_ms must be >= 0")
    effective_as_of = liquidation.received_at_ms if as_of_ms is None else as_of_ms
    if effective_as_of < liquidation.occurred_at_ms:
        raise ValueError("as_of_ms must be >= liquidation occurred_at_ms")

    normalized_source_set: set[str] = set()
    for source in expected_sources:
        if not isinstance(source, str):
            raise TypeError("expected_sources entries must be strings")
        if source.strip():
            normalized_source_set.add(source.strip().lower())
    normalized_sources = tuple(sorted(normalized_source_set))
    if not normalized_sources:
        raise ValueError("expected_sources must contain at least one source")

    deduped = deduplicate_observations(observations)
    symbol = liquidation.symbol.strip().upper()
    aligned: list[AlignedObservation] = []

    for source in normalized_sources:
        for kind in ObservationKind:
            candidates = [
                item
                for item in deduped
                if item.source.strip().lower() == source
                and item.symbol.strip().upper() == symbol
                and item.kind is kind
                and item.event_time_ms <= liquidation.occurred_at_ms
            ]
            visible = [item for item in candidates if item.available_at_ms <= effective_as_of]
            if visible:
                selected = max(
                    visible,
                    key=lambda item: (
                        item.event_time_ms,
                        item.available_at_ms,
                        item.deterministic_id,
                    ),
                )
                age_ms = liquidation.occurred_at_ms - selected.event_time_ms
                status = AlignmentStatus.ALIGNED if age_ms <= max_age_ms else AlignmentStatus.STALE
                aligned.append(
                    AlignedObservation(
                        source=source,
                        kind=kind,
                        status=status,
                        value=selected.value,
                        observation_id=selected.deterministic_id,
                        source_event_id=selected.source_event_id,
                        schema_version=selected.schema_version,
                        data_version=selected.data_version,
                        event_time_ms=selected.event_time_ms,
                        received_at_ms=selected.received_at_ms,
                        available_at_ms=selected.available_at_ms,
                        age_ms=age_ms,
                        delay_ms=max(0, selected.available_at_ms - selected.event_time_ms),
                    )
                )
                continue

            if candidates:
                selected = max(
                    candidates,
                    key=lambda item: (
                        item.event_time_ms,
                        -item.available_at_ms,
                        item.deterministic_id,
                    ),
                )
                aligned.append(
                    AlignedObservation(
                        source=source,
                        kind=kind,
                        status=AlignmentStatus.DELAYED,
                        value=None,
                        observation_id=selected.deterministic_id,
                        source_event_id=selected.source_event_id,
                        schema_version=selected.schema_version,
                        data_version=selected.data_version,
                        event_time_ms=selected.event_time_ms,
                        received_at_ms=selected.received_at_ms,
                        available_at_ms=selected.available_at_ms,
                        age_ms=liquidation.occurred_at_ms - selected.event_time_ms,
                        delay_ms=selected.available_at_ms - effective_as_of,
                    )
                )
                continue

            aligned.append(
                AlignedObservation(
                    source=source,
                    kind=kind,
                    status=AlignmentStatus.MISSING,
                    value=None,
                    observation_id=None,
                    source_event_id=None,
                    schema_version=None,
                    data_version=None,
                    event_time_ms=None,
                    received_at_ms=None,
                    available_at_ms=None,
                    age_ms=None,
                    delay_ms=None,
                )
            )

    liquidation_id = sha256(
        "|".join(
            (
                liquidation.source.strip().lower(),
                liquidation.source_event_id.strip(),
                symbol,
                str(liquidation.occurred_at_ms),
            )
        ).encode("utf-8")
    ).hexdigest()
    return LiquidationAlignment(
        liquidation_schema_version=liquidation.schema_version,
        liquidation_id=liquidation_id,
        liquidation_source=liquidation.source,
        liquidation_source_event_id=liquidation.source_event_id,
        symbol=symbol,
        event_time_ms=liquidation.occurred_at_ms,
        received_at_ms=liquidation.received_at_ms,
        as_of_ms=effective_as_of,
        observations=tuple(aligned),
    )
