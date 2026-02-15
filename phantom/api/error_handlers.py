"""
Central error handling — maps domain errors to HTTP responses.
Installed once on the FastAPI app so route handlers never touch HTTPException.
"""

import structlog
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..domain.errors import (
    DuplicateError,
    ForbiddenError,
    NotFoundError,
    PhantomError,
    RateLimitError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)

logger = structlog.get_logger()

_STATUS_MAP = {
    NotFoundError: 404,
    ValidationError: 422,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    RateLimitError: 429,
    ServiceUnavailableError: 503,
    DuplicateError: 409,
}


def install_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(PhantomError)
    async def phantom_error_handler(request: Request, exc: PhantomError):
        status_code = _STATUS_MAP.get(type(exc), 500)
        logger.warning(
            "domain_error",
            error_type=type(exc).__name__,
            message=exc.message,
            path=request.url.path,
        )
        body = {"detail": exc.message}
        if isinstance(exc, RateLimitError):
            return JSONResponse(
                status_code=status_code,
                content=body,
                headers={"Retry-After": str(exc.retry_after)},
            )
        return JSONResponse(status_code=status_code, content=body)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.error(
            "unhandled_error",
            error_type=type(exc).__name__,
            message=str(exc),
            path=request.url.path,
        )

        # WRITE ERROR TO FILE FOR DEBUGGING
        with open("error_log.txt", "a") as f:
            f.write(f"Error handling request {request.method} {request.url.path}:\n")
            f.write(f"{str(exc)}\n")
            f.write(traceback.format_exc())
            f.write("-" * 50 + "\n")

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
