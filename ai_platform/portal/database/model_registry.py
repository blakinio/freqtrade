from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


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
    """Register every durable Portal ORM table without package service side effects.

    Some package ``__init__`` modules export runtime services and consequently
    import dependencies that are not part of the database image. Loading the
    exact canonical ``models.py`` modules keeps schema construction bounded to
    SQLAlchemy declarations while preserving their normal module identities.
    """

    repository_root = Path(__file__).resolve().parents[3]
    for module_name in MODEL_MODULES:
        if module_name in sys.modules:
            continue
        path = repository_root.joinpath(*module_name.split(".")).with_suffix(".py")
        if not path.is_file():
            raise RuntimeError(f"Portal model file is missing: {path}")
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Portal model file cannot be loaded: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise
