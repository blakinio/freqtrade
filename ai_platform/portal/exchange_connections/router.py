from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ExchangeConnectionMetadata,
    ExchangeConnectionVerificationRequest,
)
from ai_platform.portal.contracts.common import ContractModel
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.control_plane.bot_management import (
    actor_from_request,
    capabilities_from_request,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.exchange_connections.schema import ExchangeConnectionProduct
from ai_platform.portal.exchange_connections.service import ExchangeConnectionService
from ai_platform.portal.security.authorization import PermissionDeniedError


class ExchangeVerificationApiRequest(ContractModel):
    verification_id: str
    environment: Environment
    idempotency_key: str


def _require(
    context: RequestContext,
    capability: BotManagementCapability,
) -> None:
    if capability not in capabilities_from_request(context):
        raise PermissionDeniedError(f"permission denied: {capability.value}")


def build_router(
    service: ExchangeConnectionService,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(prefix="/v1/bot-management/exchanges", tags=["bot-management"])

    @router.get("", response_model=list[ExchangeConnectionProduct])
    def list_connections(
        context: RequestContext = Depends(context_dependency),
    ) -> tuple[ExchangeConnectionProduct, ...]:
        _require(context, BotManagementCapability.EXCHANGE_CONNECTION_CREATE)
        return service.list_connections(tenant_id=context.tenant_id)

    @router.get("/{connection_id}", response_model=ExchangeConnectionProduct)
    def get_connection(
        connection_id: str,
        context: RequestContext = Depends(context_dependency),
    ) -> ExchangeConnectionProduct:
        _require(context, BotManagementCapability.EXCHANGE_CONNECTION_CREATE)
        return service.get_connection(
            tenant_id=context.tenant_id,
            connection_id=connection_id,
        )

    @router.post(
        "",
        response_model=ExchangeConnectionProduct,
        status_code=status.HTTP_201_CREATED,
    )
    def create_connection(
        request: ExchangeConnectionMetadata,
        context: RequestContext = Depends(context_dependency),
    ) -> ExchangeConnectionProduct:
        _require(context, BotManagementCapability.EXCHANGE_CONNECTION_CREATE)
        if request.tenant_id != context.tenant_id:
            raise PermissionDeniedError("tenant scope mismatch")
        return service.create_connection(request)

    @router.post(
        "/{connection_id}/verification-requests",
        response_model=ExchangeConnectionVerificationRequest,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def request_verification(
        connection_id: str,
        request: ExchangeVerificationApiRequest,
        context: RequestContext = Depends(context_dependency),
    ) -> ExchangeConnectionVerificationRequest:
        _require(context, BotManagementCapability.EXCHANGE_CONNECTION_VERIFY)
        return service.request_verification(
            verification_id=request.verification_id,
            tenant_id=context.tenant_id,
            connection_id=connection_id,
            actor=actor_from_request(context),
            environment=request.environment,
            correlation=context.correlation_context(),
            idempotency_key=request.idempotency_key,
            requested_at=datetime.now(UTC),
        )

    return router
