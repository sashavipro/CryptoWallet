"""rest_api/src/application/ports/gateways/permission.py."""

import uuid
from typing import Protocol

from src.domain.entities.permissions import UserPermission


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
