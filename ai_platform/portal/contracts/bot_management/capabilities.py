from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr


class BotManagementCapability(StrEnum):
    TEMPLATE_READ = "bot_management.template.read"
    CATALOG_READ = "bot_management.catalog.read"
    BOT_CREATE = "bot_management.bot.create"
    BOT_REVISE = "bot_management.bot.revise"
    BOT_START = "bot_management.lifecycle.start"
    BOT_PAUSE = "bot_management.lifecycle.pause"
    BOT_STOP = "bot_management.lifecycle.stop"
    BOT_RETIRE = "bot_management.lifecycle.retire"
    POSITION_CLOSE = "bot_management.position.close"
    POSITION_PARTIAL_CLOSE = "bot_management.position.partial_close"
    POSITION_CLOSE_ALL = "bot_management.position.close_all"
    ORDER_CANCEL = "bot_management.order.cancel"
    ORDER_CANCEL_ALL = "bot_management.order.cancel_all"
    ORDER_REPLACE = "bot_management.order.replace"
    SIGNAL_ENDPOINT_MANAGE = "bot_management.signal.endpoint.manage"
    SIGNAL_RULE_MANAGE = "bot_management.signal.rule.manage"
    EXCHANGE_CONNECTION_CREATE = "bot_management.exchange.create"
    EXCHANGE_CONNECTION_VERIFY = "bot_management.exchange.verify"
    EXCHANGE_CONNECTION_ROTATE = "bot_management.exchange.rotate"
    EXCHANGE_CONNECTION_REVOKE = "bot_management.exchange.revoke"
    GRID_CONFIGURE = "bot_management.grid.configure"
    COMMAND_READ = "bot_management.command.read"
    RECONCILIATION_READ = "bot_management.reconciliation.read"
    KILL_SWITCH_USE = "bot_management.kill_switch.use"
    PRIVILEGED_POLICY_MANAGE = "bot_management.policy.privileged_manage"


class CapabilityVocabularyVersion(ContractModel):
    vocabulary_id: NonEmptyStr
    capabilities: tuple[BotManagementCapability, ...]

    @model_validator(mode="after")
    def validate_capabilities(self) -> Self:
        values = [capability.value for capability in self.capabilities]
        if not values:
            raise ValueError("capabilities must not be empty")
        if len(values) != len(set(values)):
            raise ValueError("capabilities must be unique")
        if values != sorted(values):
            raise ValueError("capabilities must use deterministic sorted order")
        return self


BOT_MANAGEMENT_CAPABILITY_V1 = CapabilityVocabularyVersion(
    vocabulary_id="bot-management-capabilities-v1",
    capabilities=tuple(sorted(BotManagementCapability, key=lambda item: item.value)),
)
