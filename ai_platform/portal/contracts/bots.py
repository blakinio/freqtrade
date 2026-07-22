from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, PositiveInt, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment, ExecutionMode


PositiveDecimal = Annotated[Decimal, Field(gt=0)]


class BotDesiredState(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class BotObservedState(StrEnum):
    CREATED = "CREATED"
    PROVISIONING = "PROVISIONING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class BotConfigRevisionState(StrEnum):
    DRAFT = "DRAFT"
    PROMOTED = "PROMOTED"
    DEPRECATED = "DEPRECATED"


class BotSpec(ContractModel):
    tenant_id: NonEmptyStr
    strategy_version: NonEmptyStr
    model_version: NonEmptyStr
    risk_policy_version: NonEmptyStr
    exchange_connection_ref: NonEmptyStr
    pair_universe: tuple[NonEmptyStr, ...]
    timeframe: NonEmptyStr
    capital_allocation: PositiveDecimal
    capital_currency: NonEmptyStr
    runtime_version: NonEmptyStr
    config_revision: PositiveInt
    environment: Environment
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN

    @model_validator(mode="after")
    def validate_pair_universe(self) -> Self:
        if not self.pair_universe:
            raise ValueError("pair_universe must contain at least one pair")
        if len(set(self.pair_universe)) != len(self.pair_universe):
            raise ValueError("pair_universe must not contain duplicate pairs")
        return self


class BotConfigRevision(ContractModel):
    revision_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    revision: PositiveInt
    strategy_version: NonEmptyStr
    model_version: NonEmptyStr
    risk_policy_version: NonEmptyStr
    exchange_connection_ref: NonEmptyStr
    pair_universe: tuple[NonEmptyStr, ...]
    timeframe: NonEmptyStr
    capital_allocation: PositiveDecimal
    capital_currency: NonEmptyStr
    runtime_version: NonEmptyStr
    environment: Environment
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    state: BotConfigRevisionState = BotConfigRevisionState.DRAFT
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime

    @model_validator(mode="after")
    def validate_pair_universe(self) -> Self:
        if not self.pair_universe:
            raise ValueError("pair_universe must contain at least one pair")
        if len(set(self.pair_universe)) != len(self.pair_universe):
            raise ValueError("pair_universe must not contain duplicate pairs")
        return self


class BotInstance(ContractModel):
    bot_id: NonEmptyStr
    tenant_id: NonEmptyStr
    name: NonEmptyStr
    spec: BotSpec
    desired_state: BotDesiredState
    observed_state: BotObservedState

    @model_validator(mode="after")
    def validate_tenant_scope(self) -> Self:
        if self.spec.tenant_id != self.tenant_id:
            raise ValueError("bot spec must belong to the same tenant as the bot instance")
        return self
