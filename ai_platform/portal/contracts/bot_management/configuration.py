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
        if self.grid_policy is not None and self.dca_policy is not None:
            raise ValueError("grid and DCA policies cannot be enabled together")
        if self.grid_policy is not None:
            if self.grid_policy.direction != self.market_policy.direction:
                raise ValueError("grid direction must match market policy direction")
            if self.grid_policy.take_profit_price is not None:
                if self.exit_policy.take_profit is not None:
                    raise ValueError("grid and exit policy cannot both declare take profit")
            if self.grid_policy.stop_loss_price is not None:
                if self.exit_policy.stop_loss is not None:
                    raise ValueError("grid and exit policy cannot both declare stop loss")
        if self.signal_policy is not None:
            if SignalCommand.DCA in self.signal_policy.allowed_commands and self.dca_policy is None:
                raise ValueError("signal DCA command requires a DCA policy")
        policy_keys = [
            ("market", self.market_policy.policy_id, self.market_policy.revision),
            ("entry", self.entry_policy.policy_id, self.entry_policy.revision),
            (
                "position_sizing",
                self.position_sizing_policy.policy_id,
                self.position_sizing_policy.revision,
            ),
            ("exit", self.exit_policy.policy_id, self.exit_policy.revision),
            ("runtime", self.runtime_policy.policy_id, self.runtime_policy.revision),
        ]
        if self.dca_policy is not None:
            policy_keys.append(("dca", self.dca_policy.policy_id, self.dca_policy.revision))
        if self.signal_policy is not None:
            policy_keys.append(
                ("signal", self.signal_policy.policy_id, self.signal_policy.revision)
            )
        if self.grid_policy is not None:
            policy_keys.append(("grid", self.grid_policy.policy_id, self.grid_policy.revision))
        identifiers = [item[1] for item in policy_keys]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("policy identifiers must be unique across a configuration")
        return self
