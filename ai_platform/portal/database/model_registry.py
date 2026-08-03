from __future__ import annotations

import importlib


MODEL_MODULES = (
    "ai_platform.portal.bot_operations.models",
    "ai_platform.portal.control_plane.models",
    "ai_platform.portal.events.models",
    "ai_platform.portal.execution_submission.models",
    "ai_platform.portal.identity.models",
    "ai_platform.portal.intelligence.models",
    "ai_platform.portal.learning.models",
    "ai_platform.portal.model_control.models",
    "ai_platform.portal.operations.models",
    "ai_platform.portal.product.models",
    "ai_platform.portal.risk.models",
    "ai_platform.portal.signal_wizard.models",
    "ai_platform.portal.strategy_lab.models",
    "ai_platform.portal.telemetry.models",
)


def load_portal_models() -> None:
    """Register every durable Portal ORM model exactly once.

    Normal imports preserve Python's module cache and complete modules that have
    not yet been loaded. They avoid both partial ``sys.modules`` assumptions and
    duplicate SQLAlchemy table registration from manual module execution.
    """

    for module_name in MODEL_MODULES:
        importlib.import_module(module_name)
