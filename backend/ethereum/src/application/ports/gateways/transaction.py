"""ethereum/src/application/ports/gateways/transaction.py."""

from typing import Protocol

from src.domain.entities import Transaction


class TransactionGateway(Protocol):
    """Port for Transaction database operations."""

    async def add_transaction(self, transaction: Transaction) -> Transaction:
        """Add a new transaction to the database."""
        ...

    async def get_transaction_by_hash(self, tx_hash: str) -> Transaction | None:
        """Retrieve a transaction by its blockchain hash."""
        ...

    async def update_transaction(self, transaction: Transaction) -> Transaction:
        """Update existing transaction records."""
        ...
