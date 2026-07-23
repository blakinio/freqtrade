from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from ai_platform.portal.contracts.common import ContractModel, CorrelationContext, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission, Role
from ai_platform.portal.contracts.risk import TradeSide


class SignalSource(StrEnum):
    MANUAL = "MANUAL"


class SignalEvent(ContractModel):
    signal_id: UUID
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    timeframe: NonEmptyStr
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    rationale: NonEmptyStr
    source: SignalSource
    created_by_actor_id: NonEmptyStr
    occurred_at: UtcDateTime
    context: CorrelationContext
    execution_authority: bool = False

    @model_validator(mode="after")
    def forbid_execution_authority(self) -> Self:
        if self.execution_authority:
            raise ValueError("signal evidence cannot grant execution authority")
        return self


class StrategyKind(StrEnum):
    DIRECTIONAL = "DIRECTIONAL"
    GRID = "GRID"


class StrategyRuntimeStatus(StrEnum):
    BOT_REFERENCE = "BOT_REFERENCE"
    PORTAL_CONFIG_ONLY = "PORTAL_CONFIG_ONLY"


class StrategyCatalogEntry(ContractModel):
    strategy_version: NonEmptyStr
    display_name: NonEmptyStr
    description: NonEmptyStr
    kind: StrategyKind
    allowed_execution_modes: tuple[ExecutionMode, ...]
    runtime_status: StrategyRuntimeStatus
    immutable: bool = True


class GridBotConfig(ContractModel):
    grid_config_id: UUID
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    pair: NonEmptyStr
    strategy_version: NonEmptyStr
    lower_price: Decimal = Field(gt=Decimal("0"))
    upper_price: Decimal = Field(gt=Decimal("0"))
    levels: int = Field(ge=2, le=200)
    quote_allocation: Decimal = Field(gt=Decimal("0"))
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime

    @model_validator(mode="after")
    def validate_grid_bounds(self) -> Self:
        if self.lower_price >= self.upper_price:
            raise ValueError("grid lower_price must be below upper_price")
        if self.execution_mode is not ExecutionMode.DRY_RUN:
            raise ValueError("grid bot configuration is restricted to dry_run")
        return self


class NotificationCategory(StrEnum):
    SIGNAL = "SIGNAL"
    RISK = "RISK"
    EXECUTION = "EXECUTION"


class NotificationSeverity(StrEnum):
    INFO = "INFO"
    ATTENTION = "ATTENTION"


class NotificationPreference(ContractModel):
    tenant_id: NonEmptyStr
    actor_id: NonEmptyStr
    in_app_enabled: bool = True
    signal_events: bool = True
    risk_events: bool = True
    execution_events: bool = True
    updated_at: UtcDateTime


class NotificationEntry(ContractModel):
    notification_id: NonEmptyStr
    tenant_id: NonEmptyStr
    category: NotificationCategory
    severity: NotificationSeverity
    summary: NonEmptyStr
    resource_type: NonEmptyStr
    resource_id: NonEmptyStr
    occurred_at: UtcDateTime


class ProfileSecurityView(ContractModel):
    tenant_id: NonEmptyStr
    actor_id: NonEmptyStr
    actor_type: ActorType
    permissions: tuple[Permission, ...]
    authentication_boundary: NonEmptyStr
    mfa_status: NonEmptyStr
    session_management: NonEmptyStr
    secrets_exposed: bool = False


class AdministrationOverview(ContractModel):
    tenant_id: NonEmptyStr
    current_actor_id: NonEmptyStr
    current_permissions: tuple[Permission, ...]
    builtin_roles: tuple[Role, ...]
    membership_source: NonEmptyStr


class TelemetryAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class ModelHealthRecord(ContractModel):
    model_version_id: NonEmptyStr
    tenant_id: NonEmptyStr
    model_family_id: NonEmptyStr
    lifecycle_state: NonEmptyStr
    created_at: UtcDateTime
    training_window_end: UtcDateTime
    metadata_age_days: int = Field(ge=0)
    drift_status: TelemetryAvailability
    drift_reason: NonEmptyStr


class RuntimeLogAvailability(ContractModel):
    available: bool
    source: NonEmptyStr
    reason_code: NonEmptyStr
    checked_at: UtcDateTime


def utc_age_days(now: datetime, created_at: datetime) -> int:
    delta = now - created_at
    return max(delta.days, 0)
