from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, NonNegativeInt, model_validator

from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ConnectionVerificationStatus,
    ExchangeCapabilityProfile,
    ExchangeConnectionMetadata,
    VerificationReasonCode,
)
from ai_platform.portal.contracts.bot_management.policies import OrderType, PositiveDecimal
from ai_platform.portal.contracts.bot_management.templates import MarketType
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime


def _require_sorted_unique(values: list[str], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    if values != sorted(values):
        raise ValueError(f"{field_name} must use deterministic sorted order")


class ExchangeFunction(StrEnum):
    CANCEL_ORDER = "CANCEL_ORDER"
    CREATE_ORDER = "CREATE_ORDER"
    FETCH_BALANCES = "FETCH_BALANCES"
    FETCH_OPEN_ORDERS = "FETCH_OPEN_ORDERS"
    FETCH_POSITIONS = "FETCH_POSITIONS"
    REPLACE_ORDER = "REPLACE_ORDER"


class ConnectionAvailabilityStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class TradingPermissionStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class WithdrawalPermissionStatus(StrEnum):
    EXPECTED_DISABLED = "EXPECTED_DISABLED"
    DISABLED_CONFIRMED = "DISABLED_CONFIRMED"
    ENABLED_REJECTED = "ENABLED_REJECTED"


class ConnectionProductStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    VERIFYING = "VERIFYING"
    READY = "READY"
    FAILED = "FAILED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    REVOKED = "REVOKED"
    ROTATION_REQUIRED = "ROTATION_REQUIRED"


class SymbolPrecision(ContractModel):
    price_decimal_places: NonNegativeInt
    amount_decimal_places: NonNegativeInt
    minimum_amount: PositiveDecimal
    minimum_cost: PositiveDecimal | None = None


class SupportedSymbol(ContractModel):
    symbol: NonEmptyStr
    base_asset: NonEmptyStr
    quote_asset: NonEmptyStr
    order_types: Annotated[tuple[OrderType, ...], Field(min_length=1)]
    precision: SymbolPrecision

    @model_validator(mode="after")
    def validate_symbol(self) -> Self:
        order_types = [item.value for item in self.order_types]
        _require_sorted_unique(order_types, "symbol order types")
        if self.base_asset == self.quote_asset:
            raise ValueError("base and quote assets must differ")
        return self


class SupportedMarket(ContractModel):
    market_type: MarketType
    symbols: Annotated[tuple[SupportedSymbol, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_market(self) -> Self:
        symbols = [item.symbol for item in self.symbols]
        _require_sorted_unique(symbols, "market symbols")
        return self


class ExchangeCapabilityProductProfile(ContractModel):
    profile_ref: NonEmptyStr
    capability: ExchangeCapabilityProfile
    markets: Annotated[tuple[SupportedMarket, ...], Field(min_length=1)]
    functions: Annotated[tuple[ExchangeFunction, ...], Field(min_length=1)]
    published_at: UtcDateTime

    @model_validator(mode="after")
    def validate_profile(self) -> Self:
        self._validate_profile_ref()
        self._validate_markets()
        self._validate_functions()
        self._validate_leverage_and_short()
        self._validate_symbol_order_types()
        return self

    def _validate_profile_ref(self) -> None:
        expected_ref = f"{self.capability.profile_id}@{self.capability.revision}"
        if self.profile_ref != expected_ref:
            raise ValueError("profile_ref must bind the exact capability profile revision")

    def _validate_markets(self) -> None:
        market_types = [item.market_type.value for item in self.markets]
        _require_sorted_unique(market_types, "product markets")
        if set(market_types) != {item.value for item in self.capability.market_types}:
            raise ValueError("product markets must exactly match the capability profile")

    def _validate_functions(self) -> None:
        functions = [item.value for item in self.functions]
        _require_sorted_unique(functions, "exchange functions")
        has_replace = ExchangeFunction.REPLACE_ORDER in self.functions
        if has_replace != self.capability.supports_order_replace:
            raise ValueError("order replace function must match supports_order_replace")

    def _validate_leverage_and_short(self) -> None:
        leveraged_markets = {MarketType.MARGIN, MarketType.FUTURES}
        has_leveraged_market = any(item.market_type in leveraged_markets for item in self.markets)
        if has_leveraged_market and self.capability.maximum_leverage is None:
            raise ValueError("margin or futures capability requires maximum_leverage")
        if self.capability.supports_short and not has_leveraged_market:
            raise ValueError("short capability requires margin or futures market support")

    def _validate_symbol_order_types(self) -> None:
        allowed_order_types = set(self.capability.order_types)
        for market in self.markets:
            for symbol in market.symbols:
                if not set(symbol.order_types).issubset(allowed_order_types):
                    raise ValueError("symbol order types must be allowed by the capability profile")


class ExchangeConnectionState(ContractModel):
    connection_id: NonEmptyStr
    tenant_id: NonEmptyStr
    metadata_revision: int = Field(gt=0)
    verification_status: ConnectionVerificationStatus
    product_status: ConnectionProductStatus
    availability_status: ConnectionAvailabilityStatus
    trading_permission_status: TradingPermissionStatus
    withdrawal_permission_status: WithdrawalPermissionStatus
    last_verification_id: NonEmptyStr | None = None
    last_verified_at: UtcDateTime | None = None
    reason_codes: tuple[VerificationReasonCode, ...] = ()
    updated_at: UtcDateTime

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        reasons = [item.value for item in self.reason_codes]
        _require_sorted_unique(reasons, "state reason codes")
        if self.product_status == ConnectionProductStatus.READY:
            self._validate_ready()
        if self.product_status == ConnectionProductStatus.STALE:
            self._validate_stale()
        if (
            self.withdrawal_permission_status == WithdrawalPermissionStatus.ENABLED_REJECTED
            and VerificationReasonCode.WITHDRAWAL_PERMISSION_ENABLED not in self.reason_codes
        ):
            raise ValueError("withdrawal-enabled rejection requires its reason code")
        return self

    def _validate_ready(self) -> None:
        if self.verification_status != ConnectionVerificationStatus.VERIFIED:
            raise ValueError("ready connection must be verified")
        if self.availability_status != ConnectionAvailabilityStatus.AVAILABLE:
            raise ValueError("ready connection must be available")
        if self.trading_permission_status != TradingPermissionStatus.ENABLED:
            raise ValueError("ready connection must have trading permission enabled")
        if self.withdrawal_permission_status != WithdrawalPermissionStatus.DISABLED_CONFIRMED:
            raise ValueError("ready connection must confirm withdrawals disabled")
        if self.last_verified_at is None:
            raise ValueError("ready connection requires last_verified_at")

    def _validate_stale(self) -> None:
        if self.verification_status != ConnectionVerificationStatus.STALE:
            raise ValueError("stale product status requires stale verification status")
        if self.last_verified_at is None:
            raise ValueError("stale connection requires prior successful verification")


class ExchangeConnectionProduct(ContractModel):
    metadata: ExchangeConnectionMetadata
    capability_profile: ExchangeCapabilityProductProfile
    state: ExchangeConnectionState

    @model_validator(mode="after")
    def validate_product(self) -> Self:
        if self.metadata.tenant_id != self.state.tenant_id:
            raise ValueError("connection metadata and state tenant mismatch")
        if self.metadata.connection_id != self.state.connection_id:
            raise ValueError("connection metadata and state connection mismatch")
        if self.metadata.metadata_revision != self.state.metadata_revision:
            raise ValueError("connection metadata and state revision mismatch")
        if self.metadata.exchange_profile_ref != self.capability_profile.profile_ref:
            raise ValueError("connection metadata capability profile mismatch")
        if self.metadata.exchange_id != self.capability_profile.capability.exchange_id:
            raise ValueError("connection exchange does not match capability profile")
        return self


class VerificationProbeResult(ContractModel):
    verification_id: NonEmptyStr
    connection_id: NonEmptyStr
    tenant_id: NonEmptyStr
    metadata_revision: int = Field(gt=0)
    capability_profile_ref: NonEmptyStr
    exchange_available: bool
    trading_enabled: bool | None = None
    withdrawals_enabled: bool | None = None
    observed_at: UtcDateTime
    evidence_ref: NonEmptyStr

    @model_validator(mode="after")
    def validate_probe(self) -> Self:
        if not self.exchange_available:
            if self.trading_enabled is not None or self.withdrawals_enabled is not None:
                raise ValueError(
                    "unavailable exchange probe must not claim permission observations"
                )
        return self
