from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

from ai_platform.portal.control_plane.database import Base


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


def _declared_table_names(path: Path) -> frozenset[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__tablename__"
            for target in node.targets
        ):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            names.add(node.value.value)
    if not names:
        raise RuntimeError(f"Portal model file declares no durable tables: {path}")
    return frozenset(names)


def load_portal_models() -> None:
    """Register every durable Portal ORM table without package side effects.

    Registration is keyed by the tables already present on the shared metadata,
    not by ``sys.modules``. This supports callers that imported only part of the
    Portal while preventing duplicate SQLAlchemy table declarations. Model files
    are executed under private module names so package ``__init__`` services are
    never imported by the database image or schema evidence job.
    """

    repository_root = Path(__file__).resolve().parents[3]
    for index, module_name in enumerate(MODEL_MODULES):
        path = repository_root.joinpath(*module_name.split(".")).with_suffix(".py")
        if not path.is_file():
            raise RuntimeError(f"Portal model file is missing: {path}")
        declared_tables = _declared_table_names(path)
        registered_tables = declared_tables.intersection(Base.metadata.tables)
        if registered_tables == declared_tables:
            continue
        if registered_tables:
            missing = sorted(declared_tables - registered_tables)
            raise RuntimeError(
                f"Portal model registration is partial for {path}: missing {missing}"
            )
        private_name = f"_portal_schema_model_{index}"
        spec = importlib.util.spec_from_file_location(private_name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Portal model file cannot be loaded: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[private_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(private_name, None)
            raise
