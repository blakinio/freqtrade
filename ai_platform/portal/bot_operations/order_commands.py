from __future__ import annotations

from dataclasses import dataclass

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import OrderAction


@dataclass(frozen=True)
class OrderCommandPolicy:
    capability: BotManagementCapability
    blocked_by_kill_switch: bool


ORDER_COMMAND_POLICIES = {
    OrderAction.CANCEL_ORDER: OrderCommandPolicy(
        capability=BotManagementCapability.ORDER_CANCEL,
        blocked_by_kill_switch=False,
    ),
    OrderAction.CANCEL_ALL_ORDERS: OrderCommandPolicy(
        capability=BotManagementCapability.ORDER_CANCEL_ALL,
        blocked_by_kill_switch=False,
    ),
    OrderAction.REPLACE_ORDER: OrderCommandPolicy(
        capability=BotManagementCapability.ORDER_REPLACE,
        blocked_by_kill_switch=True,
    ),
}


def order_command_policy(action: OrderAction) -> OrderCommandPolicy:
    return ORDER_COMMAND_POLICIES[action]
