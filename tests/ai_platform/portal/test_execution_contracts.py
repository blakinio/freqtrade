from typing import get_type_hints

from ai_platform.portal.contracts.bots import BotInstance
from ai_platform.portal.contracts.execution import ExecutionAdapter


def test_execution_adapter_provisioning_requires_explicit_bot_instance_identity() -> None:
    hints = get_type_hints(ExecutionAdapter.provision_bot)

    assert hints["bot"] is BotInstance
    assert "spec" not in hints
