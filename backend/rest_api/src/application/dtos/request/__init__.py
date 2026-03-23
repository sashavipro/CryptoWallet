"""rest_api/src/application/dtos/requests/__init__.py."""

from .user import ChangePasswordRequest
from .user import LoginUserRequest
from .user import RegisterUserRequest
from .user import UpdateUserRequest

__all__ = (
    "ChangePasswordRequest",
    "LoginUserRequest",
    "RegisterUserRequest",
    "UpdateUserRequest",
)
