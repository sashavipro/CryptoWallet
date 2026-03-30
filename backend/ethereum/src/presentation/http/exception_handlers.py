"""ethereum/src/presentation/http/exception_handlers.py."""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.exceptions import AssetNotFoundException
from src.domain.exceptions import DomainException
from src.domain.exceptions import InsufficientFundsException
from src.domain.exceptions import InvalidEthereumAddressException
from src.domain.exceptions import InvalidPrivateKeyFormatException
from src.domain.exceptions import NegativeBalanceException
from src.domain.exceptions import NegativeFeeException
from src.domain.exceptions import NegativeTransactionFeeException
from src.domain.exceptions import NegativeTransactionValueException
from src.domain.exceptions import TransactionNotFoundException
from src.domain.exceptions import WalletAlreadyExistsException
from src.domain.exceptions import WalletNotFoundException

logger = logging.getLogger(__name__)


async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """Handle Business Errors (Domain)."""
    status_code = 400
    if isinstance(
        exc,
        (WalletNotFoundException, AssetNotFoundException, TransactionNotFoundException),
    ):
        status_code = 404
    elif isinstance(exc, WalletAlreadyExistsException):
        status_code = 409
    elif isinstance(exc, InsufficientFundsException):
        status_code = 403
    elif isinstance(
        exc,
        (
            InvalidEthereumAddressException,
            InvalidPrivateKeyFormatException,
            NegativeBalanceException,
            NegativeFeeException,
            NegativeTransactionFeeException,
            NegativeTransactionValueException,
        ),
    ):
        status_code = 400

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
    """Convert standard HTTPExceptions to our format."""
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
