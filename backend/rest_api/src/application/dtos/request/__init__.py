"""rest_api/src/application/dtos/requests/__init__.py."""

from .ibay import CreateOrderRequestDTO
from .ibay import CreateProductRequestDTO
from .ibay import UpdateOrderRequestDTO
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
    "CreateOrderRequestDTO",
    "CreatePendingTransactionRequest",
    "CreateProductRequestDTO",
    "CreateWalletRequest",
    "ImportWalletRequest",
    "LoginUserRequest",
    "RegisterUserRequest",
    "UpdateOrderRequestDTO",
    "UpdateUserRequest",
)
