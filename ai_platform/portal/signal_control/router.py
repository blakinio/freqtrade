from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, status
from pydantic import Base64Bytes

from ai_platform.portal.contracts.common import ContractModel
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.control_plane.bot_management import (
    actor_from_request,
    capabilities_from_request,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.signal_control.overview_service import SignalControlOverviewService
from ai_platform.portal.signal_control.public_schema import SignalControlOverview
from ai_platform.portal.signal_control.schema import (
    AuthoritativeSignalTargetState,
    CreateSignalEndpoint,
    ReviseSignalEndpoint,
    SignalControlContext,
    SignalEndpointRevision,
    SignalProcessingRequest,
    SignalProcessingResult,
)
from ai_platform.portal.signal_control.service import SignalControlService


class CreateSignalEndpointApiRequest(ContractModel):
    environment: Environment
    endpoint: CreateSignalEndpoint


class ReviseSignalEndpointApiRequest(ContractModel):
    environment: Environment
    endpoint: ReviseSignalEndpoint


class ProcessSignalApiRequest(ContractModel):
    environment: Environment
    request: SignalProcessingRequest
    signature: Base64Bytes
    target: AuthoritativeSignalTargetState


def build_router(
    service: SignalControlService,
    overview_service: SignalControlOverviewService,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(prefix="/v1/bot-management/signals", tags=["bot-management"])

    def signal_context(
        context: RequestContext,
        environment: Environment,
    ) -> SignalControlContext:
        return SignalControlContext(
            tenant_id=context.tenant_id,
            actor=actor_from_request(context),
            environment=environment,
            capabilities=capabilities_from_request(context),
            correlation=context.correlation_context(),
        )

    @router.get("/overview", response_model=SignalControlOverview)
    def signal_overview(
        context: RequestContext = Depends(context_dependency),
    ) -> SignalControlOverview:
        return overview_service.overview(
            tenant_id=context.tenant_id,
            capabilities=capabilities_from_request(context),
        )

    @router.post(
        "/endpoints",
        response_model=SignalEndpointRevision,
        status_code=status.HTTP_201_CREATED,
    )
    def create_endpoint(
        request: CreateSignalEndpointApiRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> SignalEndpointRevision:
        return service.create_endpoint(
            signal_context(context, request.environment),
            request.endpoint,
        )

    @router.post("/endpoints/revise", response_model=SignalEndpointRevision)
    def revise_endpoint(
        request: ReviseSignalEndpointApiRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> SignalEndpointRevision:
        return service.revise_endpoint(
            signal_context(context, request.environment),
            request.endpoint,
        )

    @router.post("/preview", response_model=SignalProcessingResult)
    def preview_signal(
        request: ProcessSignalApiRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> SignalProcessingResult:
        return service.preview(
            signal_context(context, request.environment),
            request.request,
            signature=bytes(request.signature),
            target=request.target,
        )

    @router.post("/process", response_model=SignalProcessingResult)
    def process_signal(
        request: ProcessSignalApiRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> SignalProcessingResult:
        return service.process(
            signal_context(context, request.environment),
            request.request,
            signature=bytes(request.signature),
            target=request.target,
        )

    return router
