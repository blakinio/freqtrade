from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import Field, PositiveInt, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.contracts.risk import RiskPolicyVersion


PositiveDecimal = Annotated[Decimal, Field(gt=0)]
NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]
DrawdownDecimal = Annotated[Decimal, Field(ge=0, le=1)]


class RiskPolicyLimits(ContractModel):
    max_order_notional: PositiveDecimal
    max_projected_gross_exposure: PositiveDecimal
    max_projected_open_positions: PositiveInt
    max_daily_loss: PositiveDecimal
    max_drawdown: DrawdownDecimal
    require_healthy_runtime: bool = True


class RiskPolicyDefinition(ContractModel):
    version: RiskPolicyVersion
    limits: RiskPolicyLimits


class RiskEvaluationSnapshot(ContractModel):
    intent_notional: PositiveDecimal
    projected_gross_exposure: NonNegativeDecimal
    projected_open_positions: int = Field(ge=0)
    daily_loss: NonNegativeDecimal
    current_drawdown: DrawdownDecimal
    runtime_health: RuntimeHealthState


class KillSwitchState(ContractModel):
    tenant_id: NonEmptyStr
    environment: Environment
    active: bool
    reason_code: NonEmptyStr | None = None
    updated_by_actor_id: NonEmptyStr
    updated_at: UtcDateTime

    @model_validator(mode="after")
    def require_reason_when_active(self) -> KillSwitchState:
        if self.active and self.reason_code is None:
            raise ValueError("active kill switch requires a reason code")
        return self
