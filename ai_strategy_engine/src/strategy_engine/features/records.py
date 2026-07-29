from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from pydantic import JsonValue

from strategy_engine.domain.models import FeatureRecord, Provenance
from strategy_engine.features.pivots import PivotEvent


def feature_version_from_id(feature_id: str) -> str:
    name, separator, version = feature_id.rpartition(".v")
    if not separator or not name or not version.isdigit():
        raise ValueError(f"feature id must end with .v<number>: {feature_id}")
    return version


def make_feature_record(
    *,
    feature_id: str,
    symbol: str,
    timeframe: str,
    event_time: datetime,
    detected_at: datetime,
    available_at: datetime,
    value: JsonValue,
    source: str,
    is_confirmed: bool,
    idempotency_key: str,
    code_version: str,
    data_version: str,
    configuration_hash: str,
    producer: str,
    source_event_id: str,
    parameters: dict[str, JsonValue] | None = None,
    lineage: tuple[str, ...] = (),
    provenance_details: dict[str, JsonValue] | None = None,
) -> FeatureRecord:
    details = dict(provenance_details or {})
    details.setdefault("lineage_complete", True)
    details.setdefault("future_shift", 0)
    return FeatureRecord(
        feature_id=feature_id,
        feature_version=feature_version_from_id(feature_id),
        symbol=symbol,
        timeframe=timeframe,
        event_time=event_time,
        detected_at=detected_at,
        available_at=available_at,
        value=value,
        source=source,
        is_confirmed=is_confirmed,
        idempotency_key=idempotency_key,
        code_version=code_version,
        data_version=data_version,
        configuration_hash=configuration_hash,
        parameters=parameters or {},
        provenance=Provenance(
            producer=producer,
            source_event_id=source_event_id,
            lineage=lineage,
            details=details,
        ),
    )


def make_confirmed_htf_record(
    *,
    feature_id: str,
    symbol: str,
    timeframe: str,
    bar_open_time: datetime,
    bar_duration: timedelta,
    processing_latency: timedelta,
    decision_time: datetime,
    value: JsonValue,
    source: str,
    idempotency_key: str,
    code_version: str,
    data_version: str,
    configuration_hash: str,
    producer: str,
    source_event_id: str,
    parameters: dict[str, JsonValue] | None = None,
) -> FeatureRecord:
    if bar_duration <= timedelta(0):
        raise ValueError("bar_duration must be positive")
    if processing_latency < timedelta(0):
        raise ValueError("processing_latency cannot be negative")
    close_time = bar_open_time + bar_duration
    available_at = close_time + processing_latency
    is_confirmed = close_time <= decision_time
    return make_feature_record(
        feature_id=feature_id,
        symbol=symbol,
        timeframe=timeframe,
        event_time=bar_open_time,
        detected_at=close_time,
        available_at=available_at,
        value=value,
        source=source,
        is_confirmed=is_confirmed,
        idempotency_key=idempotency_key,
        code_version=code_version,
        data_version=data_version,
        configuration_hash=configuration_hash,
        producer=producer,
        source_event_id=source_event_id,
        parameters=parameters,
        provenance_details={
            "is_htf": True,
            "bar_closed": is_confirmed,
            "htf_close_time": close_time.isoformat(),
        },
    )


def make_confirmed_pivot_record(
    *,
    pivot: PivotEvent,
    symbol: str,
    timeframe: str,
    decision_time: datetime,
    idempotency_key: str,
    code_version: str,
    data_version: str,
    configuration_hash: str,
    producer: str,
    source_event_id: str,
    parameters: dict[str, JsonValue],
    detection_event_confirmed: bool = True,
) -> FeatureRecord:
    event_time = _as_datetime(pivot.event_time)
    detected_at = _as_datetime(pivot.detected_at)
    available_at = _as_datetime(pivot.available_at)
    available_before_decision = available_at <= decision_time
    confirmed = detection_event_confirmed and available_before_decision
    return make_feature_record(
        feature_id="confirmed_pivot.v1",
        symbol=symbol,
        timeframe=timeframe,
        event_time=event_time,
        detected_at=detected_at,
        available_at=available_at,
        value={
            "kind": pivot.kind,
            "level": pivot.level,
            "pivot_index": pivot.pivot_index,
            "detected_index": pivot.detected_index,
        },
        source="confirmed-pivot",
        is_confirmed=confirmed,
        idempotency_key=idempotency_key,
        code_version=code_version,
        data_version=data_version,
        configuration_hash=configuration_hash,
        producer=producer,
        source_event_id=source_event_id,
        parameters=parameters,
        provenance_details={
            "pivot_confirmed": confirmed,
            "right_bars_confirmed": detection_event_confirmed,
            "detection_event_confirmed": detection_event_confirmed,
            "available_before_decision": available_before_decision,
        },
    )


def _as_datetime(value: Any) -> datetime:
    converted = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if not isinstance(converted, datetime):
        raise TypeError("timestamp value cannot be converted to datetime")
    return converted
