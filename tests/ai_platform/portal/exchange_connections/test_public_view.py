from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ConnectionRevocationStatus,
    ConnectionVerificationStatus,
    CredentialRotationStatus,
    ExchangeCapabilityProfile,
    ExchangeConnectionMetadata,
)
from ai_platform.portal.contracts.bot_management.policies import OrderType
from ai_platform.portal.contracts.bot_management.templates import MarketType
from ai_platform.portal.exchange_connections.public_schema import (
    public_exchange_connection_view,
)
from ai_platform.portal.exchange_connections.repository import (
    InMemoryExchangeConnectionRepository,
)
from ai_platform.portal.exchange_connections.schema import (
    ExchangeCapabilityProductProfile,
    ExchangeFunction,
    SupportedMarket,
    SupportedSymbol,
    SymbolPrecision,
)
from ai_platform.portal.exchange_connections.service import ExchangeConnectionService


NOW = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)


def _service() -> ExchangeConnectionService:
    service = ExchangeConnectionService(InMemoryExchangeConnectionRepository())
    capability = ExchangeCapabilityProfile(
        profile_id="simulated-spot",
        revision=1,
        exchange_id="simulated",
        market_types=(MarketType.SPOT,),
        order_types=(OrderType.LIMIT, OrderType.MARKET),
        supports_order_replace=True,
        supports_short=False,
        supports_subaccounts=False,
    )
    service.register_capability_profile(
        ExchangeCapabilityProductProfile(
            profile_ref="simulated-spot@1",
            capability=capability,
            markets=(
                SupportedMarket(
                    market_type=MarketType.SPOT,
                    symbols=(
                        SupportedSymbol(
                            symbol="BTC/USDT",
                            base_asset="BTC",
                            quote_asset="USDT",
                            order_types=(OrderType.LIMIT, OrderType.MARKET),
                            precision=SymbolPrecision(
                                price_decimal_places=2,
                                amount_decimal_places=6,
                                minimum_amount=Decimal("0.0001"),
                                minimum_cost=Decimal("5"),
                            ),
                        ),
                    ),
                ),
            ),
            functions=(
                ExchangeFunction.CANCEL_ORDER,
                ExchangeFunction.CREATE_ORDER,
                ExchangeFunction.FETCH_BALANCES,
                ExchangeFunction.FETCH_OPEN_ORDERS,
                ExchangeFunction.REPLACE_ORDER,
            ),
            published_at=NOW,
        )
    )
    return service


def test_public_view_excludes_credential_and_account_references() -> None:
    service = _service()
    product = service.create_connection(
        ExchangeConnectionMetadata(
            connection_id="conn-simulated-1",
            tenant_id="tenant-a",
            metadata_revision=1,
            display_name="Simulated dry-run",
            exchange_id="simulated",
            exchange_profile_ref="simulated-spot@1",
            credential_ref="credref_simulated01",
            account_label="internal-account",
            enabled_market_types=(MarketType.SPOT,),
            verification_status=ConnectionVerificationStatus.NEVER_VERIFIED,
            rotation_status=CredentialRotationStatus.CURRENT,
            revocation_status=ConnectionRevocationStatus.ACTIVE,
            created_at=NOW,
            updated_at=NOW,
        )
    )

    public = public_exchange_connection_view(product)
    serialized = public.canonical_json().lower()

    assert public.connection_id == "conn-simulated-1"
    assert public.credential_material_exposed is False
    assert '"credential_ref":' not in serialized
    assert "credref_" not in serialized
    assert '"account_label":' not in serialized
    assert '"subaccount_label":' not in serialized
    assert "internal-account" not in serialized
    assert "secret_store" not in serialized
    assert "passphrase" not in serialized
