"""rest_api/src/domain/entities/__init__.py."""

from .base import BaseEntity
from .permissions import UserPermission
from .user import User

__all__ = (
    "BaseEntity",
    "User",
    "UserPermission",
)
