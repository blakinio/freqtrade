from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.observability.logging import structured_log
from ai_platform.portal.security.sensitive_data import (
    REDACTED_VALUE,
    SensitiveFieldKind,
    SensitiveValueKind,
    classify_sensitive_key,
    classify_sensitive_text,
    fingerprint_sensitive_value,
    redact_sensitive_data,
    reject_sensitive_data,
    validate_opaque_sensitive_reference,
)
from ai_platform.portal.security.sensitive_scan import scan_paths


def _canary(label: str) -> str:
    return f"SYNTHETIC-{label}-CANARY"


@pytest.mark.parametrize(
    ("key", "kind"),
    [
        ("session_id", SensitiveFieldKind.SESSION_ID),
        ("sessionId", SensitiveFieldKind.SESSION_ID),
        ("Proxy-Authorization", SensitiveFieldKind.AUTHORIZATION),
        ("clientKey", SensitiveFieldKind.CLIENT_KEY),
        ("database_dsn", SensitiveFieldKind.DSN),
        ("DATABASE_URL", SensitiveFieldKind.DSN),
        ("privateEndpoint", SensitiveFieldKind.PRIVATE_ENDPOINT),
        ("connection-string", SensitiveFieldKind.CONNECTION_STRING),
        ("credential_ref", SensitiveFieldKind.CREDENTIAL_REFERENCE),
        ("credentialReferenceName", SensitiveFieldKind.CREDENTIAL_REFERENCE),
        ("token_ref", SensitiveFieldKind.TOKEN_REFERENCE),
        ("secret_ref_name", SensitiveFieldKind.SECRET_REFERENCE),
        ("vault_path", SensitiveFieldKind.VAULT_REFERENCE),
        ("vaultReferenceName", SensitiveFieldKind.VAULT_REFERENCE),
    ],
)
def test_extended_aliases_are_classified(key: str, kind: SensitiveFieldKind) -> None:
    match = classify_sensitive_key(key)

    assert match is not None
    assert match.kind is kind


@pytest.mark.parametrize(
    "key",
    [
        "api_key_name",
        "authorization_status",
        "cookie_policy",
        "credential_status",
        "dsn_status",
        "public_endpoint",
        "session_id_status",
        "token_count",
    ],
)
def test_metadata_descriptors_and_public_endpoints_remain_safe(key: str) -> None:
    assert classify_sensitive_key(key) is None


@pytest.mark.parametrize(
    ("value", "kind"),
    [
        ("Bearer " + _canary("AUTH"), SensitiveValueKind.AUTHORIZATION_VALUE),
        ("Basic " + _canary("AUTH"), SensitiveValueKind.AUTHORIZATION_VALUE),
        (
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzeW50aGV0aWMifQ.signature-canary",
            SensitiveValueKind.JWT,
        ),
        (
            "postgresql://synthetic-user:synthetic-pass@private.invalid/database",
            SensitiveValueKind.URL_CREDENTIALS,
        ),
        (
            "-----BEGIN PRIVATE KEY-----\n" + _canary("KEY") + "\n-----END PRIVATE KEY-----",
            SensitiveValueKind.PRIVATE_KEY,
        ),
        (
            "mode=test&session_id=" + _canary("SESSION"),
            SensitiveValueKind.EMBEDDED_SECRET_ASSIGNMENT,
        ),
    ],
)
def test_high_confidence_sensitive_values_are_classified(
    value: str,
    kind: SensitiveValueKind,
) -> None:
    match = classify_sensitive_text(value)

    assert match is not None
    assert match.kind is kind


def test_serialized_json_form_and_header_objects_fail_closed_without_value_echo() -> None:
    canary = _canary("SERIALIZED")
    values = (
        json.dumps({"safe": {"refreshToken": canary}}),
        f"mode=test&credential_ref={canary}",
        f"X-Safe: value\nProxy-Authorization: Bearer {canary}",
    )

    for value in values:
        with pytest.raises(ValueError) as exc_info:
            reject_sensitive_data({"metadata": value})
        assert canary not in str(exc_info.value)
        assert redact_sensitive_data({"metadata": value}) == {"metadata": REDACTED_VALUE}


def test_opaque_reference_contract_accepts_identifiers_and_rejects_paths_urls_or_values() -> None:
    assert validate_opaque_sensitive_reference("exchange-connection-1") == "exchange-connection-1"

    for value in (
        "vault://secret/tenant-a/exchange",
        "/private/store/credential",
        "https://user:pass@private.invalid/value",
        "Bearer " + _canary("OPAQUE"),
        "short",
    ):
        with pytest.raises(ValueError):
            validate_opaque_sensitive_reference(value)


