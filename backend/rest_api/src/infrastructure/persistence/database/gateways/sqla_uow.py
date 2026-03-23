"""rest_api/src/infrastructure/persistence/database/gateways/sqla_uow.py."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SqlaUnitOfWork:
    """Implementation of UoW for SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the UoW with a database session."""
        self.session = session

    async def commit(self) -> None:
        """Commit the current transaction."""
        logger.debug("Committing transaction")
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        logger.debug("Rolling back transaction")
        await self.session.rollback()
