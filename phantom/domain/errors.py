"""
Domain errors — exception hierarchy for business logic errors.
The API layer maps these to HTTP responses in a central error handler.
"""


class PhantomError(Exception):
    """Base exception for all Phantom domain errors."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(PhantomError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str = ""):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} '{identifier}' not found"
        super().__init__(detail)
        self.resource = resource
        self.identifier = identifier


class ValidationError(PhantomError):
    """Business rule validation failed."""

    def __init__(self, message: str = "Validation failed", field: str = ""):
        super().__init__(message)
        self.field = field


class UnauthorizedError(PhantomError):
    """Authentication failed."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class ForbiddenError(PhantomError):
    """Authorization failed (authenticated but not allowed)."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)


class RateLimitError(PhantomError):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class ServiceUnavailableError(PhantomError):
    """External service or module not available."""

    def __init__(self, service: str = ""):
        message = f"{service} is not available" if service else "Service unavailable"
        super().__init__(message)
        self.service = service


class DuplicateError(PhantomError):
    """Duplicate resource (idempotency violation)."""

    def __init__(self, resource: str = "", key: str = ""):
        message = f"Duplicate {resource}" if resource else "Duplicate entry"
        if key:
            message += f" (key: {key})"
        super().__init__(message)
        self.resource = resource
        self.key = key
