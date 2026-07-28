from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.credentials import (
    CredentialIsolationError,
    CredentialLeaseRequest,
    CredentialPolicyError,
    CredentialPurpose,
    CredentialRotationRequiredError,
    CredentialUnavailableError,
    VaultAppRoleClient,
    VaultAppRoleConfig,
    VaultCredentialBroker,
    VaultProtocolError,
    validate_private_https_endpoint,
)
from ai_platform.portal.exchange_connections.credential_interface import (
    CredentialReferenceState,
    CredentialReferenceStatusPort,
)


NOW = datetime(2026, 7, 28, 20, 0, tzinfo=UTC)


class FakeVaultTransport:
    def __init__(self, *, document: dict[str, Any] | None = None) -> None:
        self.calls: list[tuple[str, str, str | None, dict[str, Any] | None]] = []
        self.document = document or credential_document()
        self.metadata = credential_metadata()
        self.available = True
        self.token_ttl = 600

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append((method, path, token, payload))
        if path == "/v1/auth/approle/login":
            return {
                "auth": {
                    "client_token": "vault-token-sensitive",
                    "lease_duration": self.token_ttl,
                }
            }
        if not self.available:
            raise CredentialUnavailableError("CREDENTIAL_REFERENCE_NOT_FOUND")
        if "/metadata/" in path:
            return {"data": self.metadata}
        if "/data/" in path:
            return {
                "data": {
                    "data": self.document,
                    "metadata": {"version": 3},
                }
            }
        raise AssertionError(f"unexpected Vault path: {path}")


def credential_document(**updates: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "tenant_id": "tenant-a",
        "connection_id": "conn-okx-1",
        "credential_ref": "credref_okxDryRun01",
        "exchange_id": "okx",
        "exchange_api_key": "exchange-api-key-sensitive",
        "exchange_api_secret": "exchange-api-secret-sensitive",
        "exchange_passphrase": "exchange-passphrase-sensitive",
        "runtime_api_username": "runtime-user-sensitive",
        "runtime_api_password": "runtime-password-sensitive",
        "withdrawals_enabled": False,
        "dry_run_only": True,
        "rotated_at": (NOW - timedelta(days=10)).isoformat(),
        "revoked": False,
    }
    result.update(updates)
    return result


def credential_metadata(**updates: Any) -> dict[str, Any]:
    custom = {
        "tenant_id": "tenant-a",
        "connection_id": "conn-okx-1",
        "credential_ref": "credref_okxDryRun01",
        "exchange_id": "okx",
        "rotated_at": (NOW - timedelta(days=10)).isoformat(),
        "revoked": "false",
        "withdrawals_enabled": "false",
        "dry_run_only": "true",
    }
    custom.update(updates.pop("custom_metadata", {}))
    result: dict[str, Any] = {
        "current_version": 3,
        "custom_metadata": custom,
        "versions": {
            "3": {
                "created_time": (NOW - timedelta(days=10)).isoformat(),
                "deletion_time": "",
                "destroyed": False,
            }
        },
    }
    result.update(updates)
    return result


def request(**updates: Any) -> CredentialLeaseRequest:
    values: dict[str, Any] = {
        "tenant_id": "tenant-a",
        "connection_id": "conn-okx-1",
        "credential_ref": "credref_okxDryRun01",
        "exchange_id": "okx",
        "runtime_id": "portal-ft-runtime-a",
        "environment": Environment.STAGING,
        "execution_mode": ExecutionMode.DRY_RUN,
        "purpose": CredentialPurpose.RUNTIME_API,
        "requested_at": NOW,
        "correlation": CorrelationContext(
            request_id=uuid4(),
            correlation_id=uuid4(),
        ),
    }
    values.update(updates)
    return CredentialLeaseRequest(**values)


def client(tmp_path: Path, transport: FakeVaultTransport) -> VaultAppRoleClient:
    role_id = tmp_path / "role-id"
    secret_id = tmp_path / "secret-id"
    role_id.write_text("role-id-sensitive\n", encoding="utf-8")
    secret_id.write_text("secret-id-sensitive\n", encoding="utf-8")
    return VaultAppRoleClient(
        transport,
        VaultAppRoleConfig(role_id_path=role_id, secret_id_path=secret_id),
        clock=lambda: NOW,
    )


def broker(tmp_path: Path, transport: FakeVaultTransport) -> VaultCredentialBroker:
    return VaultCredentialBroker(client(tmp_path, transport), clock=lambda: NOW)


def test_vault_endpoint_requires_tls_and_private_network() -> None:
    assert validate_private_https_endpoint("https://vault:8200") == "https://vault:8200"
    assert (
        validate_private_https_endpoint(
            "https://vault.portal.internal:8200",
        )
        == "https://vault.portal.internal:8200"
    )
    assert validate_private_https_endpoint("https://127.0.0.1:8200") == ("https://127.0.0.1:8200")

    for endpoint in (
        "http://vault:8200",
        "https://user:password@vault:8200",
        "https://vault.example.com:8200",
        "https://vault:8200/v1/secret",
    ):
        with pytest.raises(VaultProtocolError):
            validate_private_https_endpoint(endpoint)


def test_lease_request_rejects_non_dry_run() -> None:
    with pytest.raises(ValidationError, match="dry-run"):
        request(execution_mode=ExecutionMode.SIMULATED)


