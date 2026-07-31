from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar
from uuid import NAMESPACE_URL, uuid5

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


CommandT = TypeVar("CommandT", SignalWizardPreviewCommand, SignalWizardSubmitCommand)


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
        bound_context, bound_command = _bind_command_context(
            context,
            command,
            operation="preview",
        )
        try:
            return service.preview(bound_context, bound_command)
        except SignalWizardValidationError as exc:
            raise _http_error(422, exc.reason_code, exc.public_message) from exc
        except SignalWizardConflictError as exc:
            raise _http_error(409, exc.reason_code, exc.public_message) from exc
        except CorruptSignalWizardRecordError as exc:
            raise _http_error(
                500,
                "SIGNAL_WIZARD_CORRUPT_RECORD",
                "Persisted Signal Wizard evidence is unavailable.",
            ) from exc

    @router.post(
        "/submit",
        response_model=SignalWizardSubmitResult,
        status_code=status.HTTP_201_CREATED,
    )
    def submit(
        command: SignalWizardSubmitCommand,
        context: RequestContext = Depends(context_dependency),
    ) -> SignalWizardSubmitResult:
        bound_context, bound_command = _bind_command_context(
            context,
            command,
            operation="submit",
        )
        try:
            return service.submit(bound_context, bound_command)
        except SignalWizardNotFoundError as exc:
            raise _http_error(404, exc.reason_code, exc.public_message) from exc
        except SignalWizardValidationError as exc:
            raise _http_error(422, exc.reason_code, exc.public_message) from exc
        except SignalWizardConflictError as exc:
            raise _http_error(409, exc.reason_code, exc.public_message) from exc
        except CorruptSignalWizardRecordError as exc:
            raise _http_error(
                500,
                "SIGNAL_WIZARD_CORRUPT_RECORD",
                "Persisted Signal Wizard evidence is unavailable.",
            ) from exc

    return router


def _bind_command_context(
    context: RequestContext,
    command: CommandT,
    *,
    operation: str,
) -> tuple[RequestContext, CommandT]:
    """Construct stable trusted command correlation after authentication."""

    identity = (
        f"signal-wizard:{context.tenant_id}:{context.actor_id}:"
        f"{operation}:{command.idempotency_key.strip()}"
    )
    bound_context = context.model_copy(
        update={
            "request_id": uuid5(NAMESPACE_URL, f"{identity}:request"),
            "correlation_id": uuid5(NAMESPACE_URL, f"{identity}:correlation"),
            "causation_id": None,
        }
    )
    command_context = command.context.model_copy(
        update={"correlation": bound_context.correlation_context()}
    )
    return bound_context, command.model_copy(update={"context": command_context})


def _http_error(status_code: int, reason_code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"reason_code": reason_code, "message": message},
    )
