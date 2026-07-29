from __future__ import annotations

import os


if os.environ.get("GITHUB_WORKFLOW") == "Liquidations Live Health" and (
    container_name := os.environ.get("LIQUID20_CONTAINER_NAME")
):
    from ai_platform.scripts.liquidation_health_runtime_adapter import (
        install_runtime_adapter,
    )

    install_runtime_adapter(container_name)
