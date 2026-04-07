"""rest_api/src/presentation/amqp/consumers/transaction.py."""

import logging
import uuid

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.ports.gateways import TransactionGateway
from src.application.ports.gateways import UnitOfWork

logger = logging.getLogger(__name__)

router = RabbitRouter()


@router.subscriber("eth.tx_initiated")
@inject
async def handle_tx_initiated(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    uow: FromDishka[UnitOfWork],
) -> None:
    """Update the transaction hash when a transaction is successfully initiated."""
    tx_id = uuid.UUID(payload["tx_id"])
    tx_hash = payload["tx_hash"]

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.tx_hash = tx_hash
            await tx_gateway.update_transaction(tx)
            logger.info("Transaction %s hash updated to %s", tx_id, tx_hash)


@router.subscriber("eth.tx_failed_initiation")
@inject
async def handle_tx_failed_initiation(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    uow: FromDishka[UnitOfWork],
) -> None:
    """Handle transaction initiation failure."""
    tx_id = uuid.UUID(payload["tx_id"])
    error = payload.get("error", "Unknown error")

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.status = "failed"
            await tx_gateway.update_transaction(tx)
            logger.info("Transaction %s marked as failed: %s", tx_id, error)
