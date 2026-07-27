from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, PositiveInt, model_validator

from ai_platform.portal.contracts.bot_management.capabilities import (
    BotManagementCapability,
)
from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ExchangeCapabilityProfile,
)
from ai_platform.portal.contracts.bot_management.pagination import (
    MAX_PAGE_SIZE,
    PageInfo,
)
from ai_platform.portal.contracts.bot_management.templates import (
    BotFamily,
    BotTemplateVersion,
    CatalogVersionRef,
    MarketType,
    PolicyFamily,
    TradeDirection,
)
from ai_platform.portal.contracts.common import (
    ContractModel,
    NonEmptyStr,
    Sha256Hex,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import ExecutionMode

CatalogPageSize = Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)]


class CatalogEntryState(StrEnum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    UNAVAILABLE = "UNAVAILABLE"


class ModelRequirement(StrEnum):
    FORBIDDEN = "FORBIDDEN"
    OPTIONAL = "OPTIONAL"
    REQUIRED = "REQUIRED"


class CatalogAccessReasonCode(StrEnum):
    CAPABILITY_MISSING = "CAPABILITY_MISSING"
    CATALOG_NOT_FOUND = "CATALOG_NOT_FOUND"
    CURSOR_INVALID = "CURSOR_INVALID"
    TENANT_MISMATCH = "TENANT_MISMATCH"


def _validate_sorted_unique(field_name: str, values: tuple[str, ...]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    if list(values) != sorted(values):
        raise ValueError(f"{field_name} must use deterministic sorted order")


def _validate_catalog_entries(
    field_name: str,
    keys: tuple[tuple[str, ...], ...],
) -> None:
    if len(keys) != len(set(keys)):
        raise ValueError(f"{field_name} must not contain duplicate keys")
    if list(keys) != sorted(keys):
        raise ValueError(f"{field_name} must use deterministic sorted order")


class CatalogAccessContext(ContractModel):
    tenant_id: NonEmptyStr
    capabilities: tuple[BotManagementCapability, ...]

    @model_validator(mode="after")
    def validate_capabilities(self) -> Self:
        _validate_sorted_unique(
            "capabilities",
            tuple(capability.value for capability in self.capabilities),
        )
        return self


class CatalogTemplateEntry(ContractModel):
    template: BotTemplateVersion
    state: CatalogEntryState
    model_requirement: ModelRequirement
    sha256: Sha256Hex
    published_at: UtcDateTime

    @model_validator(mode="after")
    def validate_model_requirement(self) -> Self:
        supported_models = self.template.supported_model_versions
        if self.model_requirement == ModelRequirement.REQUIRED and not supported_models:
            raise ValueError("model-required template must declare supported model versions")
        if self.model_requirement == ModelRequirement.FORBIDDEN and supported_models:
            raise ValueError("model-forbidden template must not declare supported model versions")
        return self

    @property
    def catalog_ref(self) -> CatalogVersionRef:
        return CatalogVersionRef(
            catalog_id=self.template.template_id,
            version=str(self.template.revision),
        )


class StrategyCatalogEntry(ContractModel):
    strategy_id: NonEmptyStr
    version: NonEmptyStr
    state: CatalogEntryState
    sha256: Sha256Hex
    supported_market_types: Annotated[tuple[MarketType, ...], Field(min_length=1)]
    supported_directions: Annotated[tuple[TradeDirection, ...], Field(min_length=1)]
    supported_execution_modes: Annotated[tuple[ExecutionMode, ...], Field(min_length=1)]
    supported_model_versions: tuple[NonEmptyStr, ...] = ()
    supported_runtime_versions: Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]
    supported_risk_policy_versions: Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]
    supported_policy_families: Annotated[tuple[PolicyFamily, ...], Field(min_length=1)]
    published_at: UtcDateTime

    @model_validator(mode="after")
    def validate_compatibility_sets(self) -> Self:
        fields = {
            "supported_market_types": tuple(item.value for item in self.supported_market_types),
            "supported_directions": tuple(item.value for item in self.supported_directions),
            "supported_execution_modes": tuple(
                item.value for item in self.supported_execution_modes
            ),
            "supported_model_versions": self.supported_model_versions,
            "supported_runtime_versions": self.supported_runtime_versions,
            "supported_risk_policy_versions": self.supported_risk_policy_versions,
            "supported_policy_families": tuple(
                item.value for item in self.supported_policy_families
            ),
        }
        for field_name, values in fields.items():
            _validate_sorted_unique(field_name, values)
        return self


class ModelCatalogEntry(ContractModel):
    model_id: NonEmptyStr
    version: NonEmptyStr
    state: CatalogEntryState
    sha256: Sha256Hex
    compatible_strategy_versions: Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]
    supported_runtime_versions: Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]
    published_at: UtcDateTime

    @model_validator(mode="after")
    def validate_compatibility_sets(self) -> Self:
        _validate_sorted_unique(
            "compatible_strategy_versions",
            self.compatible_strategy_versions,
        )
        _validate_sorted_unique(
            "supported_runtime_versions",
            self.supported_runtime_versions,
        )
        return self


