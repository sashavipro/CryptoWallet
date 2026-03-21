"""rest_api/src/application/ports/gateways.py."""

import uuid
from typing import Protocol

from src.domain.entities.permissions import UserPermission
from src.domain.entities.user import User


class UserGateway(Protocol):
    """Port for user database operations."""

    async def add_user(self, user: User) -> User:
        """Add a new user to the database."""
        ...

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by their unique ID."""
        ...

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address."""
        ...


class PermissionGateway(Protocol):
    """Port for user permissions database operations."""

    async def add_permission(self, permission: UserPermission) -> UserPermission:
        """Add a new permission record to the database."""
        ...

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserPermission | None:
        """Retrieve permissions associated with a specific user."""
        ...

    async def update_permission(self, permission: UserPermission) -> UserPermission:
        """Update an existing permission record in the database."""
        ...
