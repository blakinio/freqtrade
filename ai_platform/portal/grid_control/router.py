from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends

from ai_platform.portal.contracts.common import ContractModel
from ai_platform.portal.control_plane.bot_management import actor_from_request, capabilities_from_request
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.grid_control.evidence import GridControlContext, GridExchangeCapabilityEvidence, GridTemplateCapabilityEvidence
from ai_platform.portal.grid_control.schema import GridPolicyRevision, GridPreview, GridPreviewRequest, PersistGridPolicyRequest
from ai_platform.portal.grid_control.service import GridControlService


class GridPreviewApiRequest(ContractModel):
    request: GridPreviewRequest
    template: GridTemplateCapabilityEvidence
    exchange: GridExchangeCapabilityEvidence


def build_router(service: GridControlService, context_dependency: Callable[..., RequestContext]) -> APIRouter:
    router = APIRouter(prefix="/v1/bot-management/grid", tags=["bot-management"])

    def access(context: RequestContext) -> GridControlContext:
        return GridControlContext(
            tenant_id=context.tenant_id,
            actor=actor_from_request(context),
            capabilities=capabilities_from_request(context),
        )

    @router.post("/preview", response_model=GridPreview)
    def preview_grid(
        request: GridPreviewApiRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> GridPreview:
        return service.preview(access(context), request.request, request.template, request.exchange)

    @router.post("/policies", response_model=GridPolicyRevision)
    def save_grid_policy(
        request: PersistGridPolicyRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> GridPolicyRevision:
        return service.persist(access(context), request)

    return router
