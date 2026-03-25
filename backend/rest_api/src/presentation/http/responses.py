"""rest_api/src/presentation/http/responses.py."""

from typing import Any

from fastapi import status

from src.domain.exceptions import InvalidCredentialsException
from src.domain.exceptions import UserAlreadyExistsException
from src.domain.exceptions import UserNotFoundException


class RateLimitError(Exception):
    """Used for OpenAPI docs (429)."""


class ValidationError(Exception):
    """Used for OpenAPI docs (422)."""


EXCEPTION_STATUS_MAP = {
    ValueError: (status.HTTP_400_BAD_REQUEST, "Bad Request - Invalid input data"),
    InvalidCredentialsException: (
        status.HTTP_401_UNAUTHORIZED,
        "Unauthorized - Invalid email or password",
    ),
    UserNotFoundException: (
        status.HTTP_404_NOT_FOUND,
        "Not Found - User does not exist",
    ),
    UserAlreadyExistsException: (
        status.HTTP_409_CONFLICT,
        "Conflict - User already exists",
    ),
    ValidationError: (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Unprocessable Entity - Validation failed",
    ),
    RateLimitError: (
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Too Many Requests - Rate limit exceeded",
    ),
}


def create_error_responses(
    *exceptions: type[Exception],
) -> dict[int | str, dict[str, Any]]:
    """Generate OpenAPI response documentation for a given list of Exception classes."""
    responses = {}
    for exc in exceptions:
        mapped_data = EXCEPTION_STATUS_MAP.get(exc)
        if not mapped_data:
            continue

        status_code, description = mapped_data

        responses[status_code] = {
            "description": description,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": exc.__name__,
                        "detail": "Detailed error message from exception",
                    }
                }
            },
        }
    return responses
