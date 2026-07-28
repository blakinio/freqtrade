from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Side(StrEnum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class Action(StrEnum):
    ENTER = "enter"
    EXIT = "exit"
    REDUCE = "reduce"
    HOLD = "hold"


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("Timestamp must be normalized to UTC")
    return value


class FeatureRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_id: str
    symbol: str
    timeframe: str
    event_time: datetime
    detected_at: datetime
    available_at: datetime
    value: Any
    is_confirmed: bool
    source: str
    code_version: str
    data_version: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)

    _utc_event = field_validator("event_time")(_require_utc)
    _utc_detected = field_validator("detected_at")(_require_utc)
    _utc_available = field_validator("available_at")(_require_utc)

    @model_validator(mode="after")
    def validate_timestamp_order(self) -> "FeatureRecord":
        if self.detected_at < self.event_time:
            raise ValueError("detected_at cannot precede event_time")
        if self.available_at < self.detected_at:
            raise ValueError("available_at cannot precede detected_at")
        return self


class SignalEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_id: str
    strategy_id: str
    strategy_version: str
    symbol: str
    timeframe: str
    side: Side
    action: Action
    event_time: datetime
    detected_at: datetime
    available_at: datetime
    expires_at: datetime | None = None
    source: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reason_codes: list[str]
    feature_snapshot: dict[str, Any]
    provenance: dict[str, Any]
    execution_policy: dict[str, Any]

    _utc_event = field_validator("event_time")(_require_utc)
    _utc_detected = field_validator("detected_at")(_require_utc)
    _utc_available = field_validator("available_at")(_require_utc)

    @model_validator(mode="after")
    def validate_timestamp_order(self) -> "SignalEvent":
        if self.detected_at < self.event_time:
            raise ValueError("detected_at cannot precede event_time")
        if self.available_at < self.detected_at:
            raise ValueError("available_at cannot precede detected_at")
        if self.expires_at is not None and self.expires_at < self.available_at:
            raise ValueError("expires_at cannot precede available_at")
        return self
