from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, PositiveInt, model_validator

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.policies import GridSpacing, PositiveDecimal
from ai_platform.portal.contracts.bot_management.templates import MarginMode, TradeDirection
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.identity import Actor


class EvidenceFreshness(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"


class GridControlContext(ContractModel):
    tenant_id: NonEmptyStr
    actor: Actor
    capabilities: tuple[BotManagementCapability, ...]

    @model_validator(mode="after")
    def validate_context(self) -> Self:
        if self.actor.tenant_id != self.tenant_id:
            raise ValueError("grid context actor must belong to the context tenant")
        values = [item.value for item in self.capabilities]
        if len(values) != len(set(values)) or values != sorted(values):
            raise ValueError("grid context capabilities must be unique and sorted")
        return self


class GridTemplateCapabilityEvidence(ContractModel):
    tenant_id: NonEmptyStr
    template_id: NonEmptyStr
    template_revision: PositiveInt
    supported_spacings: Annotated[tuple[GridSpacing, ...], Field(min_length=1)]
    supported_directions: Annotated[tuple[TradeDirection, ...], Field(min_length=1)]
    maximum_level_count: Annotated[int, Field(ge=2, le=200)]
    supports_trailing_grid: bool = False
    supports_take_profit: bool = False
    supports_stop_loss: bool = False
    supports_leverage: bool = False
    supports_margin: bool = False
    freshness: EvidenceFreshness
    observed_at: UtcDateTime

    @model_validator(mode="after")
    def validate_sets(self) -> Self:
        fields = (
            ("supported_spacings", tuple(item.value for item in self.supported_spacings)),
            ("supported_directions", tuple(item.value for item in self.supported_directions)),
        )
        for name, values in fields:
            if len(values) != len(set(values)) or list(values) != sorted(values):
                raise ValueError(f"{name} must be unique and sorted")
        return self


class GridExchangeCapabilityEvidence(ContractModel):
    tenant_id: NonEmptyStr
    profile_id: NonEmptyStr
    profile_revision: PositiveInt
    price_step: PositiveDecimal
    quantity_step: PositiveDecimal
    minimum_amount: PositiveDecimal
    minimum_notional: PositiveDecimal
    supports_short: bool
    supported_margin_modes: tuple[MarginMode, ...] = ()
    maximum_leverage: PositiveDecimal | None = None
    supports_trailing_grid: bool = False
    supports_take_profit: bool = False
    supports_stop_loss: bool = False
    freshness: EvidenceFreshness
    observed_at: UtcDateTime

    @model_validator(mode="after")
    def validate_margin_modes(self) -> Self:
        values = [item.value for item in self.supported_margin_modes]
        if len(values) != len(set(values)) or values != sorted(values):
            raise ValueError("supported_margin_modes must be unique and sorted")
        return self
