from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, status

from ai_platform.portal.contracts.strategy_closure import (
    SignalWizardPreviewCommand,
    SignalWizardPreviewResult,
    SignalWizardSubmitCommand,
    SignalWizardSubmitResult,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.signal_wizard.repository import CorruptSignalWizardRecordError
from ai_platform.portal.signal_wizard.service import (
    SignalWizardConflictError,
    SignalWizardNotFoundError,
    SignalWizardService,
    SignalWizardValidationError,
)


SignalWizardCommand = TypeVar(
    "SignalWizardCommand",
    SignalWizardPreviewCommand,
    SignalWizardSubmitCommand,
)


def build_router(
    service: SignalWizardService,
    context_dependency: Callable[..., RequestContext],
) -> APIRouter:
    router = APIRouter(prefix="/v1/signal-wizard", tags=["signal-wizard"])

    @router.post(
        "/preview",
        response_model=SignalWizardPreviewResult,
        status_code=status.HTTP_200_OK,
    )
    def preview(
        command: SignalWizardPreviewCommand,
        context: RequestContext = Depends(context_dependency),
    ) -> SignalWizardPreviewResult:
        try:
            return service.preview(context, _bind_trusted_correlation(command, context))
        except SignalWizardValidationError as exc:
            raise _http_error(422, exc.reason_code, exc) from exc
        except SignalWizardConflictError as exc:
            raise _http_error(409, "SIGNAL_WIZARD_CONFLICT", exc) from exc
        except CorruptSignalWizardRecordError as exc:
            raise _http_error(500, "SIGNAL_WIZARD_CORRUPT_RECORD", exc) from exc

    @router.post(
        "/submit",
        response_model=SignalWizardSubmitResult,
        status_code=status.HTTP_201_CREATED,
    )
    def submit(
        command: SignalWizardSubmitCommand,
        context: RequestContext = Depends(context_dependency),
    ) -> SignalWizardSubmitResult:
        try:
            return service.submit(context, _bind_trusted_correlation(command, context))
        except SignalWizardNotFoundError as exc:
            raise _http_error(404, "SIGNAL_WIZARD_PREVIEW_NOT_FOUND", exc) from exc
        except SignalWizardValidationError as exc:
            raise _http_error(422, exc.reason_code, exc) from exc
        except SignalWizardConflictError as exc:
            raise _http_error(409, "SIGNAL_WIZARD_CONFLICT", exc) from exc
        except CorruptSignalWizardRecordError as exc:
            raise _http_error(500, "SIGNAL_WIZARD_CORRUPT_RECORD", exc) from exc

    return router


def _bind_trusted_correlation(
    command: SignalWizardCommand,
    context: RequestContext,
) -> SignalWizardCommand:
    """Bind per-request correlation at the authenticated control-plane boundary.

    The browser/BFF cannot know the trusted request identifiers generated while the
    upstream request is authenticated. Tenant, actor, actor type and environment stay
    unchanged and remain fail-closed in ``SignalWizardService._validate_context``.
    """

    command_context = command.context.model_copy(
        update={"correlation": context.correlation_context()}
    )
    return command.model_copy(update={"context": command_context})


def _http_error(status_code: int, reason_code: str, exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"reason_code": reason_code, "message": str(exc)},
    )
