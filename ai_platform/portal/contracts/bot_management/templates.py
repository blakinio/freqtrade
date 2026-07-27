from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, PositiveInt, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import ExecutionMode


class BotFamily(StrEnum):
    DIRECTIONAL = "directional"
    DCA = "dca"
    SIGNAL = "signal"
    GRID = "grid"


class MarketType(StrEnum):
    SPOT = "spot"
    MARGIN = "margin"
    FUTURES = "futures"


class TradeDirection(StrEnum):
    LONG = "long"
    SHORT = "short"
    BOTH = "both"


class MarginMode(StrEnum):
    ISOLATED = "isolated"
    CROSS = "cross"


class PolicyFamily(StrEnum):
    MARKET = "market"
    ENTRY = "entry"
    POSITION_SIZING = "position_sizing"
    DCA = "dca"
    EXIT = "exit"
    SIGNAL = "signal"
    GRID = "grid"
    RUNTIME = "runtime"
    RISK_REFERENCE = "risk_reference"


class CatalogVersionRef(ContractModel):
    catalog_id: NonEmptyStr
    version: NonEmptyStr


class BotTemplateVersion(ContractModel):
    template_id: NonEmptyStr
    revision: PositiveInt
    display_name: NonEmptyStr
    bot_family: BotFamily
    supported_strategy_versions: Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]
    supported_model_versions: tuple[NonEmptyStr, ...] = ()
    supported_exchange_profile_versions: Annotated[
        tuple[NonEmptyStr, ...], Field(min_length=1)
    ]
    supported_market_types: Annotated[tuple[MarketType, ...], Field(min_length=1)]
    supported_directions: Annotated[tuple[TradeDirection, ...], Field(min_length=1)]
    supported_execution_modes: Annotated[tuple[ExecutionMode, ...], Field(min_length=1)]
    required_policy_families: Annotated[tuple[PolicyFamily, ...], Field(min_length=1)]
    optional_policy_families: tuple[PolicyFamily, ...] = ()
    created_at: UtcDateTime

    @model_validator(mode="after")
    def validate_template(self) -> Self:
        sortable_fields = {
            "supported_strategy_versions": self.supported_strategy_versions,
            "supported_model_versions": self.supported_model_versions,
            "supported_exchange_profile_versions": self.supported_exchange_profile_versions,
            "supported_market_types": tuple(item.value for item in self.supported_market_types),
            "supported_directions": tuple(item.value for item in self.supported_directions),
            "supported_execution_modes": tuple(
                item.value for item in self.supported_execution_modes
            ),
            "required_policy_families": tuple(
                item.value for item in self.required_policy_families
            ),
            "optional_policy_families": tuple(
                item.value for item in self.optional_policy_families
            ),
        }
        for field_name, values in sortable_fields.items():
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates")
            if list(values) != sorted(values):
                raise ValueError(f"{field_name} must use deterministic sorted order")
        required = set(self.required_policy_families)
        optional = set(self.optional_policy_families)
        if required & optional:
            raise ValueError("required and optional policy families must be disjoint")
        if PolicyFamily.RUNTIME not in required:
            raise ValueError("runtime policy must be required")
        if PolicyFamily.MARKET not in required:
            raise ValueError("market policy must be required")
        return self
