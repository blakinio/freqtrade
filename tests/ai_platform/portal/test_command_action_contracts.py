from datetime import UTC, datetime
from uuid import uuid4

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent, AuditResult
from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.contracts.identity import ActorType


NOW = datetime(2026, 7, 22, 10, 50, tzinfo=UTC)


def test_bot_command_event_vocabulary_distinguishes_requested_from_observed_state() -> None:
    assert EventType.BOT_CREATED.value == "bot.created"
    assert EventType.BOT_CONFIG_REVISED.value == "bot.config_revised"
    assert EventType.BOT_START_REQUESTED.value == "bot.start_requested"
    assert EventType.BOT_PAUSE_REQUESTED.value == "bot.pause_requested"
    assert EventType.BOT_STOP_REQUESTED.value == "bot.stop_requested"
    assert EventType.BOT_PAUSED.value == "bot.paused"
    assert EventType.BOT_STOPPED.value == "bot.stopped"


def test_bot_command_audit_vocabulary_distinguishes_requested_from_observed_state() -> None:
    assert AuditAction.BOT_CREATED.value == "bot.created"
    assert AuditAction.BOT_CONFIG_REVISED.value == "bot.config_revised"
    assert AuditAction.BOT_START_REQUESTED.value == "bot.start_requested"
    assert AuditAction.BOT_PAUSE_REQUESTED.value == "bot.pause_requested"
    assert AuditAction.BOT_STOP_REQUESTED.value == "bot.stop_requested"
    assert AuditAction.BOT_STARTED.value == "bot.started"
    assert AuditAction.BOT_STOPPED.value == "bot.stopped"


def test_new_command_values_serialize_through_existing_v1_contracts() -> None:
    request_id = uuid4()
    correlation_id = uuid4()

    event = EventEnvelope(
        event_id=uuid4(),
        event_type=EventType.BOT_PAUSE_REQUESTED,
        event_version=1,
        occurred_at=NOW,
        tenant_id="tenant-1",
        actor_id="actor-1",
        request_id=request_id,
        correlation_id=correlation_id,
        aggregate_type="bot",
        aggregate_id="bot-1",
        payload={"desired_state": "PAUSED"},
    )
    audit = AuditEvent(
        audit_id=uuid4(),
        occurred_at=NOW,
        actor_type=ActorType.USER,
        actor_id="actor-1",
        tenant_id="tenant-1",
        resource_type="bot",
        resource_id="bot-1",
        action=AuditAction.BOT_PAUSE_REQUESTED,
        result=AuditResult.SUCCEEDED,
        request_id=request_id,
        correlation_id=correlation_id,
        details={"desired_state": "PAUSED"},
    )

    assert '"contract_version":"v1"' in event.canonical_json()
    assert '"event_type":"bot.pause_requested"' in event.canonical_json()
    assert '"action":"bot.pause_requested"' in audit.canonical_json()
