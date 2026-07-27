from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from ai_platform.portal.bot_builder.repository import InMemoryBotConfigurationRepository
from ai_platform.portal.bot_builder.schema import (
    BotBuilderAccessContext,
    BotConfigurationDraftPayload,
)
from ai_platform.portal.bot_builder.service import BotConfigurationBuilderService
from ai_platform.portal.bot_catalog.repository import InMemoryBotCatalogRepository
from ai_platform.portal.bot_catalog.schema import (
    BotCatalogSnapshot,
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
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ExchangeCapabilityProfile,
)
from ai_platform.portal.contracts.bot_management.policies import (
    DcaPolicyVersion,
    DcaSizeMode,
    DcaStep,
    DcaTriggerBasis,
    EntryPolicyVersion,
    ExitPolicyVersion,
    GridAllocationMode,
    GridPolicyVersion,
    GridSpacing,
    MarketPolicyVersion,
    OrderType,
    PositionSizingMode,
    PositionSizingPolicyVersion,
    RuntimePolicyVersion,
    SignalAuthority,
    SignalCommand,
    SignalPolicyVersion,
    StopLossPolicy,
)
from ai_platform.portal.contracts.bot_management.templates import (
    BotFamily,
    BotTemplateVersion,
    CatalogVersionRef,
    MarketType,
    PolicyFamily,
    TradeDirection,
)
from ai_platform.portal.contracts.environment import Environment, ExecutionMode


NOW = datetime(2026, 7, 27, 15, 30, tzinfo=UTC)
BASE_POLICIES = (
    PolicyFamily.ENTRY,
    PolicyFamily.EXIT,
    PolicyFamily.MARKET,
    PolicyFamily.POSITION_SIZING,
    PolicyFamily.RISK_REFERENCE,
    PolicyFamily.RUNTIME,
)
OPTIONAL_POLICIES = (
    PolicyFamily.DCA,
    PolicyFamily.GRID,
    PolicyFamily.SIGNAL,
)
ALL_POLICIES = tuple(sorted((*BASE_POLICIES, *OPTIONAL_POLICIES), key=lambda item: item.value))
CAPABILITIES = tuple(
    sorted(
        (
            BotManagementCapability.BOT_CREATE,
            BotManagementCapability.BOT_REVISE,
            BotManagementCapability.CATALOG_READ,
            BotManagementCapability.TEMPLATE_READ,
        ),
        key=lambda item: item.value,
    )
)


def builder_access(*capabilities: BotManagementCapability) -> BotBuilderAccessContext:
    selected = capabilities or CAPABILITIES
    return BotBuilderAccessContext(
        tenant_id="tenant-a",
        actor_id="actor-a",
        capabilities=tuple(sorted(selected, key=lambda item: item.value)),
    )


def template_entry(
    *,
    model_requirement: ModelRequirement = ModelRequirement.OPTIONAL,
) -> CatalogTemplateEntry:
    return CatalogTemplateEntry(
        template=BotTemplateVersion(
            template_id="directional-v1",
            revision=1,
            display_name="Directional Dry Run",
            bot_family=BotFamily.DIRECTIONAL,
            supported_strategy_versions=("strat-v1",),
            supported_model_versions=("model-v1",),
            supported_exchange_profile_versions=("okx-spot-v1",),
            supported_market_types=(MarketType.SPOT,),
            supported_directions=(TradeDirection.LONG,),
            supported_execution_modes=(ExecutionMode.DRY_RUN,),
            required_policy_families=BASE_POLICIES,
            optional_policy_families=OPTIONAL_POLICIES,
            created_at=NOW,
        ),
        state=CatalogEntryState.ACTIVE,
        model_requirement=model_requirement,
        sha256="a" * 64,
        published_at=NOW,
    )


def build_snapshot(
    *,
    model_requirement: ModelRequirement = ModelRequirement.OPTIONAL,
) -> BotCatalogSnapshot:
    return BotCatalogSnapshot(
        catalog_id="approved-bots",
        revision=1,
        published_at=NOW,
        templates=(template_entry(model_requirement=model_requirement),),
        strategies=(
            StrategyCatalogEntry(
                strategy_id="directional-strategy",
                version="strat-v1",
                state=CatalogEntryState.ACTIVE,
                sha256="b" * 64,
                supported_market_types=(MarketType.SPOT,),
                supported_directions=(TradeDirection.LONG,),
                supported_execution_modes=(ExecutionMode.DRY_RUN,),
                supported_model_versions=("model-v1",),
                supported_runtime_versions=("runtime-v1",),
                supported_risk_policy_versions=("risk-v1",),
                supported_policy_families=ALL_POLICIES,
                published_at=NOW,
            ),
        ),
        models=(
            ModelCatalogEntry(
                model_id="baseline-model",
                version="model-v1",
                state=CatalogEntryState.ACTIVE,
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
                supported_policy_families=ALL_POLICIES,
                published_at=NOW,
            ),
        ),
    )


