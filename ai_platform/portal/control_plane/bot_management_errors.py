from __future__ import annotations

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from ai_platform.portal.bot_builder.schema import BotBuilderReasonCode
from ai_platform.portal.bot_builder.service import BotBuilderServiceError
from ai_platform.portal.bot_catalog.schema import CatalogAccessReasonCode
from ai_platform.portal.bot_catalog.service import BotCatalogServiceError
from ai_platform.portal.bot_operations.service import (
    BotCommandIdentityConflictError,
    BotCommandNotFoundError,
    BotCommandReadDeniedError,
    BotCommandTransitionError,
)
from ai_platform.portal.exchange_connections.repository import (
    DuplicateCapabilityProfileError,
    DuplicateExchangeConnectionError,
    ExchangeCapabilityProfileNotFoundError,
    ExchangeConnectionNotFoundError,
    ExchangeConnectionRepositoryError,
    TenantIsolationError,
    VerificationNotFoundError,
)
from ai_platform.portal.exchange_connections.service import ExchangeConnectionValidationError
from ai_platform.portal.exchange_connections.verification import VerificationStateError
from ai_platform.portal.grid_control.schema import GridControlReasonCode
from ai_platform.portal.grid_control.service import GridControlServiceError
from ai_platform.portal.signal_control.schema import SignalControlReasonCode
from ai_platform.portal.signal_control.service import SignalControlServiceError


def _response(code: int, detail: str, reason_codes: tuple[str, ...] = ()) -> JSONResponse:
    payload: dict[str, object] = {"detail": detail}
    if reason_codes:
        payload["reason_codes"] = reason_codes
    return JSONResponse(status_code=code, content=payload)


def register_bot_management_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BotCatalogServiceError)
    async def catalog_error(_request: object, exc: BotCatalogServiceError) -> JSONResponse:
        if exc.reason_code in {
            CatalogAccessReasonCode.CAPABILITY_MISSING,
            CatalogAccessReasonCode.TENANT_MISMATCH,
        }:
            code = status.HTTP_403_FORBIDDEN
        elif exc.reason_code == CatalogAccessReasonCode.CATALOG_NOT_FOUND:
            code = status.HTTP_404_NOT_FOUND
        else:
            code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return _response(code, str(exc), (exc.reason_code.value,))

    @app.exception_handler(BotBuilderServiceError)
    async def builder_error(_request: object, exc: BotBuilderServiceError) -> JSONResponse:
        if exc.reason_code in {
            BotBuilderReasonCode.CAPABILITY_MISSING,
            BotBuilderReasonCode.TENANT_MISMATCH,
        }:
            code = status.HTTP_403_FORBIDDEN
        elif exc.reason_code == BotBuilderReasonCode.DRAFT_NOT_FOUND:
            code = status.HTTP_404_NOT_FOUND
        elif exc.reason_code in {
            BotBuilderReasonCode.DRAFT_ALREADY_EXISTS,
            BotBuilderReasonCode.DRAFT_REVISION_CONFLICT,
            BotBuilderReasonCode.CONFIGURATION_REVISION_CONFLICT,
        }:
            code = status.HTTP_409_CONFLICT
        else:
            code = status.HTTP_422_UNPROCESSABLE_ENTITY
        reasons = (exc.reason_code.value, *exc.details)
        return _response(code, str(exc), reasons)

    @app.exception_handler(BotCommandNotFoundError)
    async def command_not_found(_request: object, exc: BotCommandNotFoundError) -> JSONResponse:
        return _response(status.HTTP_404_NOT_FOUND, str(exc))

    @app.exception_handler(BotCommandReadDeniedError)
    async def command_read_denied(
        _request: object,
        exc: BotCommandReadDeniedError,
    ) -> JSONResponse:
        return _response(status.HTTP_403_FORBIDDEN, str(exc))

    @app.exception_handler(BotCommandIdentityConflictError)
    @app.exception_handler(BotCommandTransitionError)
    async def command_conflict(_request: object, exc: Exception) -> JSONResponse:
        return _response(status.HTTP_409_CONFLICT, str(exc))

    @app.exception_handler(SignalControlServiceError)
    async def signal_error(_request: object, exc: SignalControlServiceError) -> JSONResponse:
        if exc.reason_code in {
            SignalControlReasonCode.CAPABILITY_MISSING,
            SignalControlReasonCode.TENANT_MISMATCH,
        }:
            code = status.HTTP_403_FORBIDDEN
        elif exc.reason_code == SignalControlReasonCode.ENDPOINT_NOT_FOUND:
            code = status.HTTP_404_NOT_FOUND
        elif exc.reason_code in {
            SignalControlReasonCode.ENDPOINT_ALREADY_EXISTS,
            SignalControlReasonCode.ENDPOINT_REVISION_CONFLICT,
        }:
            code = status.HTTP_409_CONFLICT
        else:
            code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return _response(code, str(exc), (exc.reason_code.value,))

    @app.exception_handler(GridControlServiceError)
    async def grid_error(_request: object, exc: GridControlServiceError) -> JSONResponse:
        reasons = set(exc.reason_codes)
        if reasons.intersection(
            {
                GridControlReasonCode.CAPABILITY_MISSING,
                GridControlReasonCode.TENANT_MISMATCH,
            }
        ):
            code = status.HTTP_403_FORBIDDEN
        elif reasons.intersection(
            {
                GridControlReasonCode.POLICY_ALREADY_EXISTS,
                GridControlReasonCode.REVISION_CONFLICT,
            }
        ):
            code = status.HTTP_409_CONFLICT
        else:
            code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return _response(code, str(exc), tuple(item.value for item in exc.reason_codes))

    for error_type in (
        ExchangeConnectionNotFoundError,
        ExchangeCapabilityProfileNotFoundError,
        VerificationNotFoundError,
    ):
        app.add_exception_handler(
            error_type,
            lambda _request, exc: _response(status.HTTP_404_NOT_FOUND, str(exc)),
        )
    app.add_exception_handler(
        TenantIsolationError,
        lambda _request, exc: _response(status.HTTP_404_NOT_FOUND, "exchange connection not found"),
    )
    for error_type in (
        DuplicateCapabilityProfileError,
        DuplicateExchangeConnectionError,
        VerificationStateError,
    ):
        app.add_exception_handler(
            error_type,
            lambda _request, exc: _response(status.HTTP_409_CONFLICT, str(exc)),
        )
    for error_type in (ExchangeConnectionValidationError, ExchangeConnectionRepositoryError):
        app.add_exception_handler(
            error_type,
            lambda _request, exc: _response(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)),
        )
