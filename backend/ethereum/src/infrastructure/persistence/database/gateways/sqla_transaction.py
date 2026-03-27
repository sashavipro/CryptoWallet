"""ethereum/src/infrastructure/persistence/database/gateways/sqla_transaction.py."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.transaction import Transaction as DomainTransaction
from src.infrastructure.persistence.database.mappers.transaction import (
    map_domain_to_model,
)
from src.infrastructure.persistence.database.mappers.transaction import (
    map_transaction_to_domain,
)
from src.infrastructure.persistence.database.models.transaction import (
    Transaction as DBTransaction,
)

logger = logging.getLogger(__name__)


class TransactionGateway:
    """Gateway for Transaction database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize gateway with an active database session."""
        self.session = session

    async def add_transaction(
        self, transaction: DomainTransaction
    ) -> DomainTransaction:
        """Add a new transaction (usually in PENDING state) to the database."""
        db_tx = map_domain_to_model(transaction)
        self.session.add(db_tx)
        await self.session.flush()
        logger.info("Transaction added with hash: %s", transaction.tx_hash)
        return map_transaction_to_domain(db_tx)

    async def get_transaction_by_hash(self, tx_hash: str) -> DomainTransaction | None:
        """Retrieve a transaction by its blockchain hash."""
        query = select(DBTransaction).where(DBTransaction.tx_hash == tx_hash)
        result = await self.session.execute(query)
        db_tx = result.scalar_one_or_none()

        return map_transaction_to_domain(db_tx) if db_tx else None

    async def update_transaction(
        self, transaction: DomainTransaction
    ) -> DomainTransaction:
        """Update existing transaction records.

        For example, status changes to SUCCESS or FAILED.
        """
        db_tx = map_domain_to_model(transaction)
        merged_tx = await self.session.merge(db_tx)
        await self.session.flush()
        logger.debug("Transaction updated: %s", transaction.tx_hash)
        return map_transaction_to_domain(merged_tx)
