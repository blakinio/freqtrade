from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.audit import AuditAction, AuditEvent, AuditResult
from ai_platform.portal.contracts.events import EventEnvelope, EventType
from ai_platform.portal.contracts.identity import ActorType
from ai_platform.portal.contracts.payloads import reject_sensitive_payload_keys
from ai_platform.portal.observability.redaction import REDACTED, redact_sensitive
from ai_platform.portal.security.sensitive_data import (
    SensitiveDataCycleError,
    SensitiveDataLimitError,
    SensitiveFieldKind,
    UnsupportedSensitiveDataTypeError,
    classify_sensitive_key,
)


@pytest.mark.parametrize(
    ("key", "kind"),
    [
        ("secret", SensitiveFieldKind.SECRET),
        ("exchange-secret", SensitiveFieldKind.SECRET),
        ("credential", SensitiveFieldKind.CREDENTIAL),
        ("serviceCredentials", SensitiveFieldKind.CREDENTIAL),
        ("token", SensitiveFieldKind.TOKEN),
        ("sessionToken", SensitiveFieldKind.TOKEN),
        ("cookie", SensitiveFieldKind.COOKIE),
        ("Set-Cookie", SensitiveFieldKind.COOKIE),
        ("authorization", SensitiveFieldKind.AUTHORIZATION),
        ("AuthorizationHeader", SensitiveFieldKind.AUTHORIZATION),
        ("api_key", SensitiveFieldKind.API_KEY),
        ("API-Key", SensitiveFieldKind.API_KEY),
        ("apikey", SensitiveFieldKind.API_KEY),
        ("apiSecret", SensitiveFieldKind.API_SECRET),
        ("private-key", SensitiveFieldKind.PRIVATE_KEY),
        ("passwordHash", SensitiveFieldKind.PASSWORD),
        ("passphrase", SensitiveFieldKind.PASSPHRASE),
        ("client_secret", SensitiveFieldKind.CLIENT_SECRET),
        ("refreshToken", SensitiveFieldKind.REFRESH_TOKEN),
        ("secret-ref", SensitiveFieldKind.SECRET_REFERENCE),
        ("vaultReference", SensitiveFieldKind.VAULT_REFERENCE),
    ],
)
def test_classifier_normalizes_sensitive_aliases(
    key: str,
    kind: SensitiveFieldKind,
) -> None:
    match = classify_sensitive_key(key)

    assert match is not None
    assert match.kind is kind


@pytest.mark.parametrize(
    "key",
    [
        "monkey",
        "tokenizer",
        "secretary",
        "cookie_policy",
        "authorization_status",
        "token_count",
        "api_key_name",
        "password_required",
        "public_key",
        "exchange_key",
        "credential_status",
    ],
)
def test_classifier_avoids_documented_false_positives(key: str) -> None:
    assert classify_sensitive_key(key) is None


def test_payload_guard_rejects_nested_alias_without_disclosing_value() -> None:
    canary = "SYNTHETIC-SECRET-CANARY"
    payload = {"safe": [{"deeper": {"Client-Secret": canary}}]}

    with pytest.raises(ValueError) as exc_info:
        reject_sensitive_payload_keys(payload)

    message = str(exc_info.value)
    assert "payload.safe[0].deeper.Client-Secret" in message
    assert "client_secret" in message
    assert canary not in message


def test_redaction_uses_same_classifier_and_replaces_sensitive_subtree_atomically() -> None:
    cyclic_secret: dict[str, object] = {}
    cyclic_secret["self"] = cyclic_secret
    payload = {
        "visible": "safe",
        "nested": [
            {"vaultRef": cyclic_secret},
            {"authorization_status": "ready"},
            {"apiKey": "SYNTHETIC-CANARY"},
        ],
    }

    redacted = redact_sensitive(payload)

    assert redacted == {
        "visible": "safe",
        "nested": [
            {"vaultRef": REDACTED},
            {"authorization_status": "ready"},
            {"apiKey": REDACTED},
        ],
    }
    assert payload["nested"][0]["vaultRef"] is cyclic_secret


def test_direct_and_indirect_cycles_fail_closed_for_safe_fields() -> None:
    direct: dict[str, object] = {}
    direct["self"] = direct
    with pytest.raises(SensitiveDataCycleError, match=r"payload\.self"):
        reject_sensitive_payload_keys(direct)
    with pytest.raises(SensitiveDataCycleError, match=r"value\.self"):
        redact_sensitive(direct)

    indirect: dict[str, object] = {"items": []}
    items = indirect["items"]
    assert isinstance(items, list)
    items.append(indirect)
    with pytest.raises(SensitiveDataCycleError, match=r"payload\.items\[0\]"):
        reject_sensitive_payload_keys(indirect)


def test_shared_non_cyclic_container_is_supported_deterministically() -> None:
    shared = {"safe": "value"}
    payload = {"first": shared, "second": shared}

    assert reject_sensitive_payload_keys(payload) is payload
    assert redact_sensitive(payload) == {
        "first": {"safe": "value"},
        "second": {"safe": "value"},
    }


@pytest.mark.parametrize("value", [{"unsupported": {"set-value"}}, {1: "non-string-key"}])
def test_unsupported_containers_and_mapping_keys_fail_closed(value: object) -> None:
    with pytest.raises(UnsupportedSensitiveDataTypeError):
        reject_sensitive_payload_keys(value)
    with pytest.raises(UnsupportedSensitiveDataTypeError):
        redact_sensitive(value)


def test_depth_and_item_limits_are_bounded() -> None:
    with pytest.raises(SensitiveDataLimitError, match="depth limit"):
        reject_sensitive_payload_keys({"one": {"two": "value"}}, max_depth=1)
    with pytest.raises(SensitiveDataLimitError, match="item limit"):
        reject_sensitive_payload_keys({"one": 1, "two": 2}, max_items=1)


def _audit_event(details: dict[str, object]) -> AuditEvent:
    now = datetime(2026, 8, 3, 11, tzinfo=UTC)
    return AuditEvent(
        audit_id=uuid4(),
        occurred_at=now,
        actor_type=ActorType.USER,
        actor_id="actor-a",
        tenant_id="tenant-a",
        resource_type="bot",
        resource_id="bot-a",
        action=AuditAction.BOT_CREATED,
        result=AuditResult.SUCCEEDED,
        request_id=uuid4(),
        correlation_id=uuid4(),
        details=details,
    )


def _event(payload: dict[str, object]) -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type=EventType.BOT_CREATED,
        event_version=1,
        occurred_at=datetime(2026, 8, 3, 11, tzinfo=UTC),
        tenant_id="tenant-a",
        actor_id="actor-a",
        request_id=uuid4(),
        correlation_id=uuid4(),
        aggregate_type="bot",
        aggregate_id="bot-a",
        payload=payload,
    )


@pytest.mark.parametrize("factory", [_audit_event, _event])
def test_audit_and_event_contracts_reject_sensitive_payloads_before_consumers(factory) -> None:
    canary = "SYNTHETIC-CONTRACT-CANARY"

    with pytest.raises(ValidationError) as exc_info:
        factory({"nested": {"exchangeApiKey": canary}})

    assert canary not in str(exc_info.value)


def test_audit_and_event_contracts_accept_safe_metadata_descriptors() -> None:
    payload = {
        "cookie_policy": "strict",
        "authorization_status": "denied",
        "token_count": 0,
        "api_key_name": "primary",
    }

    assert _audit_event(payload).details == payload
    assert _event(payload).payload == payload
