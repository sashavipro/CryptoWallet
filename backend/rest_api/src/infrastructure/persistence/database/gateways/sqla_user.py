"""rest_api/src/infrastructure/persistence/database/gateways/sqla_user.py."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User as DomainUser
from src.infrastructure.persistence.database.mappers.user import map_domain_to_model
from src.infrastructure.persistence.database.mappers.user import map_user_to_domain
from src.infrastructure.persistence.database.models.user import User as DBUser

logger = logging.getLogger(__name__)


class UserGateway:
    """Gateway for user-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize gateway with active database session."""
        self.session = session

    async def add_user(self, user: DomainUser) -> DomainUser:
        """Add a new user to the database."""
        logger.debug("Adding new user to database: %s", user.email)
        db_user = map_domain_to_model(user)
        self.session.add(db_user)
        await self.session.flush()
        logger.info("Successfully added user with ID: %s", db_user.id)
        return map_user_to_domain(db_user)

    async def get_user_by_id(self, user_id: uuid.UUID) -> DomainUser | None:
        """Retrieve a user by their UUID."""
        logger.debug("Fetching user by ID: %s", user_id)
        query = select(DBUser).where(DBUser.id == user_id)
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()

        if db_user is None:
            logger.debug("User with ID %s not found", user_id)
            return None
        return map_user_to_domain(db_user)

    async def get_user_by_email(self, email: str) -> DomainUser | None:
        """Retrieve a user by their email address."""
        logger.debug("Fetching user by email: %s", email)
        query = select(DBUser).where(DBUser.email == email)
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()

        if db_user is None:
            logger.debug("User with email %s not found", email)
            return None
        return map_user_to_domain(db_user)

    async def update_user(self, user: DomainUser) -> DomainUser:
        """Update existing user records."""
        logger.debug("Updating user: %s", user.id)
        db_user = map_domain_to_model(user)
        merged_user = await self.session.merge(db_user)
        await self.session.flush()
        logger.info("User updated: %s", user.id)
        return map_user_to_domain(merged_user)
