"""ibay/src/presentation/amqp/consumers/ethereum.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import ExchangeType
from faststream.rabbit import RabbitExchange
from faststream.rabbit import RabbitQueue
from faststream.rabbit import RabbitRouter

from src.application.interactors.ibay_worker import UpdateOrderStatusInteractor

logger = logging.getLogger(__name__)
router = RabbitRouter()
tx_exchange = RabbitExchange("tx_events", type=ExchangeType.TOPIC)


@router.subscriber(
    RabbitQueue("ibay_tx_queue", routing_key="eth.tx_success"), exchange=tx_exchange
)
@inject
async def handle_tx_success(
    payload: dict, interactor: FromDishka[UpdateOrderStatusInteractor]
) -> None:
    """Handle successful Ethereum transactions by pushing the order to delivery."""
    tx_id = payload.get("tx_id")
    tx_hash = payload.get("tx_hash")
    if not tx_id or not tx_hash:
        return

    logger.info("Caught eth.tx_success for tx: %s. Pushing order to DELIVERY", tx_hash)
    await interactor(tx_id=tx_id, real_tx_hash=tx_hash, tx_status="success")


@router.subscriber(
    RabbitQueue("ibay_tx_queue", routing_key="eth.tx_failed"), exchange=tx_exchange
)
@inject
async def handle_tx_failed(
    payload: dict, interactor: FromDishka[UpdateOrderStatusInteractor]
) -> None:
    """Handle failed Ethereum transactions by failing the associated order."""
    tx_id = payload.get("tx_id")
    tx_hash = payload.get("tx_hash")
    if not tx_id or not tx_hash:
        return

    logger.warning("Caught eth.tx_failed for tx: %s. Failing order", tx_hash)
    await interactor(tx_id=tx_id, real_tx_hash=tx_hash, tx_status="failed")
