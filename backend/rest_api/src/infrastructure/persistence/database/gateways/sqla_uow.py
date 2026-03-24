"""rest_api/src/infrastructure/persistence/database/gateways/sqla_uow.py."""

import logging
import types

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SqlaUnitOfWork:
    """Implementation of UoW for SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the UoW with a database session."""
        self.session = session

    async def __aenter__(self) -> "SqlaUnitOfWork":
        """Enter the transaction context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit the transaction context."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        """Commit the current transaction."""
        logger.debug("Committing transaction")
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        logger.warning("Rolling back transaction due to an exception")
        await self.session.rollback()
