from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from threading import RLock

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
_MODEL_REGISTRY_LOCK = RLock()


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _model_path(module_name: str) -> Path:
    return _repository_root().joinpath(*module_name.split(".")).with_suffix(".py")


def _declared_table_names(path: Path) -> frozenset[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__tablename__" for target in node.targets
        ):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            names.add(node.value.value)
    if not names:
        raise RuntimeError(f"Portal model file declares no durable tables: {path}")
    return frozenset(names)


def portal_table_names() -> frozenset[str]:
    names: set[str] = set()
    for module_name in MODEL_MODULES:
        path = _model_path(module_name)
        if not path.is_file():
            raise RuntimeError(f"Portal model file is missing: {path}")
        names.update(_declared_table_names(path))
    return frozenset(names)


def _load_model_module(module_name: str, path: Path, declared_tables: frozenset[str]) -> None:
    registered_tables = declared_tables.intersection(Base.metadata.tables)
    if module_name in sys.modules:
        if registered_tables != declared_tables:
            missing = sorted(declared_tables - registered_tables)
            raise RuntimeError(
                f"Portal model module {module_name} is loaded but tables are missing: {missing}"
            )
        return
    if registered_tables:
        missing = sorted(declared_tables - registered_tables)
        if missing:
            raise RuntimeError(
                f"Portal model registration is partial for {path}: missing {missing}"
            )
        raise RuntimeError(
            f"Portal tables for {module_name} were registered without the canonical module"
        )

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

    missing = sorted(declared_tables - set(Base.metadata.tables))
    if missing:
        sys.modules.pop(module_name, None)
        raise RuntimeError(f"Portal model module {module_name} did not register tables: {missing}")


def load_portal_models() -> frozenset[str]:
    """Register and return the authoritative durable Portal table manifest.

    Model files are executed under their canonical module names without importing
    package ``__init__`` services. Later normal imports therefore reuse the exact
    same module and SQLAlchemy table objects instead of declaring them twice.
    Tables attached to the shared Base by unrelated tests or services are not part
    of the returned manifest and must never be migrated by this authority.
    """

    with _MODEL_REGISTRY_LOCK:
        declared_manifest: set[str] = set()
        for module_name in MODEL_MODULES:
            path = _model_path(module_name)
            if not path.is_file():
                raise RuntimeError(f"Portal model file is missing: {path}")
            declared_tables = _declared_table_names(path)
            declared_manifest.update(declared_tables)
            _load_model_module(module_name, path, declared_tables)
        missing_from_metadata = sorted(declared_manifest - set(Base.metadata.tables))
        if missing_from_metadata:
            raise RuntimeError(
                f"Portal model manifest is not fully registered: {missing_from_metadata}"
            )
        return frozenset(declared_manifest)
