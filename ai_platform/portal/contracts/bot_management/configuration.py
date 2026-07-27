from __future__ import annotations

from typing import Self

from pydantic import PositiveInt, model_validator

from ai_platform.portal.contracts.bot_management.policies import (
    DcaPolicyVersion,
    EntryPolicyVersion,
    ExitPolicyVersion,
    GridPolicyVersion,
    MarketPolicyVersion,
    PositionSizingPolicyVersion,
    RuntimePolicyVersion,
    SignalCommand,
    SignalPolicyVersion,
)
from ai_platform.portal.contracts.bot_management.templates import CatalogVersionRef
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment, ExecutionMode


def _validate_grid_configuration(config: BotManagementConfiguration) -> None:
    grid = config.grid_policy
    if grid is None:
        return
    if config.dca_policy is not None:
        raise ValueError("grid and DCA policies cannot be enabled together")
    if grid.direction != config.market_policy.direction:
        raise ValueError("grid direction must match market policy direction")
    if grid.take_profit_price is not None and config.exit_policy.take_profit is not None:
        raise ValueError("grid and exit policy cannot both declare take profit")
    if grid.stop_loss_price is not None and config.exit_policy.stop_loss is not None:
        raise ValueError("grid and exit policy cannot both declare stop loss")


def _validate_signal_configuration(config: BotManagementConfiguration) -> None:
    signal = config.signal_policy
    if signal is None:
        return
    if SignalCommand.DCA in signal.allowed_commands and config.dca_policy is None:
        raise ValueError("signal DCA command requires a DCA policy")


def _policy_identifiers(config: BotManagementConfiguration) -> tuple[str, ...]:
    identifiers = [
        config.market_policy.policy_id,
        config.entry_policy.policy_id,
        config.position_sizing_policy.policy_id,
        config.exit_policy.policy_id,
        config.runtime_policy.policy_id,
    ]
    optional_policies = (config.dca_policy, config.signal_policy, config.grid_policy)
    identifiers.extend(policy.policy_id for policy in optional_policies if policy is not None)
    return tuple(identifiers)


def _validate_policy_identifiers(config: BotManagementConfiguration) -> None:
    identifiers = _policy_identifiers(config)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("policy identifiers must be unique across a configuration")


class BotManagementConfiguration(ContractModel):
    configuration_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    revision: PositiveInt
    template_ref: CatalogVersionRef
    compatibility_decision_ref: NonEmptyStr
    strategy_version: NonEmptyStr
    model_version: NonEmptyStr | None = None
    exchange_connection_ref: NonEmptyStr
    market_policy: MarketPolicyVersion
    entry_policy: EntryPolicyVersion
    position_sizing_policy: PositionSizingPolicyVersion
    dca_policy: DcaPolicyVersion | None = None
    exit_policy: ExitPolicyVersion
    risk_policy_version: NonEmptyStr
    signal_policy: SignalPolicyVersion | None = None
    grid_policy: GridPolicyVersion | None = None
    runtime_policy: RuntimePolicyVersion
    environment: Environment
    execution_mode: ExecutionMode
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        if self.runtime_policy.execution_mode != self.execution_mode:
            raise ValueError("runtime policy execution mode must match configuration")
        _validate_grid_configuration(self)
        _validate_signal_configuration(self)
        _validate_policy_identifiers(self)
        return self
