from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Self

from ai_platform.market_data.common import (
    SCHEMA_VERSION,
    ChannelFamily,
    CompressionPolicy,
    GapReason,
    _require_int,
    _require_text,
    canonical_sha256,
    validate_sha256,
)


@dataclass(frozen=True, slots=True)
class SegmentManifest:
    schema_version: int
    segment_id: str
    capture_run_id: str
    source_id: str
    channel_family: ChannelFamily
    connection_id: str
    instrument_ids: tuple[str, ...]
    opened_at_ms: int
    closed_at_ms: int
    first_event_id: str
    last_event_id: str
    event_count: int
    first_sequence: int | None
    last_sequence: int | None
    byte_count: int
    compression: CompressionPolicy
    content_sha256: str
    immutable: bool
    closure_state: str
    manifest_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        for field_name in (
            "segment_id",
            "capture_run_id",
            "source_id",
            "connection_id",
            "first_event_id",
            "last_event_id",
        ):
            _require_text(str(getattr(self, field_name)), field=field_name)
        if not self.instrument_ids or len(set(self.instrument_ids)) != len(self.instrument_ids):
            raise ValueError("instrument_ids must be non-empty and unique")
        _require_int(self.opened_at_ms, field="opened_at_ms", minimum=1)
        _require_int(self.closed_at_ms, field="closed_at_ms", minimum=1)
        if self.closed_at_ms < self.opened_at_ms:
            raise ValueError("closed_at_ms must be >= opened_at_ms")
        _require_int(self.event_count, field="event_count", minimum=1)
        _require_int(self.byte_count, field="byte_count", minimum=1)
        if (self.first_sequence is None) != (self.last_sequence is None):
            raise ValueError("first_sequence and last_sequence must both be present or absent")
        if self.first_sequence is not None and self.last_sequence is not None:
            _require_int(self.first_sequence, field="first_sequence")
            _require_int(self.last_sequence, field="last_sequence")
            if self.last_sequence < self.first_sequence:
                raise ValueError("last_sequence must be >= first_sequence")
        validate_sha256(self.content_sha256, field="content_sha256")
        validate_sha256(self.manifest_sha256, field="manifest_sha256")
        if not self.immutable or self.closure_state != "closed":
            raise ValueError("closed segments require immutable=true and closure_state=closed")
        if self.manifest_sha256 != canonical_sha256(self.hash_payload()):
            raise ValueError("manifest_sha256 does not match segment content")
        expected_id = f"segment:{self.content_sha256[:24]}:{self.manifest_sha256[:16]}"
        if self.segment_id != expected_id:
            raise ValueError("segment_id does not match segment content and manifest")

    @classmethod
    def create(
        cls,
        *,
        capture_run_id: str,
        source_id: str,
        channel_family: ChannelFamily,
        connection_id: str,
        instrument_ids: tuple[str, ...],
        opened_at_ms: int,
        closed_at_ms: int,
        first_event_id: str,
        last_event_id: str,
        event_count: int,
        first_sequence: int | None,
        last_sequence: int | None,
        byte_count: int,
        compression: CompressionPolicy,
        content_sha256: str,
    ) -> Self:
        seed = {
            "schema_version": SCHEMA_VERSION,
            "capture_run_id": capture_run_id,
            "source_id": source_id,
            "channel_family": channel_family.value,
            "connection_id": connection_id,
            "instrument_ids": list(instrument_ids),
            "opened_at_ms": opened_at_ms,
            "closed_at_ms": closed_at_ms,
            "first_event_id": first_event_id,
            "last_event_id": last_event_id,
            "event_count": event_count,
            "first_sequence": first_sequence,
            "last_sequence": last_sequence,
            "byte_count": byte_count,
            "compression": compression.value,
            "content_sha256": content_sha256,
            "immutable": True,
            "closure_state": "closed",
        }
        digest = canonical_sha256(seed)
        return cls(
            schema_version=SCHEMA_VERSION,
            segment_id=f"segment:{content_sha256[:24]}:{digest[:16]}",
            capture_run_id=capture_run_id,
            source_id=source_id,
            channel_family=channel_family,
            connection_id=connection_id,
            instrument_ids=instrument_ids,
            opened_at_ms=opened_at_ms,
            closed_at_ms=closed_at_ms,
            first_event_id=first_event_id,
            last_event_id=last_event_id,
            event_count=event_count,
            first_sequence=first_sequence,
            last_sequence=last_sequence,
            byte_count=byte_count,
            compression=compression,
            content_sha256=content_sha256,
            immutable=True,
            closure_state="closed",
            manifest_sha256=digest,
        )

    def hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capture_run_id": self.capture_run_id,
            "source_id": self.source_id,
            "channel_family": self.channel_family.value,
            "connection_id": self.connection_id,
            "instrument_ids": list(self.instrument_ids),
            "opened_at_ms": self.opened_at_ms,
            "closed_at_ms": self.closed_at_ms,
            "first_event_id": self.first_event_id,
            "last_event_id": self.last_event_id,
            "event_count": self.event_count,
            "first_sequence": self.first_sequence,
            "last_sequence": self.last_sequence,
            "byte_count": self.byte_count,
            "compression": self.compression.value,
            "content_sha256": self.content_sha256,
            "immutable": self.immutable,
            "closure_state": self.closure_state,
        }

    def as_json_dict(self) -> dict[str, Any]:
        return {
            **self.hash_payload(),
            "segment_id": self.segment_id,
            "manifest_sha256": self.manifest_sha256,
        }


