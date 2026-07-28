from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.service import ControlPlaneService

if TYPE_CHECKING:
    from ai_platform.portal.control_plane.api import create_app as create_app


__all__ = [
    "ControlPlaneService",
    "RequestContext",
    "build_engine",
    "build_session_factory",
    "create_app",
    "create_schema",
]


def __getattr__(name: str) -> object:
    if name == "create_app":
        return import_module("ai_platform.portal.control_plane.api").create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
