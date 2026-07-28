from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self

from pydantic import model_validator

from ai_platform.portal.contracts.bot_management.pagination import (
    BotManagementListFilters,
    BoundedPagination,
    PageInfo,
)
from ai_platform.portal.contracts.bots import BotDesiredState, BotObservedState
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment, ExecutionMode


class DashboardEvidenceSource(StrEnum):
    CONTROL_PLANE = "CONTROL_PLANE"
    RUNTIME = "RUNTIME"
    VALUATION = "VALUATION"
    MODEL = "MODEL"
    RISK = "RISK"


class DashboardEvidenceState(StrEnum):
    CURRENT = "CURRENT"
    ATTENTION = "ATTENTION"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DashboardEvidenceStatus(ContractModel):
    source: DashboardEvidenceSource
    state: DashboardEvidenceState
    observed_at: UtcDateTime | None = None
    reason_codes: tuple[NonEmptyStr, ...] = ()

    @model_validator(mode="after")
    def validate_reason_codes(self) -> Self:
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("dashboard evidence reason codes must be unique")
        if list(self.reason_codes) != sorted(self.reason_codes):
            raise ValueError("dashboard evidence reason codes must use deterministic order")
        return self


class BotDashboardEvidence(ContractModel):
    runtime: DashboardEvidenceStatus
    valuation: DashboardEvidenceStatus
    model: DashboardEvidenceStatus

    @model_validator(mode="after")
    def validate_sources(self) -> Self:
        expected = {
            DashboardEvidenceSource.RUNTIME,
            DashboardEvidenceSource.VALUATION,
            DashboardEvidenceSource.MODEL,
        }
        actual = {self.runtime.source, self.valuation.source, self.model.source}
        if actual != expected:
            raise ValueError("bot dashboard evidence sources are invalid")
        return self


class BotDashboardItem(ContractModel):
    bot_id: NonEmptyStr
    name: NonEmptyStr
    environment: Environment
    execution_mode: ExecutionMode
    desired_state: BotDesiredState
    observed_state: BotObservedState
    config_revision: int
    strategy_version: NonEmptyStr
    model_version: NonEmptyStr
    risk_policy_version: NonEmptyStr
    open_position_count: int
    open_order_count: int
    runtime_trade_count: int
    realized_net_pnl: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    evidence: BotDashboardEvidence
    requires_attention: bool
    attention_reasons: tuple[NonEmptyStr, ...] = ()

    @model_validator(mode="after")
    def validate_item(self) -> Self:
        for field_name in (
            "config_revision",
            "open_position_count",
            "open_order_count",
            "runtime_trade_count",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be non-negative")
        if len(self.attention_reasons) != len(set(self.attention_reasons)):
            raise ValueError("attention reasons must be unique")
        if list(self.attention_reasons) != sorted(self.attention_reasons):
            raise ValueError("attention reasons must use deterministic order")
        if self.requires_attention != bool(self.attention_reasons):
            raise ValueError("requires_attention must agree with attention reasons")
        return self


class DashboardTotals(ContractModel):
    matching_bot_count: int
    active_bot_count: int
    attention_bot_count: int
    open_position_count: int
    open_order_count: int
    runtime_trade_count: int
    risk_decision_count: int
    realized_net_pnl: Decimal | None = None
    unrealized_pnl: Decimal | None = None

    @model_validator(mode="after")
    def validate_totals(self) -> Self:
        for field_name in (
            "matching_bot_count",
            "active_bot_count",
            "attention_bot_count",
            "open_position_count",
            "open_order_count",
            "runtime_trade_count",
            "risk_decision_count",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be non-negative")
        if self.active_bot_count > self.matching_bot_count:
            raise ValueError("active bot count must not exceed matching bot count")
        if self.attention_bot_count > self.matching_bot_count:
            raise ValueError("attention bot count must not exceed matching bot count")
        return self


class DashboardSearchRequest(ContractModel):
    filters: BotManagementListFilters
    page: BoundedPagination


class BotDashboardPage(ContractModel):
    schema_version: Literal[1] = 1
    generated_at: UtcDateTime
    filters: BotManagementListFilters
    items: tuple[BotDashboardItem, ...]
    page_info: PageInfo
    totals: DashboardTotals
    source_statuses: tuple[DashboardEvidenceStatus, ...]

    @model_validator(mode="after")
    def validate_page(self) -> Self:
        if len(self.items) != self.page_info.result_count:
            raise ValueError("dashboard item count must match page info")
        bot_ids = tuple(item.bot_id for item in self.items)
        if len(bot_ids) != len(set(bot_ids)):
            raise ValueError("dashboard items must use unique bot identities")
        sources = tuple(status.source.value for status in self.source_statuses)
        if sources != tuple(sorted(sources)):
            raise ValueError("dashboard source statuses must use deterministic order")
        if len(sources) != len(set(sources)):
            raise ValueError("dashboard source statuses must use unique sources")
        return self
