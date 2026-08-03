from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


_GENERIC_MESSAGES = {
    "extra_forbidden": "Extra inputs are not permitted",
    "json_invalid": "Request body contains invalid JSON",
    "missing": "Required field is missing",
    "string_pattern_mismatch": "Field format is invalid",
    "string_too_long": "Field is too long",
    "string_too_short": "Field is too short",
    "value_error": "Field value is invalid",
}


def install_safe_request_validation_handler(app: FastAPI) -> None:
    """Prevent FastAPI/Pydantic from echoing rejected secret-bearing input values."""

    @app.exception_handler(RequestValidationError)
    async def safe_request_validation_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details: list[dict[str, Any]] = []
        for error in exc.errors():
            error_type = str(error.get("type", "validation_error"))
            location = [str(part) if not isinstance(part, int) else part for part in error.get("loc", ())]
            details.append(
                {
                    "type": error_type,
                    "loc": location,
                    "msg": _GENERIC_MESSAGES.get(error_type, "Request field is invalid"),
                }
            )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": details},
            headers={"cache-control": "no-store"},
        )
