from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ConnectionRevocationStatus,
    ConnectionVerificationStatus,
    CredentialRotationStatus,
    ExchangeCapabilityProfile,
    ExchangeConnectionMetadata,
    VerificationReasonCode,
)
from ai_platform.portal.contracts.bot_management.policies import OrderType
from ai_platform.portal.contracts.bot_management.templates import MarketType
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor, ActorType
from ai_platform.portal.exchange_connections import (
    ConnectionProductStatus,
    ExchangeCapabilityProductProfile,
    ExchangeConnectionService,
    ExchangeFunction,
    InMemoryExchangeConnectionRepository,
    SupportedMarket,
    SupportedSymbol,
    SymbolPrecision,
    TenantIsolationError,
    VerificationProbeResult,
    WithdrawalPermissionStatus,
)
from ai_platform.portal.exchange_connections.service import ExchangeConnectionValidationError


NOW = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)


def profile(*, supports_subaccounts: bool = True) -> ExchangeCapabilityProductProfile:
    capability = ExchangeCapabilityProfile(
        profile_id="okx-unified",
        revision=1,
        exchange_id="okx",
        market_types=(MarketType.FUTURES, MarketType.SPOT),
        order_types=(OrderType.LIMIT, OrderType.MARKET),
        supports_order_replace=True,
        supports_short=True,
        supports_subaccounts=supports_subaccounts,
        maximum_leverage=Decimal("5"),
    )
    symbol = SupportedSymbol(
        symbol="BTC/USDT",
        base_asset="BTC",
        quote_asset="USDT",
        order_types=(OrderType.LIMIT, OrderType.MARKET),
        precision=SymbolPrecision(
            price_decimal_places=1,
            amount_decimal_places=6,
            minimum_amount=Decimal("0.0001"),
            minimum_cost=Decimal("5"),
        ),
    )
    return ExchangeCapabilityProductProfile(
        profile_ref="okx-unified@1",
        capability=capability,
        markets=(
            SupportedMarket(market_type=MarketType.FUTURES, symbols=(symbol,)),
            SupportedMarket(market_type=MarketType.SPOT, symbols=(symbol,)),
        ),
        functions=(
            ExchangeFunction.CANCEL_ORDER,
            ExchangeFunction.CREATE_ORDER,
            ExchangeFunction.FETCH_BALANCES,
            ExchangeFunction.FETCH_OPEN_ORDERS,
            ExchangeFunction.FETCH_POSITIONS,
            ExchangeFunction.REPLACE_ORDER,
        ),
        published_at=NOW,
    )


