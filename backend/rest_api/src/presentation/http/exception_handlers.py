"""rest_api/src/presentation/http/exception_handlers.py."""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.exceptions import DomainException
from src.domain.exceptions import InvalidCredentialsException
from src.domain.exceptions import UserAlreadyExistsException
from src.domain.exceptions import UserNotFoundException

logger = logging.getLogger(__name__)


async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """Handle Business Errors (Domain)."""
    status_code = 400
    if isinstance(exc, UserNotFoundException):
        status_code = 404
    elif isinstance(exc, UserAlreadyExistsException):
        status_code = 409
    elif isinstance(exc, InvalidCredentialsException):
        status_code = 401

    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": exc.__class__.__name__, "detail": str(exc)},
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle Validation Errors in Value Objects."""
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": "ValidationError", "detail": str(exc)},
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Convert standard HTTPExceptions to our format.

    This includes exceptions raised by HTTPBearer.
    """
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": "HTTPException", "detail": exc.detail},
        headers=headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a clear and concise error message for Pydantic/FastAPI validation."""
    errors = [
        {"loc": ".".join(map(str, err["loc"])), "msg": err["msg"], "type": err["type"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "UnprocessableEntity", "detail": errors},
    )
