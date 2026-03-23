"""rest_api/src/application/ports/gateways/user.py."""

import uuid
from typing import Protocol

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