def metadata(
    *,
    tenant_id: str = "tenant-a",
    subaccount_label: str | None = "dry-run",
) -> ExchangeConnectionMetadata:
    return ExchangeConnectionMetadata(
        connection_id="conn-okx-1",
        tenant_id=tenant_id,
        metadata_revision=1,
        display_name="OKX dry-run",
        exchange_id="okx",
        exchange_profile_ref="okx-unified@1",
        credential_ref="credref_okxDryRun01",
        account_label="primary",
        subaccount_label=subaccount_label,
        enabled_market_types=(MarketType.FUTURES, MarketType.SPOT),
        verification_status=ConnectionVerificationStatus.NEVER_VERIFIED,
        rotation_status=CredentialRotationStatus.CURRENT,
        revocation_status=ConnectionRevocationStatus.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def service(*, supports_subaccounts: bool = True) -> ExchangeConnectionService:
    result = ExchangeConnectionService(InMemoryExchangeConnectionRepository())
    result.register_capability_profile(profile(supports_subaccounts=supports_subaccounts))
    return result


def verify_ready(result: ExchangeConnectionService) -> None:
    result.create_connection(metadata())
    result.request_verification(
        verification_id="verify-1",
        tenant_id="tenant-a",
        connection_id="conn-okx-1",
        actor=Actor(actor_id="user-1", tenant_id="tenant-a", actor_type=ActorType.USER),
        environment=Environment.STAGING,
        correlation=CorrelationContext(request_id=uuid4(), correlation_id=uuid4()),
        idempotency_key="verify-idempotency-1",
        requested_at=NOW + timedelta(minutes=1),
    )
    verification = result.complete_verification(
        VerificationProbeResult(
            verification_id="verify-1",
            connection_id="conn-okx-1",
            tenant_id="tenant-a",
            metadata_revision=1,
            capability_profile_ref="okx-unified@1",
            exchange_available=True,
            trading_enabled=True,
            withdrawals_enabled=False,
            observed_at=NOW + timedelta(minutes=2),
            evidence_ref="evidence-verification-1",
        )
    )
    assert verification.status == ConnectionVerificationStatus.VERIFIED


def test_secret_fields_are_excluded_from_product_models() -> None:
    with pytest.raises(ValidationError):
        ExchangeConnectionMetadata(
            **metadata().model_dump(),
            api_key="not-allowed",
        )
    with pytest.raises(ValidationError):
        ExchangeCapabilityProductProfile(
            **profile().model_dump(),
            secret_store_path="vault://tenant-a/okx",
        )

    serialized = service().create_connection(metadata()).canonical_json().lower()
    assert "api_key" not in serialized
    assert "passphrase" not in serialized
    assert "secret_store" not in serialized
    assert "private_endpoint" not in serialized
    assert "credref_okxdryrun01" in serialized


def test_repository_denies_cross_tenant_access() -> None:
    result = service()
    result.create_connection(metadata())

    with pytest.raises(TenantIsolationError):
        result.get_connection(tenant_id="tenant-b", connection_id="conn-okx-1")
    assert result.list_connections(tenant_id="tenant-b") == ()


def test_invalid_capability_combinations_are_rejected() -> None:
    base = profile()
    with pytest.raises(ValidationError, match="order replace function"):
        ExchangeCapabilityProductProfile(
            **base.model_dump(exclude={"functions"}),
            functions=tuple(
                item for item in base.functions if item != ExchangeFunction.REPLACE_ORDER
            ),
        )

    spot_capability = ExchangeCapabilityProfile(
        profile_id="spot-short",
        revision=1,
        exchange_id="okx",
        market_types=(MarketType.SPOT,),
        order_types=(OrderType.LIMIT, OrderType.MARKET),
        supports_order_replace=False,
        supports_short=True,
        supports_subaccounts=False,
    )
    with pytest.raises(ValidationError, match="short capability"):
        ExchangeCapabilityProductProfile(
            profile_ref="spot-short@1",
            capability=spot_capability,
            markets=(base.markets[1],),
            functions=(
                ExchangeFunction.CANCEL_ORDER,
                ExchangeFunction.CREATE_ORDER,
                ExchangeFunction.FETCH_BALANCES,
                ExchangeFunction.FETCH_OPEN_ORDERS,
            ),
            published_at=NOW,
        )

    result = service(supports_subaccounts=False)
    with pytest.raises(ExchangeConnectionValidationError, match="subaccount"):
        result.create_connection(metadata())


def test_verified_connection_becomes_stale_after_maximum_age() -> None:
    result = service()
    verify_ready(result)

    stale = result.mark_stale(
        tenant_id="tenant-a",
        connection_id="conn-okx-1",
        as_of=NOW + timedelta(hours=3),
        maximum_age=timedelta(hours=1),
    )

    assert stale.metadata.verification_status == ConnectionVerificationStatus.STALE
    assert stale.state.product_status == ConnectionProductStatus.STALE
    assert stale.state.last_verified_at == NOW + timedelta(minutes=2)


def test_withdrawal_enabled_probe_is_rejected_without_permission_observation() -> None:
    result = service()
    result.create_connection(metadata())
    result.request_verification(
        verification_id="verify-withdrawals",
        tenant_id="tenant-a",
        connection_id="conn-okx-1",
        actor=Actor(actor_id="user-1", tenant_id="tenant-a", actor_type=ActorType.USER),
        environment=Environment.STAGING,
        correlation=CorrelationContext(request_id=uuid4(), correlation_id=uuid4()),
        idempotency_key="verify-withdrawals-1",
        requested_at=NOW + timedelta(minutes=1),
    )

    verification = result.complete_verification(
        VerificationProbeResult(
            verification_id="verify-withdrawals",
            connection_id="conn-okx-1",
            tenant_id="tenant-a",
            metadata_revision=1,
            capability_profile_ref="okx-unified@1",
            exchange_available=True,
            trading_enabled=True,
            withdrawals_enabled=True,
            observed_at=NOW + timedelta(minutes=2),
            evidence_ref="evidence-withdrawals-enabled",
        )
    )
    product = result.get_connection(tenant_id="tenant-a", connection_id="conn-okx-1")
    assert verification.status == ConnectionVerificationStatus.FAILED
    assert verification.permission_observation is None
    assert verification.reason_codes == (VerificationReasonCode.WITHDRAWAL_PERMISSION_ENABLED,)
    assert product.state.withdrawal_permission_status == WithdrawalPermissionStatus.ENABLED_REJECTED
    assert product.state.product_status == ConnectionProductStatus.FAILED
