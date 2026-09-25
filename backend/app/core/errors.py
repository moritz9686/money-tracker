"""Application exceptions with stable, safe API error codes."""


class ApplicationError(Exception):
    """Base exception converted to a consistent JSON error response."""

    status_code = 500
    code = "INTERNAL_ERROR"
    message = "An unexpected error occurred"


class AuthenticationError(ApplicationError):
    status_code = 401
    code = "AUTHENTICATION_ERROR"
    message = "Authentication failed"


class NotFoundError(ApplicationError):
    status_code = 404
    code = "NOT_FOUND"
    message = "The requested resource was not found"


class ConflictError(ApplicationError):
    status_code = 409
    code = "CONFLICT"
    message = "The request conflicts with existing data"


class InputValidationError(ApplicationError):
    status_code = 422
    code = "VALIDATION_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
