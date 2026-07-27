from __future__ import annotations

from dataclasses import dataclass

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import LifecycleAction


@dataclass(frozen=True)
class LifecycleCommandPolicy:
    capability: BotManagementCapability
    blocked_by_kill_switch: bool


LIFECYCLE_COMMAND_POLICIES = {
    LifecycleAction.START: LifecycleCommandPolicy(
        capability=BotManagementCapability.BOT_START,
        blocked_by_kill_switch=True,
    ),
    LifecycleAction.PAUSE_NEW_ENTRIES: LifecycleCommandPolicy(
        capability=BotManagementCapability.BOT_PAUSE,
        blocked_by_kill_switch=False,
    ),
    LifecycleAction.RESUME: LifecycleCommandPolicy(
        capability=BotManagementCapability.BOT_START,
        blocked_by_kill_switch=True,
    ),
    LifecycleAction.STOP_KEEP_POSITIONS: LifecycleCommandPolicy(
        capability=BotManagementCapability.BOT_STOP,
        blocked_by_kill_switch=False,
    ),
    LifecycleAction.STOP_AFTER_EXIT: LifecycleCommandPolicy(
        capability=BotManagementCapability.BOT_STOP,
        blocked_by_kill_switch=False,
    ),
    LifecycleAction.RESTART_RUNTIME: LifecycleCommandPolicy(
        capability=BotManagementCapability.BOT_START,
        blocked_by_kill_switch=True,
    ),
    LifecycleAction.RETIRE: LifecycleCommandPolicy(
        capability=BotManagementCapability.BOT_RETIRE,
        blocked_by_kill_switch=False,
    ),
}


def lifecycle_command_policy(action: LifecycleAction) -> LifecycleCommandPolicy:
    return LIFECYCLE_COMMAND_POLICIES[action]
