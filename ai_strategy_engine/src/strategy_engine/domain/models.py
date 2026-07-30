from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

from strategy_engine.dsl.ast import ConditionGroup

NonEmptyStr = Annotated[str, Field(min_length=1)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
SchemaVersion = Literal["1.0.0"]
StrategySchemaVersion = Literal["1.0.0", "2.0.0"]


class Side(StrEnum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class Action(StrEnum):
    ENTER = "enter"
    EXIT = "exit"
    REDUCE = "reduce"
    HOLD = "hold"


class CanonicalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    def canonical_json(self, *, exclude: set[str] | None = None) -> str:
        payload = self.model_dump(mode="json", exclude=exclude or set())
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def canonical_sha256(self, *, exclude: set[str] | None = None) -> str:
        return hashlib.sha256(self.canonical_json(exclude=exclude).encode("utf-8")).hexdigest()


def canonical_sha256(payload: JsonValue | dict[str, Any] | BaseModel) -> str:
    if isinstance(payload, BaseModel):
        value: Any = payload.model_dump(mode="json")
    else:
        value = payload
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("timestamp must be normalized to UTC")
    return value


class Provenance(CanonicalModel):
    producer: NonEmptyStr
    source_event_id: NonEmptyStr
    lineage: tuple[NonEmptyStr, ...] = ()
    details: dict[str, JsonValue] = Field(default_factory=dict)


class FeatureRecord(CanonicalModel):
    schema_version: SchemaVersion = "1.0.0"
    feature_id: NonEmptyStr
    feature_version: NonEmptyStr
    symbol: NonEmptyStr
    timeframe: NonEmptyStr
    event_time: datetime
    detected_at: datetime
    available_at: datetime
    value: JsonValue
    source: NonEmptyStr
    is_confirmed: bool
    idempotency_key: NonEmptyStr
    code_version: Sha256
    data_version: Sha256
    configuration_hash: Sha256
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    provenance: Provenance

    _utc_event = field_validator("event_time")(_require_utc)
    _utc_detected = field_validator("detected_at")(_require_utc)
    _utc_available = field_validator("available_at")(_require_utc)

    @model_validator(mode="after")
    def validate_timestamp_order(self) -> Self:
        if self.detected_at < self.event_time:
            raise ValueError("detected_at cannot precede event_time")
        if self.available_at < self.detected_at:
            raise ValueError("available_at cannot precede detected_at")
        return self


class SignalEvent(CanonicalModel):
    schema_version: SchemaVersion = "1.0.0"
    signal_id: NonEmptyStr
    signal_version: NonEmptyStr
    strategy_id: NonEmptyStr
    strategy_version: NonEmptyStr
    symbol: NonEmptyStr
    timeframe: NonEmptyStr
    side: Side
    action: Action
    event_time: datetime
    detected_at: datetime
    available_at: datetime
    expires_at: datetime | None = None
    source: NonEmptyStr
    is_confirmed: bool
    idempotency_key: NonEmptyStr
    code_version: Sha256
    data_version: Sha256
    configuration_hash: Sha256
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reason_codes: tuple[NonEmptyStr, ...]
    feature_snapshot: dict[str, JsonValue]
    provenance: Provenance
    execution_policy: dict[str, JsonValue]

    _utc_event = field_validator("event_time")(_require_utc)
    _utc_detected = field_validator("detected_at")(_require_utc)
    _utc_available = field_validator("available_at")(_require_utc)
    _utc_expires = field_validator("expires_at")(
        lambda value: None if value is None else _require_utc(value)
    )

    @model_validator(mode="after")
    def validate_timestamp_order(self) -> Self:
        if self.detected_at < self.event_time:
            raise ValueError("detected_at cannot precede event_time")
        if self.available_at < self.detected_at:
            raise ValueError("available_at cannot precede detected_at")
        if self.expires_at is not None and self.expires_at < self.available_at:
            raise ValueError("expires_at cannot precede available_at")
        return self


class FeatureReference(CanonicalModel):
    id: NonEmptyStr
    params: dict[str, JsonValue] = Field(default_factory=dict)
    timeframe: NonEmptyStr
    confirmation: Literal["closed_bar", "confirmed_htf"]


class StrategyUniverse(CanonicalModel):
    symbols: tuple[NonEmptyStr, ...]
    timeframes: tuple[NonEmptyStr, ...]

    @model_validator(mode="after")
    def require_values(self) -> Self:
        if not self.symbols:
            raise ValueError("at least one symbol is required")
        if not self.timeframes:
            raise ValueError("at least one timeframe is required")
        if len(set(self.symbols)) != len(self.symbols):
            raise ValueError("duplicate symbols are not allowed")
        if len(set(self.timeframes)) != len(self.timeframes):
            raise ValueError("duplicate timeframes are not allowed")
        return self


class StrategyDefinition(CanonicalModel):
    schema_version: StrategySchemaVersion = "1.0.0"
    strategy_id: NonEmptyStr
    version: NonEmptyStr
    universe: StrategyUniverse
    features: tuple[FeatureReference, ...]
    regime: ConditionGroup | None = None
    entry_long: ConditionGroup
    entry_short: ConditionGroup | None = None
    exit: ConditionGroup
    risk: dict[str, JsonValue]
    execution: dict[str, JsonValue]
    provenance: Provenance

    @property
    def strategy_version(self) -> str:
        return self.version

    def migrate_to_v2(self) -> Self:
        """Return the deterministic v2 wire representation of a readable v1 strategy."""
        return self.model_copy(update={"schema_version": "2.0.0"})


class ValidationReport(CanonicalModel):
    schema_version: SchemaVersion = "1.0.0"
    valid: bool
    checked_at: datetime
    strategy_hash: Sha256
    errors: tuple[NonEmptyStr, ...] = ()
    warnings: tuple[NonEmptyStr, ...] = ()

    _utc_checked = field_validator("checked_at")(_require_utc)

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        if self.valid and self.errors:
            raise ValueError("a valid report cannot contain errors")
        if not self.valid and not self.errors:
            raise ValueError("an invalid report must contain errors")
        return self


class ShadowDecisionEvidence(CanonicalModel):
    schema_version: SchemaVersion = "1.0.0"
    evidence_version: NonEmptyStr
    decision_time: datetime
    symbol: NonEmptyStr
    timeframe: NonEmptyStr
    strategy_id: NonEmptyStr
    strategy_version: NonEmptyStr
    feature_records: tuple[FeatureRecord, ...]
    signal: SignalEvent | None
    risk_outcome: Literal["approved", "rejected", "no_signal"]
    reason_codes: tuple[NonEmptyStr, ...]
    data_hash: Sha256
    config_hash: Sha256
    code_hash: Sha256
    idempotency_key: NonEmptyStr
    provenance: Provenance
    no_order_submitted: Literal[True] = True
    evidence_hash: Sha256

    _utc_decision = field_validator("decision_time")(_require_utc)

    @model_validator(mode="after")
    def verify_evidence_hash(self) -> Self:
        expected = self.canonical_sha256(exclude={"evidence_hash"})
        if self.evidence_hash != expected:
            raise ValueError("evidence_hash does not match canonical evidence payload")
        return self

    @classmethod
    def create(cls, **values: Any) -> Self:
        values_without_hash = dict(values)
        values_without_hash.pop("evidence_hash", None)
        provisional = cls.model_construct(**values_without_hash, evidence_hash="0" * 64)
        digest = provisional.canonical_sha256(exclude={"evidence_hash"})
        return cls(**values_without_hash, evidence_hash=digest)
