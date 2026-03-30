"""ethereum/src/presentation/http/responses.py."""

from typing import Any

from fastapi import status

from src.domain.exceptions import AssetNotFoundException
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


class RateLimitError(Exception):
    """Used for OpenAPI docs (429)."""


class ValidationError(Exception):
    """Used for OpenAPI docs (422)."""


EXCEPTION_STATUS_MAP = {
    ValueError: (status.HTTP_400_BAD_REQUEST, "Bad Request - Invalid input data"),
    # Ethereum-специфичные ошибки
    InvalidEthereumAddressException: (
        status.HTTP_400_BAD_REQUEST,
        "Bad Request - Invalid Ethereum address format",
    ),
    InvalidPrivateKeyFormatException: (
        status.HTTP_400_BAD_REQUEST,
        "Bad Request - Invalid private key format",
    ),
    NegativeBalanceException: (
        status.HTTP_400_BAD_REQUEST,
        "Bad Request - Balance cannot be negative",
    ),
    NegativeFeeException: (
        status.HTTP_400_BAD_REQUEST,
        "Bad Request - Transaction fee cannot be negative",
    ),
    NegativeTransactionFeeException: (
        status.HTTP_400_BAD_REQUEST,
        "Bad Request - Transaction fee cannot be negative",
    ),
    NegativeTransactionValueException: (
        status.HTTP_400_BAD_REQUEST,
        "Bad Request - Transaction value cannot be negative",
    ),
    WalletNotFoundException: (
        status.HTTP_404_NOT_FOUND,
        "Not Found - Wallet does not exist",
    ),
    AssetNotFoundException: (
        status.HTTP_404_NOT_FOUND,
        "Not Found - Asset does not exist",
    ),
    TransactionNotFoundException: (
        status.HTTP_404_NOT_FOUND,
        "Not Found - Transaction does not exist",
    ),
    WalletAlreadyExistsException: (
        status.HTTP_409_CONFLICT,
        "Conflict - Wallet already exists for this user and asset",
    ),
    InsufficientFundsException: (
        status.HTTP_403_FORBIDDEN,
        "Forbidden - Insufficient funds",
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
                        "detail": description.split(" - ")[-1],
                    }
                }
            },
        }
    return responses