def build_service(
    *,
    model_requirement: ModelRequirement = ModelRequirement.OPTIONAL,
) -> tuple[BotConfigurationBuilderService, InMemoryBotConfigurationRepository]:
    repository = InMemoryBotConfigurationRepository()
    catalog = BotCatalogService(
        InMemoryBotCatalogRepository((build_snapshot(model_requirement=model_requirement),))
    )
    return BotConfigurationBuilderService(repository, catalog), repository


def market_policy(policy_id: str = "market-v1") -> MarketPolicyVersion:
    return MarketPolicyVersion(
        policy_id=policy_id,
        revision=1,
        pairs=("BTC/USDT",),
        market_type=MarketType.SPOT,
        direction=TradeDirection.LONG,
        timeframe="5m",
    )


def entry_policy(policy_id: str = "entry-v1") -> EntryPolicyVersion:
    return EntryPolicyVersion(
        policy_id=policy_id,
        revision=1,
        order_type=OrderType.MARKET,
        max_concurrent_positions=2,
    )


def sizing_policy(policy_id: str = "sizing-v1") -> PositionSizingPolicyVersion:
    return PositionSizingPolicyVersion(
        policy_id=policy_id,
        revision=1,
        mode=PositionSizingMode.FIXED_QUOTE_AMOUNT,
        fixed_quote_amount=Decimal("100"),
        max_per_pair_allocation_percent=Decimal("10"),
        max_total_allocation_percent=Decimal("25"),
    )


def exit_policy(policy_id: str = "exit-v1") -> ExitPolicyVersion:
    return ExitPolicyVersion(
        policy_id=policy_id,
        revision=1,
        stop_loss=StopLossPolicy(loss_percent=Decimal("5")),
        strategy_exit_enabled=True,
    )


def runtime_policy(
    policy_id: str = "runtime-policy-v1",
    *,
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN,
) -> RuntimePolicyVersion:
    return RuntimePolicyVersion(
        policy_id=policy_id,
        revision=1,
        runtime_version="runtime-v1",
        execution_mode=execution_mode,
        heartbeat_timeout_seconds=30,
        command_timeout_seconds=10,
        reconciliation_timeout_seconds=60,
    )


def dca_policy(policy_id: str = "dca-v1") -> DcaPolicyVersion:
    return DcaPolicyVersion(
        policy_id=policy_id,
        revision=1,
        trigger_basis=DcaTriggerBasis.PRICE_DEVIATION_PERCENT,
        size_mode=DcaSizeMode.FIXED_QUOTE_AMOUNT,
        max_steps=1,
        max_cumulative_allocation_percent=Decimal("20"),
        steps=(
            DcaStep(
                step_number=1,
                trigger_deviation_percent=Decimal("3"),
                size_value=Decimal("50"),
            ),
        ),
    )


def grid_policy(policy_id: str = "grid-v1") -> GridPolicyVersion:
    return GridPolicyVersion(
        policy_id=policy_id,
        revision=1,
        lower_price=Decimal("90000"),
        upper_price=Decimal("100000"),
        level_count=5,
        spacing=GridSpacing.ARITHMETIC,
        allocation_mode=GridAllocationMode.TOTAL_QUOTE,
        total_quote_allocation=Decimal("500"),
        direction=TradeDirection.LONG,
    )


def signal_policy(policy_id: str = "signal-v1") -> SignalPolicyVersion:
    return SignalPolicyVersion(
        policy_id=policy_id,
        revision=1,
        signal_schema_ref="signal-schema-v1",
        allowed_commands=(SignalCommand.DCA, SignalCommand.OPEN),
        authority=SignalAuthority.ADVISORY_ONLY,
        max_signal_age_seconds=300,
        replay_window_seconds=60,
    )


def complete_payload(
    *,
    model_version: str | None = "model-v1",
    market: MarketPolicyVersion | None = None,
    entry: EntryPolicyVersion | None = None,
    sizing: PositionSizingPolicyVersion | None = None,
    exit_: ExitPolicyVersion | None = None,
    runtime: RuntimePolicyVersion | None = None,
    dca: DcaPolicyVersion | None = None,
    grid: GridPolicyVersion | None = None,
    signal: SignalPolicyVersion | None = None,
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN,
) -> BotConfigurationDraftPayload:
    return BotConfigurationDraftPayload(
        catalog_ref=CatalogVersionRef(catalog_id="approved-bots", version="1"),
        template_ref=CatalogVersionRef(catalog_id="directional-v1", version="1"),
        strategy_version="strat-v1",
        model_version=model_version,
        exchange_connection_ref="connection-okx-main",
        exchange_profile_version="okx-spot-v1",
        market_policy=market or market_policy(),
        entry_policy=entry or entry_policy(),
        position_sizing_policy=sizing or sizing_policy(),
        dca_policy=dca,
        exit_policy=exit_ or exit_policy(),
        risk_policy_version="risk-v1",
        signal_policy=signal,
        grid_policy=grid,
        runtime_policy=runtime or runtime_policy(execution_mode=execution_mode),
        environment=Environment.STAGING,
        execution_mode=execution_mode,
    )