def test_approle_login_is_bounded_and_secret_document_is_redacted(
    tmp_path: Path,
) -> None:
    transport = FakeVaultTransport()
    vault = client(tmp_path, transport)

    record = vault.read_credential("tenants/tenant-a/exchange-connections/credref_okxDryRun01")

    assert record.version == 3
    assert record.document.exchange_id == "okx"
    rendered = repr(record.document)
    assert "exchange-api-key-sensitive" not in rendered
    assert "runtime-password-sensitive" not in rendered
    assert transport.calls[0][1] == "/v1/auth/approle/login"
    assert transport.calls[0][2] is None
    assert transport.calls[1][2] == "vault-token-sensitive"


def test_approle_token_ttl_must_remain_short(tmp_path: Path) -> None:
    transport = FakeVaultTransport()
    transport.token_ttl = 3600

    with pytest.raises(VaultProtocolError, match="VAULT_TOKEN_TTL_EXCEEDS_POLICY"):
        client(tmp_path, transport).read_metadata(
            "tenants/tenant-a/exchange-connections/credref_okxDryRun01"
        )


def test_broker_resolves_exact_scope_and_clears_material(tmp_path: Path) -> None:
    transport = FakeVaultTransport()
    credential_broker = broker(tmp_path, transport)

    with credential_broker.resolve(request()) as lease:
        runtime_auth = lease.use_runtime_api(lambda user, password: (user, password))
        exchange_auth = lease.use_exchange(
            lambda key, secret, passphrase: (key, secret, passphrase)
        )
        assert runtime_auth == (
            b"runtime-user-sensitive",
            b"runtime-password-sensitive",
        )
        assert exchange_auth == (
            b"exchange-api-key-sensitive",
            b"exchange-api-secret-sensitive",
            b"exchange-passphrase-sensitive",
        )
        serialized = lease.evidence.canonical_json().lower()
        assert "api_key" not in serialized
        assert "api_secret" not in serialized
        assert "password" not in serialized
        assert "passphrase" not in serialized
        assert "vault-kv-v2-" in serialized
        assert lease.evidence.withdrawals_disabled is True
        assert lease.evidence.dry_run_only is True

    assert lease.closed is True
    with pytest.raises(CredentialPolicyError, match="CREDENTIAL_LEASE_CLOSED"):
        lease.use_runtime_api(lambda user, password: (user, password))


def test_broker_denies_cross_tenant_and_exchange_scope(tmp_path: Path) -> None:
    cross_tenant = FakeVaultTransport(document=credential_document(tenant_id="tenant-b"))
    with pytest.raises(CredentialIsolationError, match="CREDENTIAL_SCOPE_MISMATCH"):
        broker(tmp_path, cross_tenant).resolve(request())

    wrong_exchange = FakeVaultTransport(document=credential_document(exchange_id="binance"))
    with pytest.raises(
        CredentialIsolationError,
        match="CREDENTIAL_EXCHANGE_MISMATCH",
    ):
        broker(tmp_path, wrong_exchange).resolve(request())


def test_broker_denies_withdrawals_and_rotation_overdue(tmp_path: Path) -> None:
    withdrawals = FakeVaultTransport(document=credential_document(withdrawals_enabled=True))
    with pytest.raises(CredentialPolicyError, match="WITHDRAWAL_PERMISSION_ENABLED"):
        broker(tmp_path, withdrawals).resolve(request())

    overdue = FakeVaultTransport(
        document=credential_document(rotated_at=(NOW - timedelta(days=90)).isoformat())
    )
    with pytest.raises(CredentialRotationRequiredError):
        broker(tmp_path, overdue).resolve(request())


def test_broker_rejects_unsafe_secret_paths_before_vault_call(
    tmp_path: Path,
) -> None:
    transport = FakeVaultTransport()
    credential_broker = broker(tmp_path, transport)

    with pytest.raises(
        CredentialIsolationError,
        match="CREDENTIAL_REFERENCE_PATH_INVALID",
    ):
        credential_broker.inspect_reference(
            tenant_id="tenant/escape",
            credential_ref="credref_okxDryRun01",
        )
    assert len(transport.calls) == 0


def test_inspection_implements_bm06_port_and_maps_states(tmp_path: Path) -> None:
    transport = FakeVaultTransport()
    credential_broker = broker(tmp_path, transport)
    status_port: CredentialReferenceStatusPort = credential_broker

    current = status_port.inspect_reference(
        tenant_id="tenant-a",
        credential_ref="credref_okxDryRun01",
    )
    assert current.state == CredentialReferenceState.CURRENT

    transport.metadata = credential_metadata(
        custom_metadata={
            "rotated_at": (NOW - timedelta(days=90)).isoformat(),
        }
    )
    rotation = status_port.inspect_reference(
        tenant_id="tenant-a",
        credential_ref="credref_okxDryRun01",
    )
    assert rotation.state == CredentialReferenceState.ROTATION_REQUIRED

    transport.metadata = credential_metadata(custom_metadata={"revoked": "true"})
    revoked = status_port.inspect_reference(
        tenant_id="tenant-a",
        credential_ref="credref_okxDryRun01",
    )
    assert revoked.state == CredentialReferenceState.REVOKED

    transport.available = False
    unavailable = status_port.inspect_reference(
        tenant_id="tenant-a",
        credential_ref="credref_okxDryRun01",
    )
    assert unavailable.state == CredentialReferenceState.UNAVAILABLE
