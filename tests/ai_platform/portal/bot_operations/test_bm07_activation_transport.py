from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from ai_platform.portal.bot_operations.activation_errors import (
    CommandActivationAmbiguousError,
    CommandActivationRejectedError,
    CommandActivationTransportError,
)
from ai_platform.portal.bot_operations.activation_transport import (
    HttpxPrivateRuntimeCommandTransport,
)
from ai_platform.portal.credentials.material import (
    CredentialMaterial,
    ResolvedCredentialLease,
)
from ai_platform.portal.credentials.schema import (
    CredentialLeaseEvidence,
    CredentialPurpose,
)
from ai_platform.portal.execution_submission.transport import PrivateRuntimeTarget


NOW = datetime(2026, 7, 29, 8, 0, tzinfo=UTC)


def _target(tmp_path: Path) -> PrivateRuntimeTarget:
    certificate = tmp_path / "runtime-ca.pem"
    certificate.write_text("test-ca", encoding="utf-8")
    return PrivateRuntimeTarget(
        runtime_id="runtime-1",
        endpoint="https://freqtrade.internal:8443",
        ca_certificate_path=certificate,
    )


def _lease() -> ResolvedCredentialLease:
    return ResolvedCredentialLease(
        evidence=CredentialLeaseEvidence(
            lease_id="credlease_0123456789abcdef0123456789abcdef",
            tenant_id="tenant-a",
            connection_id="connection-1",
            credential_ref="credref_okxDryRun01",
            exchange_id="okx",
            runtime_id="runtime-1",
            purpose=CredentialPurpose.RUNTIME_API,
            vault_version=1,
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=5),
            rotated_at=NOW - timedelta(days=1),
            evidence_ref="vault-evidence-1",
        ),
        _material=CredentialMaterial.from_values(
            exchange_api_key="exchange-key",
            exchange_api_secret="exchange-secret",
            exchange_passphrase=None,
            runtime_api_username="runtime-user-secret",
            runtime_api_password="runtime-password-secret",
        ),
    )


def test_force_exit_and_cancel_use_private_tls_and_secret_free_acknowledgements(
    tmp_path: Path,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.scheme == "https"
        assert request.url.host == "freqtrade.internal"
        assert request.headers["authorization"].startswith("Basic ")
        if request.url.path == "/api/v1/forceexit":
            assert json.loads(request.content) == {"amount": "25", "tradeid": "77"}
            return httpx.Response(200, json={"status": "position exit requested"})
        assert request.method == "DELETE"
        assert request.url.path == "/api/v1/trades/77/open-order"
        return httpx.Response(200, json={"result": True})

    transport = HttpxPrivateRuntimeCommandTransport(
        http_transport=httpx.MockTransport(handler),
        clock=lambda: NOW,
    )
    target = _target(tmp_path)
    with _lease() as lease:
        exit_ack = transport.force_exit(target, lease, trade_id="77", amount="25")
        cancel_ack = transport.cancel_open_order(target, lease, trade_id="77")

    assert exit_ack.acknowledged_at == cancel_ack.acknowledged_at == NOW
    assert exit_ack.execution_proven is cancel_ack.execution_proven is False
    serialized = exit_ack.canonical_json() + cancel_ack.canonical_json()
    assert "runtime-user-secret" not in serialized
    assert "runtime-password-secret" not in serialized
    assert "freqtrade.internal" not in serialized
    assert len(requests) == 2


def test_retryable_or_malformed_runtime_response_is_ambiguous(tmp_path: Path) -> None:
    server_error = HttpxPrivateRuntimeCommandTransport(
        http_transport=httpx.MockTransport(
            lambda request: httpx.Response(503, content=b"temporary")
        )
    )
    with (
        _lease() as lease,
        pytest.raises(CommandActivationAmbiguousError) as error,
    ):
        server_error.force_exit(_target(tmp_path), lease, trade_id="77")
    assert error.value.response_digest is not None

    malformed = HttpxPrivateRuntimeCommandTransport(
        http_transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"not-json"))
    )
    with _lease() as lease, pytest.raises(CommandActivationAmbiguousError):
        malformed.cancel_open_order(_target(tmp_path), lease, trade_id="77")


def test_explicit_runtime_rejection_and_auth_failure_are_distinct(
    tmp_path: Path,
) -> None:
    rejected = HttpxPrivateRuntimeCommandTransport(
        http_transport=httpx.MockTransport(lambda request: httpx.Response(409, json={}))
    )
    with _lease() as lease, pytest.raises(CommandActivationRejectedError):
        rejected.force_exit(_target(tmp_path), lease, trade_id="77")

    denied = HttpxPrivateRuntimeCommandTransport(
        http_transport=httpx.MockTransport(lambda request: httpx.Response(403, json={}))
    )
    with (
        _lease() as lease,
        pytest.raises(CommandActivationTransportError) as error,
    ):
        denied.cancel_open_order(_target(tmp_path), lease, trade_id="77")
    assert error.value.reason_code == "RUNTIME_AUTHENTICATION_FAILED"


def test_timeout_is_ambiguous_and_never_claims_success(tmp_path: Path) -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    transport = HttpxPrivateRuntimeCommandTransport(http_transport=httpx.MockTransport(timeout))
    with _lease() as lease, pytest.raises(CommandActivationAmbiguousError):
        transport.force_exit(_target(tmp_path), lease, trade_id="all")
