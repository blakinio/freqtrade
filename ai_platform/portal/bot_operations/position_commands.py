from __future__ import annotations

from dataclasses import dataclass

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import PositionAction


@dataclass(frozen=True)
class PositionCommandPolicy:
    capability: BotManagementCapability
    blocked_by_kill_switch: bool


POSITION_COMMAND_POLICIES = {
    PositionAction.CLOSE_POSITION: PositionCommandPolicy(
        capability=BotManagementCapability.POSITION_CLOSE,
        blocked_by_kill_switch=False,
    ),
    PositionAction.PARTIAL_CLOSE: PositionCommandPolicy(
        capability=BotManagementCapability.POSITION_PARTIAL_CLOSE,
        blocked_by_kill_switch=False,
    ),
    PositionAction.CLOSE_ALL: PositionCommandPolicy(
        capability=BotManagementCapability.POSITION_CLOSE_ALL,
        blocked_by_kill_switch=False,
    ),
    PositionAction.FORCE_TAKE_PROFIT: PositionCommandPolicy(
        capability=BotManagementCapability.POSITION_CLOSE,
        blocked_by_kill_switch=False,
    ),
}


def position_command_policy(action: PositionAction) -> PositionCommandPolicy:
    return POSITION_COMMAND_POLICIES[action]
