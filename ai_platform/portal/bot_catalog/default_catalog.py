from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256

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
from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ExchangeCapabilityProfile,
)
from ai_platform.portal.contracts.bot_management.policies import OrderType
from ai_platform.portal.contracts.bot_management.templates import (
    BotFamily,
    BotTemplateVersion,
    MarketType,
    PolicyFamily,
    TradeDirection,
)
from ai_platform.portal.contracts.common import ContractModel
from ai_platform.portal.contracts.environment import ExecutionMode


PUBLISHED_AT = datetime(2026, 7, 28, 8, 24, 26, tzinfo=UTC)
REQUIRED_POLICIES = (
    PolicyFamily.ENTRY,
    PolicyFamily.EXIT,
    PolicyFamily.MARKET,
    PolicyFamily.POSITION_SIZING,
    PolicyFamily.RISK_REFERENCE,
    PolicyFamily.RUNTIME,
)


def _digest(value: ContractModel | dict[str, object]) -> str:
    if isinstance(value, ContractModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def approved_dry_run_catalog() -> BotCatalogSnapshot:
    """Return the immutable starter catalog already represented by portal product fixtures."""

    template = BotTemplateVersion(
        template_id="ai-directional-dry-run",
        revision=1,
        display_name="AI Directional Dry Run",
        bot_family=BotFamily.DIRECTIONAL,
        supported_strategy_versions=("ai-directional-v1",),
        supported_model_versions=("model-validated-2026-07",),
        supported_exchange_profile_versions=("simulated-spot-v1",),
        supported_market_types=(MarketType.SPOT,),
        supported_directions=(TradeDirection.LONG,),
        supported_execution_modes=(ExecutionMode.DRY_RUN,),
        required_policy_families=REQUIRED_POLICIES,
        optional_policy_families=(),
        created_at=PUBLISHED_AT,
    )
    exchange_profile = ExchangeCapabilityProfile(
        profile_id="simulated-spot",
        revision=1,
        exchange_id="simulated",
        market_types=(MarketType.SPOT,),
        order_types=(OrderType.LIMIT, OrderType.MARKET),
        supports_order_replace=True,
        supports_short=False,
        supports_subaccounts=False,
    )

    return BotCatalogSnapshot(
        catalog_id="portal-approved-dry-run",
        revision=1,
        published_at=PUBLISHED_AT,
        templates=(
            CatalogTemplateEntry(
                template=template,
                state=CatalogEntryState.ACTIVE,
                model_requirement=ModelRequirement.REQUIRED,
                sha256=_digest(template),
                published_at=PUBLISHED_AT,
            ),
        ),
        strategies=(
            StrategyCatalogEntry(
                strategy_id="ai-directional",
                version="ai-directional-v1",
                state=CatalogEntryState.ACTIVE,
                sha256=_digest(
                    {
                        "strategy_id": "ai-directional",
                        "version": "ai-directional-v1",
                    }
                ),
                supported_market_types=(MarketType.SPOT,),
                supported_directions=(TradeDirection.LONG,),
                supported_execution_modes=(ExecutionMode.DRY_RUN,),
                supported_model_versions=("model-validated-2026-07",),
                supported_runtime_versions=("freqtrade-2026.7",),
                supported_risk_policy_versions=("risk-default-v1",),
                supported_policy_families=REQUIRED_POLICIES,
                published_at=PUBLISHED_AT,
            ),
        ),
        models=(
            ModelCatalogEntry(
                model_id="model-validated",
                version="model-validated-2026-07",
                state=CatalogEntryState.ACTIVE,
                sha256=_digest(
                    {
                        "model_id": "model-validated",
                        "version": "model-validated-2026-07",
                    }
                ),
                compatible_strategy_versions=("ai-directional-v1",),
                supported_runtime_versions=("freqtrade-2026.7",),
                published_at=PUBLISHED_AT,
            ),
        ),
        exchange_profiles=(
            ExchangeProfileCatalogEntry(
                version="simulated-spot-v1",
                state=CatalogEntryState.ACTIVE,
                profile=exchange_profile,
                sha256=_digest(exchange_profile),
                published_at=PUBLISHED_AT,
            ),
        ),
        runtimes=(
            RuntimeCatalogEntry(
                runtime_id="freqtrade",
                version="freqtrade-2026.7",
                state=CatalogEntryState.ACTIVE,
                sha256=_digest(
                    {
                        "runtime_id": "freqtrade",
                        "version": "freqtrade-2026.7",
                        "execution_mode": "dry_run",
                    }
                ),
                supported_market_types=(MarketType.SPOT,),
                supported_execution_modes=(ExecutionMode.DRY_RUN,),
                published_at=PUBLISHED_AT,
            ),
        ),
        risk_policies=(
            RiskPolicyCatalogEntry(
                risk_policy_id="risk-default",
                version="risk-default-v1",
                state=CatalogEntryState.ACTIVE,
                sha256=_digest(
                    {
                        "risk_policy_id": "risk-default",
                        "version": "risk-default-v1",
                    }
                ),
                supported_market_types=(MarketType.SPOT,),
                supported_execution_modes=(ExecutionMode.DRY_RUN,),
                supported_policy_families=REQUIRED_POLICIES,
                published_at=PUBLISHED_AT,
            ),
        ),
    )
