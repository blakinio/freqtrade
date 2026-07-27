from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ai_platform.portal.bot_catalog.repository import InMemoryBotCatalogRepository
from ai_platform.portal.bot_catalog.schema import (
    BotCatalogSnapshot,
    CatalogAccessContext,
    CatalogEntryState,
    CatalogTemplateEntry,
    ExchangeProfileCatalogEntry,
    ModelCatalogEntry,
    ModelRequirement,
    RiskPolicyCatalogEntry,
    RuntimeCatalogEntry,
    StrategyCatalogEntry,
)
from ai_platform.portal.bot_catalog.service import BotCatalogService
from ai_platform.portal.contracts.bot_management.capabilities import (
    BotManagementCapability,
)
from ai_platform.portal.contracts.bot_management.compatibility import (
    CompatibilitySelection,
)
from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ExchangeCapabilityProfile,
)
from ai_platform.portal.contracts.bot_management.policies import OrderType
from ai_platform.portal.contracts.bot_management.templates import (
    BotFamily,
    BotTemplateVersion,
    CatalogVersionRef,
    MarketType,
    PolicyFamily,
    TradeDirection,
)
from ai_platform.portal.contracts.environment import ExecutionMode

NOW = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)
POLICIES = (
    PolicyFamily.ENTRY,
    PolicyFamily.EXIT,
    PolicyFamily.MARKET,
    PolicyFamily.POSITION_SIZING,
    PolicyFamily.RISK_REFERENCE,
    PolicyFamily.RUNTIME,
)


def template_entry(
    template_id: str = "directional-v1",
    *,
    revision: int = 1,
    display_name: str = "Directional Dry Run",
    state: CatalogEntryState = CatalogEntryState.ACTIVE,
    model_requirement: ModelRequirement = ModelRequirement.OPTIONAL,
    bot_family: BotFamily = BotFamily.DIRECTIONAL,
) -> CatalogTemplateEntry:
    model_versions = () if model_requirement == ModelRequirement.FORBIDDEN else ("model-v1",)
    return CatalogTemplateEntry(
        template=BotTemplateVersion(
            template_id=template_id,
            revision=revision,
            display_name=display_name,
            bot_family=bot_family,
            supported_strategy_versions=("strat-v1",),
            supported_model_versions=model_versions,
            supported_exchange_profile_versions=("okx-spot-v1",),
            supported_market_types=(MarketType.SPOT,),
            supported_directions=(TradeDirection.LONG,),
            supported_execution_modes=(ExecutionMode.DRY_RUN,),
            required_policy_families=POLICIES,
            optional_policy_families=(),
            created_at=NOW,
        ),
        state=state,
        model_requirement=model_requirement,
        sha256="a" * 64,
        published_at=NOW,
    )


def snapshot_with_templates(
    templates: tuple[CatalogTemplateEntry, ...],
    *,
    revision: int = 1,
    strategy_state: CatalogEntryState = CatalogEntryState.ACTIVE,
    model_state: CatalogEntryState = CatalogEntryState.ACTIVE,
) -> BotCatalogSnapshot:
    return BotCatalogSnapshot(
        catalog_id="approved-bots",
        revision=revision,
        published_at=NOW,
        templates=templates,
        strategies=(
            StrategyCatalogEntry(
                strategy_id="directional-strategy",
                version="strat-v1",
                state=strategy_state,
                sha256="b" * 64,
                supported_market_types=(MarketType.SPOT,),
                supported_directions=(TradeDirection.LONG,),
                supported_execution_modes=(ExecutionMode.DRY_RUN,),
                supported_model_versions=("model-v1",),
                supported_runtime_versions=("runtime-v1",),
                supported_risk_policy_versions=("risk-v1",),
                supported_policy_families=POLICIES,
                published_at=NOW,
            ),
        ),
        models=(
            ModelCatalogEntry(
                model_id="baseline-model",
                version="model-v1",
                state=model_state,
                sha256="c" * 64,
                compatible_strategy_versions=("strat-v1",),
                supported_runtime_versions=("runtime-v1",),
                published_at=NOW,
            ),
        ),
        exchange_profiles=(
            ExchangeProfileCatalogEntry(
                version="okx-spot-v1",
                state=CatalogEntryState.ACTIVE,
                profile=ExchangeCapabilityProfile(
                    profile_id="okx-spot",
                    revision=1,
                    exchange_id="okx",
                    market_types=(MarketType.SPOT,),
                    order_types=(OrderType.LIMIT, OrderType.MARKET),
                    supports_order_replace=True,
                    supports_short=False,
                    supports_subaccounts=True,
                ),
                sha256="d" * 64,
                published_at=NOW,
            ),
        ),
        runtimes=(
            RuntimeCatalogEntry(
                runtime_id="freqtrade-runtime",
                version="runtime-v1",
                state=CatalogEntryState.ACTIVE,
                sha256="e" * 64,
                supported_market_types=(MarketType.SPOT,),
                supported_execution_modes=(ExecutionMode.DRY_RUN,),
                published_at=NOW,
            ),
        ),
        risk_policies=(
            RiskPolicyCatalogEntry(
                risk_policy_id="portal-risk",
                version="risk-v1",
                state=CatalogEntryState.ACTIVE,
                sha256="f" * 64,
                supported_market_types=(MarketType.SPOT,),
                supported_execution_modes=(ExecutionMode.DRY_RUN,),
                supported_policy_families=POLICIES,
                published_at=NOW,
            ),
        ),
    )


@pytest.fixture
def snapshot() -> BotCatalogSnapshot:
    return snapshot_with_templates((template_entry(),))


@pytest.fixture
def access() -> CatalogAccessContext:
    return CatalogAccessContext(
        tenant_id="tenant-a",
        capabilities=(
            BotManagementCapability.CATALOG_READ,
            BotManagementCapability.TEMPLATE_READ,
        ),
    )


@pytest.fixture
def service(snapshot: BotCatalogSnapshot) -> BotCatalogService:
    return BotCatalogService(InMemoryBotCatalogRepository((snapshot,)))


@pytest.fixture
def selection() -> CompatibilitySelection:
    return CompatibilitySelection(
        tenant_id="tenant-a",
        template_ref=CatalogVersionRef(catalog_id="directional-v1", version="1"),
        strategy_version="strat-v1",
        model_version="model-v1",
        exchange_profile_version="okx-spot-v1",
        market_type=MarketType.SPOT,
        direction=TradeDirection.LONG,
        execution_mode=ExecutionMode.DRY_RUN,
        runtime_version="runtime-v1",
        risk_policy_version="risk-v1",
        policy_families=POLICIES,
    )
