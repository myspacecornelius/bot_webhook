"""
Request middleware — adds request IDs, correlation IDs, and duration logging.

Every inbound HTTP request gets a unique X-Request-ID header (UUID4).
This ID is bound to structlog context so **every** log line emitted during
the request lifecycle includes it automatically.
"""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject request_id into every request and log request lifecycle."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Use client-provided correlation ID or generate one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id = request.headers.get("X-Correlation-ID", request_id)

        # Bind to structlog context for all downstream log calls
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            logger.error(
                "request_error",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        # Attach request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Skip noisy paths (health checks, static assets)
        if (
            not request.url.path.startswith("/docs")
            and request.url.path != "/openapi.json"
        ):
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms,
            )

        return response
