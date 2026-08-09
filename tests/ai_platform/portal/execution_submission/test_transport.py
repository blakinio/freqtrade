from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import httpx
import pytest

from ai_platform.portal.bot_operations.schema import AuthoritativeBotRuntimeState
from ai_platform.portal.contracts.bot_management.execution import ExecutionBinding
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    RiskDecision,
    RiskDecisionOutcome,
    RiskLimitEvaluation,
    TradeIntent,
    TradeSide,
)
from ai_platform.portal.credentials.material import CredentialMaterial, ResolvedCredentialLease
from ai_platform.portal.credentials.schema import (
    CredentialLeaseEvidence,
    CredentialPurpose,
)
from ai_platform.portal.execution.private_read import RuntimeReadFreshness
from ai_platform.portal.execution_submission.errors import (
    SubmissionPolicyError,
    SubmissionRuntimeRejectedError,
    SubmissionTransportAmbiguousError,
)
from ai_platform.portal.execution_submission.schema import PrivateDryRunSubmission
from ai_platform.portal.execution_submission.transport import (
    HttpxPrivateFreqtradeTransport,
    PrivateRuntimeTarget,
)


NOW = datetime(2026, 7, 29, 6, 0, tzinfo=UTC)
CONTEXT = CorrelationContext(
    request_id=UUID("10000000-0000-0000-0000-000000000001"),
    correlation_id=UUID("20000000-0000-0000-0000-000000000002"),
)


def _target(
    tmp_path: Path,
    endpoint: str = "https://freqtrade.internal:8443",
) -> PrivateRuntimeTarget:
    certificate = tmp_path / "runtime-ca.pem"
    certificate.write_text("test-ca", encoding="utf-8")
    return PrivateRuntimeTarget(
        runtime_id="runtime-1",
        endpoint=endpoint,
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
            runtime_api_username="runtime-user",
            runtime_api_password="runtime-password",
        ),
    )


def _submission() -> PrivateDryRunSubmission:
    trade_intent = TradeIntent(
        trade_intent_id=UUID("40000000-0000-0000-0000-000000000004"),
        tenant_id="tenant-a",
        bot_id="bot-1",
        source_actor_id="actor-1",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("25"),
        environment=Environment.TEST,
        created_at=NOW - timedelta(seconds=1),
        context=CONTEXT,
    )
    decision = RiskDecision(
        risk_decision_id=UUID("50000000-0000-0000-0000-000000000005"),
        tenant_id="tenant-a",
        trade_intent_id=trade_intent.trade_intent_id,
        risk_policy_version="risk-v1",
        decision=RiskDecisionOutcome.APPROVED,
        reason_codes=("RISK_APPROVED",),
        evaluated_limits=(
            RiskLimitEvaluation(
                limit_name="max_order_amount",
                configured_value="100",
                observed_value="25",
                passed=True,
            ),
        ),
        occurred_at=NOW,
        context=CONTEXT,
    )
    intent = ApprovedExecutionIntent(
        execution_intent_id=UUID("60000000-0000-0000-0000-000000000006"),
        tenant_id="tenant-a",
        trade_intent=trade_intent,
        risk_decision=decision,
        created_at=NOW,
        context=CONTEXT,
    )
    binding = ExecutionBinding(
        tenant_id="tenant-a",
        bot_id="bot-1",
        config_revision=7,
        runtime_id="runtime-1",
        runtime_revision=9,
        environment=Environment.TEST,
        execution_mode=ExecutionMode.DRY_RUN,
        idempotency_key="submit-intent-1",
        correlation=CONTEXT,
    )
    return PrivateDryRunSubmission(
        command_id="command-1",
        intent=intent,
        binding=binding,
        runtime=AuthoritativeBotRuntimeState(
            tenant_id="tenant-a",
            bot_id="bot-1",
            config_revision=7,
            runtime_generation_id="generation-1",
            runtime_id="runtime-1",
            runtime_revision=9,
            environment=Environment.TEST,
            freshness=RuntimeReadFreshness.CURRENT,
            kill_switch_active=False,
            observed_at=NOW,
        ),
        runtime_health=RuntimeHealthState.HEALTHY,
        connection_id="connection-1",
        credential_ref="credref_okxDryRun01",
        exchange_id="okx",
        approved_until=NOW + timedelta(minutes=1),
    )