def test_bot_contract_uses_validated_opaque_exchange_reference() -> None:
    common = {
        "tenant_id": "tenant-a",
        "strategy_version": "strategy-v1",
        "model_version": "model-v1",
        "risk_policy_version": "risk-v1",
        "pair_universe": ("BTC/USDT",),
        "timeframe": "5m",
        "capital_allocation": "1000",
        "capital_currency": "USDT",
        "runtime_version": "runtime-v1",
        "config_revision": 1,
        "environment": Environment.TEST,
        "execution_mode": ExecutionMode.DRY_RUN,
    }
    assert BotSpec(exchange_connection_ref="exchange-connection-1", **common)

    with pytest.raises(ValidationError):
        BotSpec(exchange_connection_ref="vault://secret/tenant-a/exchange", **common)


def test_sensitive_fingerprint_is_keyed_deterministic_and_never_contains_value() -> None:
    value = _canary("FINGERPRINT")
    key_a = b"a" * 32
    key_b = b"b" * 32

    first = fingerprint_sensitive_value(value, key=key_a)
    second = fingerprint_sensitive_value(value, key=key_a)
    different = fingerprint_sensitive_value(value, key=key_b)

    assert first == second
    assert first != different
    assert first.startswith("hmac-sha256:")
    assert value not in first
    with pytest.raises(ValueError, match="at least 32 bytes"):
        fingerprint_sensitive_value(value, key=b"short")


def test_structured_log_redacts_extended_aliases_and_serialized_values(capsys) -> None:
    canary = _canary("LOG")

    structured_log(
        "security.test",
        attributes={
            "credential_ref": canary,
            "serialized": json.dumps({"session_id": canary}),
            "authorization_status": "denied",
        },
    )
    output = capsys.readouterr().out

    assert canary not in output
    assert output.count(REDACTED_VALUE) == 2
    assert '"authorization_status":"denied"' in output


def test_historical_scanner_reports_json_jsonl_and_sqlite_paths_without_values(
    tmp_path: Path,
) -> None:
    canary = _canary("HISTORICAL")
    json_path = tmp_path / "events.json"
    json_path.write_text(
        json.dumps({"records": [{"credential_ref": canary}]}),
        encoding="utf-8",
    )
    jsonl_path = tmp_path / "audit.jsonl"
    jsonl_path.write_text(
        json.dumps({"safe": json.dumps({"session_id": canary})}) + "\n",
        encoding="utf-8",
    )
    sqlite_path = tmp_path / "portal.sqlite3"
    connection = sqlite3.connect(sqlite_path)
    try:
        connection.execute("CREATE TABLE audit_events (payload_json TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO audit_events(payload_json) VALUES (?)",
            (json.dumps({"nested": {"private_endpoint": canary}}),),
        )
        connection.commit()
    finally:
        connection.close()

    report = scan_paths((tmp_path,))
    serialized = report.to_json()

    assert report.scanned_files == 3
    assert len(report.findings) == 3
    assert {finding.record_id for finding in report.findings} == {
        "document",
        "line:1",
        "audit_events:rowid:1",
    }
    assert canary not in serialized
    assert "credential_reference" in serialized
    assert "session_id" in serialized
    assert "private_endpoint" in serialized


def _context() -> RequestContext:
    return RequestContext(
        tenant_id="tenant-a",
        actor_id="actor-a",
        actor_type=ActorType.USER,
        permissions=(Permission.BOT_CREATE,),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def test_canonical_api_rejects_raw_reference_and_nested_alias_without_echo() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    client = TestClient(create_app(session_factory, lambda: _context()))
    canary = _canary("API")
    payload = {
        "bot_id": "bot-a",
        "name": "bot",
        "spec": {
            "tenant_id": "tenant-a",
            "strategy_version": "strategy-v1",
            "model_version": "model-v1",
            "risk_policy_version": "risk-v1",
            "exchange_connection_ref": f"vault://private/{canary}",
            "pair_universe": ["BTC/USDT"],
            "timeframe": "5m",
            "capital_allocation": "1000",
            "capital_currency": "USDT",
            "runtime_version": "runtime-v1",
            "config_revision": 1,
            "environment": "test",
            "execution_mode": "dry_run",
            "metadata": {"api_key": canary},
        },
    }

    response = client.post("/v1/bots", json=payload)
    body = response.text

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert canary not in body
    assert "vault://" not in body
    assert '"input"' not in body
