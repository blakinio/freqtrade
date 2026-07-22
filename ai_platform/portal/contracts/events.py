from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import JsonValue, PositiveInt, field_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.payloads import reject_sensitive_payload_keys


class EventType(StrEnum):
    BOT_CREATED = "bot.created"
    BOT_CONFIG_REVISED = "bot.config_revised"
    BOT_START_REQUESTED = "bot.start_requested"
    BOT_PAUSE_REQUESTED = "bot.pause_requested"
    BOT_STOP_REQUESTED = "bot.stop_requested"
    BOT_STARTED = "bot.started"
    BOT_PAUSED = "bot.paused"
    BOT_STOPPED = "bot.stopped"
    BOT_ERROR = "bot.error"
    PREDICTION_CREATED = "prediction.created"
    TRADE_INTENT_CREATED = "trade_intent.created"
    RISK_APPROVED = "risk.approved"
    RISK_REJECTED = "risk.rejected"
    ORDER_SUBMITTED = "order.submitted"
    ORDER_FILLED = "order.filled"
    TRADE_OPENED = "trade.opened"
    TRADE_CLOSED = "trade.closed"
    MODEL_REGISTERED = "model.registered"
    MODEL_VALIDATED = "model.validated"
    MODEL_PROMOTED = "model.promoted"
    INSIGHT_CREATED = "insight.created"


class EventEnvelope(ContractModel):
    event_id: UUID
    event_type: EventType
    event_version: PositiveInt
    occurred_at: UtcDateTime
    tenant_id: NonEmptyStr
    actor_id: NonEmptyStr
    request_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None
    aggregate_type: NonEmptyStr
    aggregate_id: NonEmptyStr
    payload: dict[str, JsonValue]

    @field_validator("payload")
    @classmethod
    def reject_sensitive_payload(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        reject_sensitive_payload_keys(value)
        return value
