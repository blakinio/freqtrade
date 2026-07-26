from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from ai_platform.market_data.common import (
    SCHEMA_VERSION,
    FrozenJsonObject,
    OutputImmutabilityState,
    _require_int,
    _require_text,
    canonical_sha256,
    validate_commit,
    validate_sha256,
)
from ai_platform.market_data.segments import GapMarker, SegmentManifest


@dataclass(frozen=True, slots=True)
class CaptureManifest:
    schema_version: int
    request_sha256: str
    collector_commit: str
    capture_run_id: str
    host_id: str
    started_at_ms: int
    ended_at_ms: int | None
    source_channel_states: FrozenJsonObject
    connection_intervals: tuple[FrozenJsonObject, ...]
    raw_segments: tuple[SegmentManifest, ...]
    counts: FrozenJsonObject
    gaps: tuple[GapMarker, ...]
    reconnects: FrozenJsonObject
    clock_evidence: FrozenJsonObject
    rejected_records: int
    output_immutability_state: OutputImmutabilityState
    execution_disabled: bool
    trading_credentials_absent: bool
    manifest_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        validate_sha256(self.request_sha256, field="request_sha256")
        validate_commit(self.collector_commit, field="collector_commit")
        _require_text(self.capture_run_id, field="capture_run_id")
        _require_text(self.host_id, field="host_id")
        _require_int(self.started_at_ms, field="started_at_ms", minimum=1)
        if self.ended_at_ms is not None:
            _require_int(self.ended_at_ms, field="ended_at_ms", minimum=1)
            if self.ended_at_ms < self.started_at_ms:
                raise ValueError("ended_at_ms must be >= started_at_ms")
        if not self.source_channel_states.to_dict():
            raise ValueError("source_channel_states must be non-empty")
        _require_int(self.rejected_records, field="rejected_records")
        if not self.execution_disabled:
            raise ValueError("execution_disabled must be true")
        if not self.trading_credentials_absent:
            raise ValueError("trading_credentials_absent must be true")
        if self.output_immutability_state is OutputImmutabilityState.CLOSED_IMMUTABLE:
            if self.ended_at_ms is None or not self.raw_segments:
                raise ValueError("closed immutable manifests require end time and raw segments")
            if any(
                not segment.immutable or segment.closure_state != "closed"
                for segment in self.raw_segments
            ):
                raise ValueError("all raw segments must be closed and immutable")
        validate_sha256(self.manifest_sha256, field="manifest_sha256")
        if self.manifest_sha256 != canonical_sha256(self.hash_payload()):
            raise ValueError("manifest_sha256 does not match capture manifest")

    @classmethod
    def create(
        cls,
        *,
        request_sha256: str,
        collector_commit: str,
        capture_run_id: str,
        host_id: str,
        started_at_ms: int,
        ended_at_ms: int | None,
        source_channel_states: FrozenJsonObject,
        connection_intervals: tuple[FrozenJsonObject, ...],
        raw_segments: tuple[SegmentManifest, ...],
        counts: FrozenJsonObject,
        gaps: tuple[GapMarker, ...],
        reconnects: FrozenJsonObject,
        clock_evidence: FrozenJsonObject,
        rejected_records: int,
        output_immutability_state: OutputImmutabilityState,
    ) -> Self:
        seed = {
            "schema_version": SCHEMA_VERSION,
            "request_sha256": request_sha256,
            "collector_commit": collector_commit,
            "capture_run_id": capture_run_id,
            "host_id": host_id,
            "started_at_ms": started_at_ms,
            "ended_at_ms": ended_at_ms,
            "source_channel_states": source_channel_states.to_dict(),
            "connection_intervals": [item.to_dict() for item in connection_intervals],
            "raw_segments": [item.as_json_dict() for item in raw_segments],
            "counts": counts.to_dict(),
            "gaps": [item.as_json_dict() for item in gaps],
            "reconnects": reconnects.to_dict(),
            "clock_evidence": clock_evidence.to_dict(),
            "rejected_records": rejected_records,
            "output_immutability_state": output_immutability_state.value,
            "execution_disabled": True,
            "trading_credentials_absent": True,
        }
        return cls(
            schema_version=SCHEMA_VERSION,
            request_sha256=request_sha256,
            collector_commit=collector_commit,
            capture_run_id=capture_run_id,
            host_id=host_id,
            started_at_ms=started_at_ms,
            ended_at_ms=ended_at_ms,
            source_channel_states=source_channel_states,
            connection_intervals=connection_intervals,
            raw_segments=raw_segments,
            counts=counts,
            gaps=gaps,
            reconnects=reconnects,
            clock_evidence=clock_evidence,
            rejected_records=rejected_records,
            output_immutability_state=output_immutability_state,
            execution_disabled=True,
            trading_credentials_absent=True,
            manifest_sha256=canonical_sha256(seed),
        )

    def hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_sha256": self.request_sha256,
            "collector_commit": self.collector_commit,
            "capture_run_id": self.capture_run_id,
            "host_id": self.host_id,
            "started_at_ms": self.started_at_ms,
            "ended_at_ms": self.ended_at_ms,
            "source_channel_states": self.source_channel_states.to_dict(),
            "connection_intervals": [item.to_dict() for item in self.connection_intervals],
            "raw_segments": [item.as_json_dict() for item in self.raw_segments],
            "counts": self.counts.to_dict(),
            "gaps": [item.as_json_dict() for item in self.gaps],
            "reconnects": self.reconnects.to_dict(),
            "clock_evidence": self.clock_evidence.to_dict(),
            "rejected_records": self.rejected_records,
            "output_immutability_state": self.output_immutability_state.value,
            "execution_disabled": self.execution_disabled,
            "trading_credentials_absent": self.trading_credentials_absent,
        }

    def as_json_dict(self) -> dict[str, Any]:
        return {**self.hash_payload(), "manifest_sha256": self.manifest_sha256}
