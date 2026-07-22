from ai_platform.portal.contracts.audit import AuditAction
from ai_platform.portal.contracts.events import EventType


def test_model_lifecycle_audit_actions_use_canonical_values() -> None:
    assert AuditAction.MODEL_REGISTERED.value == "model.registered"
    assert AuditAction.MODEL_PROMOTED.value == "model.promoted"
    assert AuditAction.MODEL_ROLLED_BACK.value == "model.rolled_back"


def test_model_lifecycle_events_use_canonical_values() -> None:
    assert EventType.MODEL_REGISTERED.value == "model.registered"
    assert EventType.MODEL_VALIDATED.value == "model.validated"
    assert EventType.MODEL_PROMOTED.value == "model.promoted"
    assert EventType.MODEL_ROLLED_BACK.value == "model.rolled_back"


def test_existing_model_promoted_vocabulary_is_unchanged() -> None:
    assert AuditAction("model.promoted") is AuditAction.MODEL_PROMOTED
    assert EventType("model.promoted") is EventType.MODEL_PROMOTED