class ExchangeProfileCatalogEntry(ContractModel):
    version: NonEmptyStr
    state: CatalogEntryState
    profile: ExchangeCapabilityProfile
    sha256: Sha256Hex
    published_at: UtcDateTime


class RuntimeCatalogEntry(ContractModel):
    runtime_id: NonEmptyStr
    version: NonEmptyStr
    state: CatalogEntryState
    sha256: Sha256Hex
    supported_market_types: Annotated[tuple[MarketType, ...], Field(min_length=1)]
    supported_execution_modes: Annotated[tuple[ExecutionMode, ...], Field(min_length=1)]
    published_at: UtcDateTime

    @model_validator(mode="after")
    def validate_compatibility_sets(self) -> Self:
        _validate_sorted_unique(
            "supported_market_types",
            tuple(item.value for item in self.supported_market_types),
        )
        _validate_sorted_unique(
            "supported_execution_modes",
            tuple(item.value for item in self.supported_execution_modes),
        )
        return self


class RiskPolicyCatalogEntry(ContractModel):
    risk_policy_id: NonEmptyStr
    version: NonEmptyStr
    state: CatalogEntryState
    sha256: Sha256Hex
    supported_market_types: Annotated[tuple[MarketType, ...], Field(min_length=1)]
    supported_execution_modes: Annotated[tuple[ExecutionMode, ...], Field(min_length=1)]
    supported_policy_families: Annotated[tuple[PolicyFamily, ...], Field(min_length=1)]
    published_at: UtcDateTime

    @model_validator(mode="after")
    def validate_compatibility_sets(self) -> Self:
        _validate_sorted_unique(
            "supported_market_types",
            tuple(item.value for item in self.supported_market_types),
        )
        _validate_sorted_unique(
            "supported_execution_modes",
            tuple(item.value for item in self.supported_execution_modes),
        )
        _validate_sorted_unique(
            "supported_policy_families",
            tuple(item.value for item in self.supported_policy_families),
        )
        return self


class BotCatalogSnapshot(ContractModel):
    catalog_id: NonEmptyStr
    revision: PositiveInt
    published_at: UtcDateTime
    templates: Annotated[tuple[CatalogTemplateEntry, ...], Field(min_length=1)]
    strategies: Annotated[tuple[StrategyCatalogEntry, ...], Field(min_length=1)]
    models: tuple[ModelCatalogEntry, ...] = ()
    exchange_profiles: Annotated[tuple[ExchangeProfileCatalogEntry, ...], Field(min_length=1)]
    runtimes: Annotated[tuple[RuntimeCatalogEntry, ...], Field(min_length=1)]
    risk_policies: Annotated[tuple[RiskPolicyCatalogEntry, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_catalog_order(self) -> Self:
        keyed_fields = {
            "templates": tuple(
                (entry.template.template_id, str(entry.template.revision))
                for entry in self.templates
            ),
            "strategies": tuple((entry.version,) for entry in self.strategies),
            "models": tuple((entry.version,) for entry in self.models),
            "exchange_profiles": tuple((entry.version,) for entry in self.exchange_profiles),
            "runtimes": tuple((entry.version,) for entry in self.runtimes),
            "risk_policies": tuple((entry.version,) for entry in self.risk_policies),
        }
        for field_name, keys in keyed_fields.items():
            _validate_catalog_entries(field_name, keys)
        return self

    @property
    def catalog_ref(self) -> CatalogVersionRef:
        return CatalogVersionRef(catalog_id=self.catalog_id, version=str(self.revision))


class CatalogTemplateFilters(ContractModel):
    query: NonEmptyStr | None = None
    bot_families: tuple[BotFamily, ...] = ()
    market_types: tuple[MarketType, ...] = ()
    execution_modes: tuple[ExecutionMode, ...] = ()
    states: tuple[CatalogEntryState, ...] = (CatalogEntryState.ACTIVE,)

    @model_validator(mode="after")
    def validate_filters(self) -> Self:
        fields = {
            "bot_families": tuple(item.value for item in self.bot_families),
            "market_types": tuple(item.value for item in self.market_types),
            "execution_modes": tuple(item.value for item in self.execution_modes),
            "states": tuple(item.value for item in self.states),
        }
        for field_name, values in fields.items():
            _validate_sorted_unique(field_name, values)
        return self


class CatalogPageRequest(ContractModel):
    page_size: CatalogPageSize = 50
    cursor: NonEmptyStr | None = None


class TemplateCatalogPage(ContractModel):
    catalog_ref: CatalogVersionRef
    items: tuple[CatalogTemplateEntry, ...]
    page_info: PageInfo

    @model_validator(mode="after")
    def validate_page(self) -> Self:
        if len(self.items) != self.page_info.result_count:
            raise ValueError("template item count must match page info")
        keys = tuple(
            (item.template.template_id, str(item.template.revision)) for item in self.items
        )
        _validate_catalog_entries("items", keys)
        return self