@pytest.mark.parametrize(
    "endpoint,reason",
    [
        ("http://freqtrade.internal:8080", "RUNTIME_TLS_PRIVATE_ENDPOINT_REQUIRED"),
        ("https://user:password@freqtrade.internal", "RUNTIME_ENDPOINT_EMBEDS_CREDENTIALS"),
        ("https://freqtrade.internal/private", "RUNTIME_ENDPOINT_PATH_REJECTED"),
        ("https://freqtrade.example.com", "RUNTIME_ENDPOINT_MUST_BE_PRIVATE"),
    ],
)
def test_runtime_target_rejects_unsafe_endpoints(
    tmp_path: Path,
    endpoint: str,
    reason: str,
) -> None:
    with pytest.raises(SubmissionPolicyError) as error:
        _target(tmp_path, endpoint)
    assert error.value.reason_code == reason


def test_verify_and_submit_use_only_private_tls_runtime_api(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.host == "freqtrade.internal"
        assert request.url.scheme == "https"
        assert request.headers["authorization"].startswith("Basic ")
        if request.url.path == "/api/v1/show_config":
            return httpx.Response(
                200,
                json={"dry_run": True, "force_entry_enable": True, "exchange": "okx"},
            )
        payload = json.loads(request.content)
        assert payload == {
            "enter_tag": "portal:60000000-0000-0000-0000-000000000006",
            "pair": "BTC/USDT",
            "side": "long",
            "stakeamount": "25",
        }
        return httpx.Response(200, json={"trade_id": 77, "pair": "BTC/USDT"})

    transport = HttpxPrivateFreqtradeTransport(
        http_transport=httpx.MockTransport(handler),
        clock=lambda: NOW,
    )
    lease = _lease()
    target = _target(tmp_path)

    evidence = transport.verify_dry_run(target, lease)
    response = transport.submit(target, _submission(), lease)

    assert evidence.runtime_id == "runtime-1"
    assert evidence.verified_at == NOW
    assert response.runtime_request_ref == "freqtrade-trade_id-77"
    assert len(requests) == 2
    lease.close()


@pytest.mark.parametrize(
    "config,reason",
    [
        ({"dry_run": False, "force_entry_enable": True}, "RUNTIME_NOT_DRY_RUN"),
        ({"dry_run": True, "force_entry_enable": False}, "RUNTIME_FORCE_ENTRY_DISABLED"),
    ],
)
def test_runtime_configuration_must_independently_prove_dry_run(
    tmp_path: Path,
    config: dict[str, bool],
    reason: str,
) -> None:
    transport = HttpxPrivateFreqtradeTransport(
        http_transport=httpx.MockTransport(lambda request: httpx.Response(200, json=config)),
        clock=lambda: NOW,
    )
    with _lease() as lease, pytest.raises(SubmissionPolicyError) as error:
        transport.verify_dry_run(_target(tmp_path), lease)
    assert error.value.reason_code == reason


def test_submit_rejects_success_status_without_runtime_identity(tmp_path: Path) -> None:
    transport = HttpxPrivateFreqtradeTransport(
        http_transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"status": "Error entering trade"})
        )
    )
    with _lease() as lease, pytest.raises(SubmissionRuntimeRejectedError):
        transport.submit(_target(tmp_path), _submission(), lease)


def test_submit_treats_timeout_and_mismatched_pair_as_ambiguous(tmp_path: Path) -> None:
    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    timeout_transport = HttpxPrivateFreqtradeTransport(
        http_transport=httpx.MockTransport(timeout_handler)
    )
    with _lease() as lease, pytest.raises(SubmissionTransportAmbiguousError):
        timeout_transport.submit(_target(tmp_path), _submission(), lease)

    mismatch_transport = HttpxPrivateFreqtradeTransport(
        http_transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"trade_id": 77, "pair": "ETH/USDT"})
        )
    )
    with _lease() as lease, pytest.raises(SubmissionTransportAmbiguousError) as error:
        mismatch_transport.submit(_target(tmp_path), _submission(), lease)
    assert error.value.response_digest is not None
