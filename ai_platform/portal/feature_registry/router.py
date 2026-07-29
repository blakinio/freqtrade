from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query

from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.feature_registry.schema import (
    FeatureDependencyResolution,
    FeatureRegistryFeature,
    FeatureRegistryReplay,
    FeatureRegistrySnapshot,
)
from ai_platform.portal.feature_registry.service import (
    FeatureRegistryNotFoundError,
    FeatureRegistryService,
)


def build_router(
    service: FeatureRegistryService,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(prefix="/v1/feature-registry", tags=["feature-registry"])

    @router.get("/snapshot", response_model=FeatureRegistrySnapshot)
    def snapshot(
        context: RequestContext = Depends(context_dependency),
    ) -> FeatureRegistrySnapshot:
        return service.snapshot(context)

    @router.get("/features", response_model=list[FeatureRegistryFeature])
    def list_features(
        approved_for_ai: bool | None = None,
        status: str | None = Query(default=None, min_length=1, max_length=64),
        role: str | None = Query(default=None, min_length=1, max_length=64),
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[FeatureRegistryFeature, ...]:
        return service.list_features(
            context,
            approved_for_ai=approved_for_ai,
            status=status,
            role=role,
        )

    @router.get("/features/{feature_id}", response_model=FeatureRegistryFeature)
    def get_feature(
        feature_id: str,
        context: RequestContext = Depends(context_dependency),
    ) -> FeatureRegistryFeature:
        return _translate_errors(lambda: service.get_feature(context, feature_id))

    @router.get("/resolve", response_model=FeatureDependencyResolution)
    def resolve_dependencies(
        feature_id: list[str] = Query(min_length=1),
        context: RequestContext = Depends(context_dependency),
    ) -> FeatureDependencyResolution:
        return _translate_errors(lambda: service.resolve_dependencies(context, feature_id))

    @router.get("/replay", response_model=FeatureRegistryReplay)
    def replay(
        context: RequestContext = Depends(context_dependency),
    ) -> FeatureRegistryReplay:
        return service.replay(context)

    return router


T = TypeVar("T")


def _translate_errors(callback: Callable[[], T]) -> T:
    try:
        return callback()
    except FeatureRegistryNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "reason_code": "FEATURE_REGISTRY_UNKNOWN_FEATURE",
                "message": str(exc),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "reason_code": "FEATURE_REGISTRY_INVALID_REQUEST",
                "message": str(exc),
            },
        ) from exc
