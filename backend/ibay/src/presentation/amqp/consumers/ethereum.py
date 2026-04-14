"""ibay/src/presentation/amqp/consumers/ethereum.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors.ibay_worker import UpdateOrderStatusInteractor

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.tx_success")
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


@router.subscriber("eth.tx_failed")
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
