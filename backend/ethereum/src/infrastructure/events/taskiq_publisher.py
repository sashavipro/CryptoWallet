"""ethereum/src/infrastructure/events/taskiq_publisher.py."""

import uuid
from decimal import Decimal

from src.application.ports.events import EventPublisher
from src.infrastructure.message_broker import publish_balance_updated_task
from src.infrastructure.message_broker import publish_transaction_status_updated_task


class TaskiqEventPublisherImpl(EventPublisher):
    """Implementation of EventPublisher using TaskIQ and RabbitMQ."""

    async def publish_balance_updated(
        self, user_id: uuid.UUID, wallet_id: uuid.UUID, new_balance: Decimal
    ) -> None:
        """Publish an event indicating a user's balance has changed."""
        await publish_balance_updated_task.kiq(
            str(user_id), str(wallet_id), str(new_balance)
        )

    async def publish_transaction_status_updated(
        self, user_id: uuid.UUID, tx_id: uuid.UUID, new_status: str, tx_hash: str
    ) -> None:
        """Publish an event indicating a transaction's status has changed."""
        await publish_transaction_status_updated_task.kiq(
            str(user_id), str(tx_id), new_status, tx_hash
        )
