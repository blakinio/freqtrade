from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.bot_management.compatibility import (
    BotCompatibilityDecision,
    CompatibilityEvidenceRef,
    CompatibilityEvidenceType,
    CompatibilityReasonCode,
    CompatibilitySelection,
    CompatibilityStatus,
)
from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ConnectionRevocationStatus,
    ConnectionVerificationStatus,
    CredentialRotationStatus,
    ExchangeConnectionMetadata,
    ExchangePermissionObservation,
)
from ai_platform.portal.contracts.bot_management.policies import SignalAuthority, SignalCommand
from ai_platform.portal.contracts.bot_management.signals import (
    SignalAuthenticationMode,
    SignalEndpointMetadata,
    SignalEnvelope,
    SignalReplayEnvelope,
    SignalSchemaVersion,
)
from ai_platform.portal.contracts.bot_management.templates import (
    BotFamily,
    BotTemplateVersion,
    CatalogVersionRef,
    MarketType,
    PolicyFamily,
    TradeDirection,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import ExecutionMode


NOW = datetime(2026, 7, 27, 9, 0, tzinfo=UTC)
DIGEST = "b" * 64


def template() -> BotTemplateVersion:
    return BotTemplateVersion(
        template_id="template-directional",
        revision=1,
        display_name="Directional dry-run",
        bot_family=BotFamily.DIRECTIONAL,
        supported_strategy_versions=("strategy-v1",),
        supported_model_versions=("model-v1",),
        supported_exchange_profile_versions=("binance-spot-v1",),
        supported_market_types=(MarketType.SPOT,),
        supported_directions=(TradeDirection.LONG,),
        supported_execution_modes=(ExecutionMode.DRY_RUN, ExecutionMode.SIMULATED),
        required_policy_families=tuple(
            sorted(
                (
                    PolicyFamily.ENTRY,
                    PolicyFamily.EXIT,
                    PolicyFamily.MARKET,
                    PolicyFamily.POSITION_SIZING,
                    PolicyFamily.RISK_REFERENCE,
                    PolicyFamily.RUNTIME,
                ),
                key=lambda item: item.value,
            )
        ),
        optional_policy_families=(PolicyFamily.SIGNAL,),
        created_at=NOW,
    )


def evidence() -> tuple[CompatibilityEvidenceRef, ...]:
    items = (
        CompatibilityEvidenceRef(
            evidence_type=CompatibilityEvidenceType.EXCHANGE_PROFILE,
            evidence_id="binance-spot",
            version="1",
            sha256=DIGEST,
        ),
        CompatibilityEvidenceRef(
            evidence_type=CompatibilityEvidenceType.STRATEGY,
            evidence_id="strategy-v1",
            version="1",
            sha256=DIGEST,
        ),
        CompatibilityEvidenceRef(
            evidence_type=CompatibilityEvidenceType.TEMPLATE,
            evidence_id="template-directional",
            version="1",
            sha256=DIGEST,
        ),
    )
    return tuple(
        sorted(
            items,
            key=lambda item: (
                item.evidence_type.value,
                item.evidence_id,
                item.version,
                item.sha256,
            ),
        )
    )


def compatibility_decision() -> BotCompatibilityDecision:
    selection = CompatibilitySelection(
        tenant_id="tenant-a",
        template_ref=CatalogVersionRef(catalog_id="template-directional", version="1"),
        strategy_version="strategy-v1",
        model_version="model-v1",
        exchange_profile_version="binance-spot-v1",
        market_type=MarketType.SPOT,
        direction=TradeDirection.LONG,
        execution_mode=ExecutionMode.DRY_RUN,
        runtime_version="freqtrade-2026.7",
        risk_policy_version="risk-v1",
        policy_families=tuple(
            sorted(
                (
                    PolicyFamily.ENTRY,
                    PolicyFamily.EXIT,
                    PolicyFamily.MARKET,
                    PolicyFamily.POSITION_SIZING,
                    PolicyFamily.RISK_REFERENCE,
                    PolicyFamily.RUNTIME,
                ),
                key=lambda item: item.value,
            )
        ),
    )
    return BotCompatibilityDecision(
        decision_id="compat-1",
        tenant_id="tenant-a",
        selection=selection,
        status=CompatibilityStatus.COMPATIBLE,
        evidence_refs=evidence(),
        decided_at=NOW,
    )


def test_template_rejects_duplicate_catalog_values() -> None:
    data = template().model_dump()
    data["supported_strategy_versions"] = ("strategy-v1", "strategy-v1")
    with pytest.raises(ValidationError, match="duplicates"):
        BotTemplateVersion(**data)


def test_compatibility_decision_is_deterministic_and_fail_closed() -> None:
    first = compatibility_decision()
    second = compatibility_decision()
    assert first.canonical_json() == second.canonical_json()

    data = first.model_dump()
    data["reason_codes"] = (CompatibilityReasonCode.STRATEGY_UNSUPPORTED,)
    with pytest.raises(ValidationError, match="must not contain"):
        BotCompatibilityDecision(**data)


def test_exchange_metadata_uses_only_opaque_credential_references() -> None:
    values = {
        "connection_id": "connection-1",
        "tenant_id": "tenant-a",
        "metadata_revision": 1,
        "display_name": "Binance dry-run",
        "exchange_id": "binance",
        "exchange_profile_ref": "binance-spot-v1",
        "credential_ref": "credref_abcdefgh1234",
        "account_label": "main",
        "enabled_market_types": (MarketType.SPOT,),
        "verification_status": ConnectionVerificationStatus.VERIFIED,
        "rotation_status": CredentialRotationStatus.CURRENT,
        "revocation_status": ConnectionRevocationStatus.ACTIVE,
        "created_at": NOW,
        "updated_at": NOW,
    }
    metadata = ExchangeConnectionMetadata(**values)
    serialized = metadata.canonical_json().lower()
    for forbidden in (
        "api_key",
        "secret",
        "passphrase",
        "token",
        "http://",
        "https://",
        "/run/secrets",
        "vault://",
    ):
        assert forbidden not in serialized

    with pytest.raises(ValidationError):
        ExchangeConnectionMetadata(**(values | {"credential_ref": "vault://tenant/key"}))
    with pytest.raises(ValidationError):
        ExchangeConnectionMetadata(**(values | {"api_key": "forbidden"}))


def test_withdrawal_permission_observation_is_forbidden() -> None:
    with pytest.raises(ValidationError, match="withdrawal-enabled"):
        ExchangePermissionObservation(
            connection_id="connection-1",
            tenant_id="tenant-a",
            trading_enabled=True,
            withdrawals_enabled=True,
            observed_at=NOW,
            evidence_ref="permission-evidence-1",
        )


def test_signal_schema_cannot_require_secret_fields() -> None:
    with pytest.raises(ValidationError, match="secret-bearing"):
        SignalSchemaVersion(
            schema_id="schema-v1",
            revision=1,
            supported_commands=(SignalCommand.OPEN,),
            required_field_names=("api_key", "pair"),
        )


def test_signal_envelopes_are_secret_free_and_replay_bounded() -> None:
    endpoint = SignalEndpointMetadata(
        endpoint_id="endpoint-1",
        tenant_id="tenant-a",
        revision=1,
        display_name="TradingView input",
        endpoint_slug="endpoint_slug_123456",
        authentication_mode=SignalAuthenticationMode.HMAC_SHA256,
        authentication_ref="signalref_abcdefgh1234",
        signal_schema_ref="schema-v1",
        supported_commands=(SignalCommand.OPEN,),
        authority=SignalAuthority.ADVISORY_ONLY,
        replay_window_seconds=30,
        enabled=True,
        created_at=NOW,
        updated_at=NOW,
    )
    replay = SignalReplayEnvelope(
        signal_id="signal-1",
        tenant_id="tenant-a",
        endpoint_id="endpoint-1",
        idempotency_key="idem-signal-1",
        nonce_hash="c" * 64,
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=30),
    )
    envelope = SignalEnvelope(
        replay=replay,
        signal_schema_ref="schema-v1",
        authentication_evidence_ref="auth-evidence-1",
        bot_id="bot-1",
        config_revision=7,
        command=SignalCommand.OPEN,
        pair="BTC/USDT",
    )
    serialized = endpoint.canonical_json().lower() + envelope.canonical_json().lower()
    for forbidden in (
        "api_key",
        "secret",
        "passphrase",
        "token",
        "http://",
        "https://",
        "/run/secrets",
        "vault://",
    ):
        assert forbidden not in serialized

    with pytest.raises(ValidationError, match="after issue time"):
        SignalReplayEnvelope(
            signal_id="signal-1",
            tenant_id="tenant-a",
            endpoint_id="endpoint-1",
            idempotency_key="idem-signal-1",
            nonce_hash="c" * 64,
            issued_at=NOW,
            expires_at=NOW,
        )


def test_correlation_context_serializes_without_sensitive_material() -> None:
    context = CorrelationContext(
        request_id=UUID("00000000-0000-0000-0000-000000000001"),
        correlation_id=UUID("00000000-0000-0000-0000-000000000002"),
    )
    assert "00000000-0000-0000-0000-000000000001" in context.canonical_json()
