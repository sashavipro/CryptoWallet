"""rest_api/src/infrastructure/persistence/database/gateways/sqla_user.py."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User as DomainUser
from src.infrastructure.persistence.database.mappers.user import map_domain_to_model
from src.infrastructure.persistence.database.mappers.user import map_user_to_domain
from src.infrastructure.persistence.database.models.user import User as DBUser


class UserGateway:
    """Gateway for user-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize gateway with active database session."""
        self.session = session

    async def add_user(self, user: DomainUser) -> DomainUser:
        """Add a new user to the database."""
        db_user = map_domain_to_model(user)
        self.session.add(db_user)
        await self.session.flush()
        return map_user_to_domain(db_user)

    async def get_user_by_id(self, user_id: uuid.UUID) -> DomainUser | None:
        """Retrieve a user by their UUID."""
        query = select(DBUser).where(DBUser.id == user_id)
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()

        if db_user is None:
            return None
        return map_user_to_domain(db_user)

    async def get_user_by_email(self, email: str) -> DomainUser | None:
        """Retrieve a user by their email address."""
        query = select(DBUser).where(DBUser.email == email)
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()

        if db_user is None:
            return None
        return map_user_to_domain(db_user)
