"""rest_api/src/presentation/amqp/consumers.py."""

import logging
import uuid

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.ports.gateways.transaction import TransactionGateway
from src.application.ports.gateways.uow import UnitOfWork

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.tx_initiated")
@inject
async def handle_tx_initiated(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    uow: FromDishka[UnitOfWork],
):
    """Update the transaction hash when a transaction is successfully initiated."""
    tx_id = uuid.UUID(payload["tx_id"])
    tx_hash = payload["tx_hash"]

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.tx_hash = tx_hash
            await tx_gateway.update_transaction(tx)


@router.subscriber("eth.tx_failed_initiation")
@inject
async def handle_tx_failed_initiation(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    uow: FromDishka[UnitOfWork],
):
    """Mark a transaction as failed if it could not be initiated."""
    tx_id = uuid.UUID(payload["tx_id"])

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.mark_failed()
            await tx_gateway.update_transaction(tx)
