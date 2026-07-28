from __future__ import annotations

from pydantic import model_validator

from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ConnectionRevocationStatus,
    ConnectionVerificationStatus,
    CredentialRotationStatus,
    VerificationReasonCode,
)
from ai_platform.portal.contracts.bot_management.templates import MarketType
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.exchange_connections.schema import (
    ConnectionAvailabilityStatus,
    ConnectionProductStatus,
    ExchangeCapabilityProductProfile,
    ExchangeConnectionProduct,
    TradingPermissionStatus,
    WithdrawalPermissionStatus,
)


class PublicExchangeConnectionView(ContractModel):
    connection_id: NonEmptyStr
    metadata_revision: int
    display_name: NonEmptyStr
    exchange_id: NonEmptyStr
    exchange_profile_ref: NonEmptyStr
    enabled_market_types: tuple[MarketType, ...]
    verification_status: ConnectionVerificationStatus
    rotation_status: CredentialRotationStatus
    revocation_status: ConnectionRevocationStatus
    product_status: ConnectionProductStatus
    availability_status: ConnectionAvailabilityStatus
    trading_permission_status: TradingPermissionStatus
    withdrawal_permission_status: WithdrawalPermissionStatus
    last_verified_at: UtcDateTime | None = None
    reason_codes: tuple[VerificationReasonCode, ...] = ()
    capability_profile: ExchangeCapabilityProductProfile
    updated_at: UtcDateTime
    credential_material_exposed: bool = False

    @model_validator(mode="after")
    def validate_public_view(self) -> PublicExchangeConnectionView:
        if self.metadata_revision < 1:
            raise ValueError("public exchange metadata revision must be positive")
        if self.credential_material_exposed:
            raise ValueError("public exchange view must never expose credential material")
        return self


def public_exchange_connection_view(
    product: ExchangeConnectionProduct,
) -> PublicExchangeConnectionView:
    metadata = product.metadata
    state = product.state
    return PublicExchangeConnectionView(
        connection_id=metadata.connection_id,
        metadata_revision=metadata.metadata_revision,
        display_name=metadata.display_name,
        exchange_id=metadata.exchange_id,
        exchange_profile_ref=metadata.exchange_profile_ref,
        enabled_market_types=metadata.enabled_market_types,
        verification_status=metadata.verification_status,
        rotation_status=metadata.rotation_status,
        revocation_status=metadata.revocation_status,
        product_status=state.product_status,
        availability_status=state.availability_status,
        trading_permission_status=state.trading_permission_status,
        withdrawal_permission_status=state.withdrawal_permission_status,
        last_verified_at=state.last_verified_at,
        reason_codes=state.reason_codes,
        capability_profile=product.capability_profile,
        updated_at=state.updated_at,
    )
