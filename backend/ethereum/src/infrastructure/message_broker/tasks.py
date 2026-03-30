"""ethereum/src/infrastructure/message_broker/tasks.py."""

import logging

from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


@broker.task(task_name="balance.updated")
async def publish_balance_updated_task(
    user_id: str, wallet_id: str, new_balance: str
) -> None:
    """Task signature for balance updated event.

    The actual consumption and WebSocket notification happens
    in the 'sockets' microservice.
    """
    logger.info(
        "Event Received/Published: Balance for user %s, wallet %s updated to %s",
        user_id,
        wallet_id,
        new_balance,
    )


@broker.task(task_name="transaction.status_updated")
async def publish_transaction_status_updated_task(
    user_id: str, tx_id: str, new_status: str, tx_hash: str
) -> None:
    """Task signature for transaction status updated event.

    The actual consumption and WebSocket notification happens
    in the 'sockets' microservice.
    """
    logger.info(
        "Event Received/Published: Transaction %s for user %s, hash %s updated to %s",
        tx_id,
        user_id,
        tx_hash,
        new_status,
    )
