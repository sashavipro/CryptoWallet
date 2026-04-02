"""rest_api/src/application/dtos/requests/__init__.py."""

from .transaction import CompleteTransactionRequest
from .transaction import CreatePendingTransactionRequest
from .user import ChangePasswordRequest
from .user import LoginUserRequest
from .user import RegisterUserRequest
from .user import UpdateUserRequest
from .wallet import CreateWalletRequest
from .wallet import ImportWalletRequest

__all__ = (
    "ChangePasswordRequest",
    "CompleteTransactionRequest",
    "CreatePendingTransactionRequest",
    "CreateWalletRequest",
    "ImportWalletRequest",
    "LoginUserRequest",
    "RegisterUserRequest",
    "UpdateUserRequest",
)
