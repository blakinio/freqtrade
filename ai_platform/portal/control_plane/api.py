from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

from ai_platform.portal.control_plane.api_core import *  # noqa: F403
from ai_platform.portal.control_plane.api_core import create_app as _create_core_app
from ai_platform.portal.control_plane.context import RequestContext, identity_dependency
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.feature_registry.router import (
    build_router as build_feature_registry_router,
)
from ai_platform.portal.feature_registry.service import FeatureRegistryService
from ai_platform.portal.strategy_lab.router import build_router as build_strategy_lab_router
from ai_platform.portal.strategy_lab.service import StrategyLabService


def create_app(
    session_factory: SessionFactory,
    identity_context_provider: Callable[[], RequestContext] | None = None,
    *args: Any,
    feature_registry_service: FeatureRegistryService | None = None,
    strategy_lab_service: StrategyLabService | None = None,
    **kwargs: Any,
) -> FastAPI:
    """Build the canonical Portal API with research-only registry and Strategy Lab routes."""
    app = _create_core_app(
        session_factory,
        identity_context_provider,
        *args,
        **kwargs,
    )
    feature_registry = feature_registry_service or FeatureRegistryService()
    strategy_lab = strategy_lab_service or StrategyLabService(session_factory)
    context_dependency = identity_dependency(identity_context_provider)
    app.include_router(build_feature_registry_router(feature_registry, context_dependency))
    app.include_router(build_strategy_lab_router(strategy_lab, context_dependency))
    return app
