from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field, JsonValue, field_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.identity import ActorType
from ai_platform.portal.contracts.payloads import reject_sensitive_payload_keys


class AuditAction(StrEnum):
    EXCHANGE_CONNECTION_CHANGED = "exchange_connection.changed"
    BOT_CREATED = "bot.created"
    BOT_CONFIG_REVISED = "bot.config_revised"
    BOT_START_REQUESTED = "bot.start_requested"
    BOT_PAUSE_REQUESTED = "bot.pause_requested"
    BOT_STOP_REQUESTED = "bot.stop_requested"
    BOT_STARTED = "bot.started"
    BOT_STOPPED = "bot.stopped"
    MANUAL_TRADE_INTENT = "trade.manual_intent"
    RISK_POLICY_CHANGED = "risk_policy.changed"
    MODEL_PROMOTED = "model.promoted"
    ROLE_PERMISSION_CHANGED = "role_permission.changed"
    KILL_SWITCH_ACTIVATED = "kill_switch.activated"
    KILL_SWITCH_RELEASED = "kill_switch.released"


class AuditResult(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    DENIED = "DENIED"
    FAILED = "FAILED"


class AuditEvent(ContractModel):
    audit_id: UUID
    occurred_at: UtcDateTime
    actor_type: ActorType
    actor_id: NonEmptyStr
    tenant_id: NonEmptyStr
    resource_type: NonEmptyStr
    resource_id: NonEmptyStr
    action: AuditAction
    result: AuditResult
    request_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None
    reason_code: NonEmptyStr | None = None
    details: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("details")
    @classmethod
    def reject_sensitive_details(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        reject_sensitive_payload_keys(value, path="details")
        return value
