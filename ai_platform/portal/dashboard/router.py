from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends

from ai_platform.portal.control_plane.context import RequestContext

from .schema import BotDashboardPage, DashboardSearchRequest
from .service import DashboardReadService


def build_router(
    service: DashboardReadService,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(prefix="/v1/bot-management/dashboard", tags=["bot-management"])

    @router.post("/search", response_model=BotDashboardPage)
    def search_dashboard(
        request: DashboardSearchRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> BotDashboardPage:
        return service.search(context, request.filters, request.page)

    return router
