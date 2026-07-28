from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status

from ai_platform.portal.bot_builder.schema import (
    BotBuilderAccessContext,
    BotConfigurationDraftPreview,
    BotConfigurationDraftRevision,
    CreateBotConfigurationDraft,
    DraftRevisionRef,
    FinalizeBotConfigurationDraft,
    FinalizedBotConfiguration,
    ReviseBotConfigurationDraft,
)
from ai_platform.portal.bot_builder.service import BotConfigurationBuilderService
from ai_platform.portal.control_plane.bot_management import capabilities_from_request
from ai_platform.portal.control_plane.context import RequestContext


def build_router(
    service: BotConfigurationBuilderService,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(prefix="/v1/bot-management/builder", tags=["bot-management"])

    def access(context: RequestContext) -> BotBuilderAccessContext:
        return BotBuilderAccessContext(
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
            capabilities=capabilities_from_request(context),
        )

    @router.post(
        "/drafts",
        response_model=BotConfigurationDraftRevision,
        status_code=status.HTTP_201_CREATED,
    )
    def create_draft(
        request: CreateBotConfigurationDraft,
        context: RequestContext = Depends(context_dependency),
    ) -> BotConfigurationDraftRevision:
        return service.create_draft(access(context), request, datetime.now(UTC))

    @router.post("/drafts/revise", response_model=BotConfigurationDraftRevision)
    def revise_draft(
        request: ReviseBotConfigurationDraft,
        context: RequestContext = Depends(context_dependency),
    ) -> BotConfigurationDraftRevision:
        return service.revise_draft(access(context), request, datetime.now(UTC))

    @router.post("/drafts/preview", response_model=BotConfigurationDraftPreview)
    def preview_draft(
        request: DraftRevisionRef,
        context: RequestContext = Depends(context_dependency),
    ) -> BotConfigurationDraftPreview:
        return service.preview_draft(access(context), request, datetime.now(UTC))

    @router.post("/drafts/finalize", response_model=FinalizedBotConfiguration)
    def finalize_draft(
        request: FinalizeBotConfigurationDraft,
        context: RequestContext = Depends(context_dependency),
    ) -> FinalizedBotConfiguration:
        return service.finalize_draft(access(context), request, datetime.now(UTC))

    return router