@dataclass(frozen=True, slots=True)
class GapMarker:
    schema_version: int
    gap_id: str
    capture_run_id: str
    source_id: str
    channel_family: ChannelFamily
    connection_id: str
    instrument_id: str | None
    detected_at_ms: int
    reason: GapReason
    missing_from_sequence: int | None
    missing_to_sequence: int | None
    interval_started_at_ms: int | None
    interval_ended_at_ms: int | None
    resolved: bool
    resolved_at_ms: int | None
    resynchronization_segment_id: str | None

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        for field_name in ("gap_id", "capture_run_id", "source_id", "connection_id"):
            _require_text(str(getattr(self, field_name)), field=field_name)
        if self.instrument_id is not None:
            _require_text(self.instrument_id, field="instrument_id")
        _require_int(self.detected_at_ms, field="detected_at_ms", minimum=1)
        sequence_fields_present = (
            self.missing_from_sequence is not None and self.missing_to_sequence is not None
        )
        interval_fields_present = (
            self.interval_started_at_ms is not None and self.interval_ended_at_ms is not None
        )
        if self.reason is GapReason.SEQUENCE_GAP:
            if not sequence_fields_present:
                raise ValueError("sequence gaps require missing sequence bounds")
            missing_from = self.missing_from_sequence
            missing_to = self.missing_to_sequence
            if missing_from is None or missing_to is None:
                raise ValueError("sequence gaps require missing sequence bounds")
            _require_int(missing_from, field="missing_from_sequence")
            _require_int(missing_to, field="missing_to_sequence")
            if missing_to < missing_from:
                raise ValueError("missing_to_sequence must be >= missing_from_sequence")
        elif sequence_fields_present:
            raise ValueError("sequence bounds are reserved for sequence gaps")
        if interval_fields_present:
            interval_start = self.interval_started_at_ms
            interval_end = self.interval_ended_at_ms
            if interval_start is None or interval_end is None:
                raise ValueError("interval bounds must both be present")
            _require_int(interval_start, field="interval_started_at_ms", minimum=1)
            _require_int(interval_end, field="interval_ended_at_ms", minimum=1)
            if interval_end < interval_start:
                raise ValueError("interval_ended_at_ms must be >= interval_started_at_ms")
        elif (self.interval_started_at_ms is None) != (self.interval_ended_at_ms is None):
            raise ValueError("interval bounds must both be present or absent")
        if self.resolved:
            if self.resolved_at_ms is None:
                raise ValueError("resolved gaps require resolved_at_ms")
            _require_int(self.resolved_at_ms, field="resolved_at_ms", minimum=1)
            if self.resolved_at_ms < self.detected_at_ms:
                raise ValueError("resolved_at_ms must be >= detected_at_ms")
            if self.channel_family in {
                ChannelFamily.ORDER_BOOK_SNAPSHOT,
                ChannelFamily.ORDER_BOOK_DELTA,
            } and self.resynchronization_segment_id is None:
                raise ValueError("resolved order-book gaps require resynchronization segment")
        elif self.resolved_at_ms is not None or self.resynchronization_segment_id is not None:
            raise ValueError("unresolved gaps must not claim resolution evidence")
        if self.gap_id != f"gap:{canonical_sha256(self.identity_payload())[:32]}":
            raise ValueError("gap_id does not match gap content")

    @classmethod
    def create(
        cls,
        *,
        capture_run_id: str,
        source_id: str,
        channel_family: ChannelFamily,
        connection_id: str,
        instrument_id: str | None,
        detected_at_ms: int,
        reason: GapReason,
        missing_from_sequence: int | None = None,
        missing_to_sequence: int | None = None,
        interval_started_at_ms: int | None = None,
        interval_ended_at_ms: int | None = None,
        resolved: bool = False,
        resolved_at_ms: int | None = None,
        resynchronization_segment_id: str | None = None,
    ) -> Self:
        seed = {
            "schema_version": SCHEMA_VERSION,
            "capture_run_id": capture_run_id,
            "source_id": source_id,
            "channel_family": channel_family.value,
            "connection_id": connection_id,
            "instrument_id": instrument_id,
            "detected_at_ms": detected_at_ms,
            "reason": reason.value,
            "missing_from_sequence": missing_from_sequence,
            "missing_to_sequence": missing_to_sequence,
            "interval_started_at_ms": interval_started_at_ms,
            "interval_ended_at_ms": interval_ended_at_ms,
            "resolved": resolved,
            "resolved_at_ms": resolved_at_ms,
            "resynchronization_segment_id": resynchronization_segment_id,
        }
        return cls(
            schema_version=SCHEMA_VERSION,
            gap_id=f"gap:{canonical_sha256(seed)[:32]}",
            capture_run_id=capture_run_id,
            source_id=source_id,
            channel_family=channel_family,
            connection_id=connection_id,
            instrument_id=instrument_id,
            detected_at_ms=detected_at_ms,
            reason=reason,
            missing_from_sequence=missing_from_sequence,
            missing_to_sequence=missing_to_sequence,
            interval_started_at_ms=interval_started_at_ms,
            interval_ended_at_ms=interval_ended_at_ms,
            resolved=resolved,
            resolved_at_ms=resolved_at_ms,
            resynchronization_segment_id=resynchronization_segment_id,
        )

    @property
    def invalidates_order_book(self) -> bool:
        return self.channel_family in {
            ChannelFamily.ORDER_BOOK_SNAPSHOT,
            ChannelFamily.ORDER_BOOK_DELTA,
        } and not self.resolved

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capture_run_id": self.capture_run_id,
            "source_id": self.source_id,
            "channel_family": self.channel_family.value,
            "connection_id": self.connection_id,
            "instrument_id": self.instrument_id,
            "detected_at_ms": self.detected_at_ms,
            "reason": self.reason.value,
            "missing_from_sequence": self.missing_from_sequence,
            "missing_to_sequence": self.missing_to_sequence,
            "interval_started_at_ms": self.interval_started_at_ms,
            "interval_ended_at_ms": self.interval_ended_at_ms,
            "resolved": self.resolved,
            "resolved_at_ms": self.resolved_at_ms,
            "resynchronization_segment_id": self.resynchronization_segment_id,
        }

    def as_json_dict(self) -> dict[str, Any]:
        return {**self.identity_payload(), "gap_id": self.gap_id}


def assert_order_book_reconstructible(gaps: Sequence[GapMarker]) -> None:
    invalidating = sorted(gap.gap_id for gap in gaps if gap.invalidates_order_book)
    if invalidating:
        raise RuntimeError(
            "order book is invalid until successful resynchronization; unresolved gaps: "
            + ", ".join(invalidating)
        )
