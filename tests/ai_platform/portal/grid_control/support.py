from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.policies import (
    GridAllocationMode,
    GridPolicyVersion,
    GridSpacing,
)
from ai_platform.portal.contracts.bot_management.templates import MarginMode, TradeDirection
from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.contracts.identity import Actor, ActorType
from ai_platform.portal.grid_control.evidence import (
    EvidenceFreshness,
    GridControlContext,
    GridExchangeCapabilityEvidence,
    GridTemplateCapabilityEvidence,
)
from ai_platform.portal.grid_control.repository import InMemoryGridControlRepository
from ai_platform.portal.grid_control.schema import GridPreviewRequest
from ai_platform.portal.grid_control.service import GridControlService


NOW = datetime(2026, 7, 28, 8, 0, tzinfo=UTC)


def clock() -> datetime:
    return NOW


def context() -> GridControlContext:
    return GridControlContext(
        tenant_id="tenant-a",
        actor=Actor(
            actor_id="user-1",
            tenant_id="tenant-a",
            actor_type=ActorType.USER,
        ),
        capabilities=(BotManagementCapability.GRID_CONFIGURE,),
    )


def policy() -> GridPolicyVersion:
    return GridPolicyVersion(
        policy_id="grid-policy",
        revision=1,
        lower_price=Decimal("90"),
        upper_price=Decimal("110"),
        level_count=5,
        spacing=GridSpacing.ARITHMETIC,
        allocation_mode=GridAllocationMode.TOTAL_QUOTE,
        total_quote_allocation=Decimal("300"),
        direction=TradeDirection.LONG,
    )


def request() -> GridPreviewRequest:
    return GridPreviewRequest(
        tenant_id="tenant-a",
        bot_id="bot-1",
        bot_revision=3,
        config_revision=7,
        template_id="grid-template",
        template_revision=2,
        exchange_profile_id="exchange-profile",
        exchange_profile_revision=4,
        policy=policy(),
        available_quote=Decimal("500"),
        execution_mode=ExecutionMode.DRY_RUN,
    )


def template() -> GridTemplateCapabilityEvidence:
    return GridTemplateCapabilityEvidence(
        tenant_id="tenant-a",
        template_id="grid-template",
        template_revision=2,
        supported_spacings=(GridSpacing.ARITHMETIC, GridSpacing.GEOMETRIC),
        supported_directions=(TradeDirection.LONG, TradeDirection.SHORT),
        maximum_level_count=50,
        supports_trailing_grid=True,
        supports_take_profit=True,
        supports_stop_loss=True,
        supports_leverage=True,
        supports_margin=True,
        freshness=EvidenceFreshness.CURRENT,
        observed_at=NOW,
    )


def exchange() -> GridExchangeCapabilityEvidence:
    return GridExchangeCapabilityEvidence(
        tenant_id="tenant-a",
        profile_id="exchange-profile",
        profile_revision=4,
        price_step=Decimal("0.01"),
        quantity_step=Decimal("0.001"),
        minimum_amount=Decimal("0.001"),
        minimum_notional=Decimal("5"),
        supports_short=True,
        supported_margin_modes=(MarginMode.CROSS, MarginMode.ISOLATED),
        maximum_leverage=Decimal("20"),
        supports_trailing_grid=True,
        supports_take_profit=True,
        supports_stop_loss=True,
        freshness=EvidenceFreshness.CURRENT,
        observed_at=NOW,
    )


def service() -> GridControlService:
    return GridControlService(InMemoryGridControlRepository(), clock=clock)
