"""ethereum/src/application/ports/events.py."""

import uuid
from decimal import Decimal
from typing import Protocol


class EventPublisher(Protocol):
    """Port for publishing integration events to a message broker."""

    async def publish_balance_updated(
        self, user_id: uuid.UUID, wallet_id: uuid.UUID, new_balance: Decimal
    ) -> None:
        """Publish an event indicating a user's balance has changed."""
        ...

    async def publish_transaction_status_updated(
        self, user_id: uuid.UUID, tx_id: uuid.UUID, new_status: str, tx_hash: str
    ) -> None:
        """Publish an event indicating a transaction's status has changed."""
        ...
