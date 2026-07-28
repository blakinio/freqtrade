from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from ai_platform.portal.bot_catalog.schema import (
    CatalogAccessContext,
    CatalogPageRequest,
    CatalogTemplateFilters,
    TemplateCatalogPage,
)
from ai_platform.portal.bot_catalog.service import BotCatalogService
from ai_platform.portal.contracts.bot_management.compatibility import (
    BotCompatibilityDecision,
    CompatibilitySelection,
)
from ai_platform.portal.contracts.bot_management.templates import CatalogVersionRef
from ai_platform.portal.contracts.common import ContractModel
from ai_platform.portal.control_plane.bot_management import capabilities_from_request
from ai_platform.portal.control_plane.context import RequestContext


class CatalogTemplateSearchRequest(ContractModel):
    catalog_ref: CatalogVersionRef
    filters: CatalogTemplateFilters
    page: CatalogPageRequest


class CatalogCompatibilityRequest(ContractModel):
    catalog_ref: CatalogVersionRef
    selection: CompatibilitySelection


def build_router(
    service: BotCatalogService,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(prefix="/v1/bot-management/catalog", tags=["bot-management"])

    def access(context: RequestContext) -> CatalogAccessContext:
        return CatalogAccessContext(
            tenant_id=context.tenant_id,
            capabilities=capabilities_from_request(context),
        )

    @router.get("/{catalog_id}/latest", response_model=CatalogVersionRef)
    def latest_catalog_ref(
        catalog_id: str,
        context: RequestContext = Depends(context_dependency),
    ) -> CatalogVersionRef:
        return service.latest_catalog_ref(access(context), catalog_id)

    @router.post("/templates/search", response_model=TemplateCatalogPage)
    def search_templates(
        request: CatalogTemplateSearchRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> TemplateCatalogPage:
        return service.list_templates(
            access(context),
            request.catalog_ref,
            request.filters,
            request.page,
        )

    @router.post("/compatibility", response_model=BotCompatibilityDecision)
    def decide_compatibility(
        request: CatalogCompatibilityRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> BotCompatibilityDecision:
        return service.decide_compatibility(
            access(context),
            request.catalog_ref,
            request.selection,
            datetime.now(UTC),
        )

    return router
