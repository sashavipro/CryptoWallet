"""rest_api/src/presentation/amqp/consumers.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.ports.gateways.transaction import TransactionGateway
from src.application.ports.gateways.uow import UnitOfWork

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.tx_status_updated")
@inject
async def handle_tx_status_updated(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    uow: FromDishka[UnitOfWork],
):
    """Слушатель: воркер сообщает, что транзакция в сети ETH завершена."""
    tx_hash = payload["tx_hash"]
    new_status = payload["status"]  # "SUCCESS" или "FAILED"
    fee = payload.get("tx_fee", "0")

    logger.info("Received update for tx %s: %s", tx_hash, new_status)

    tx = await tx_gateway.get_transaction_by_hash(tx_hash)
    if tx:
        async with uow:
            if new_status == "SUCCESS":
                tx.mark_success(fee=fee)
            else:
                tx.mark_failed()
            await tx_gateway.update_transaction(tx)
