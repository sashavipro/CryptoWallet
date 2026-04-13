"""ibay/src/presentation/amqp/consumers/transaction.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors.ibay_worker import UpdateOrderStatusInteractor

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.tx_success")
@inject
async def handle_payment_success(
    payload: dict, interactor: FromDishka[UpdateOrderStatusInteractor]
) -> None:
    """Listen for successful transactions (this might be payment for a lot)."""
    tx_hash = payload.get("tx_hash")
    if tx_hash:
        await interactor(tx_hash=tx_hash, tx_status="success")


@router.subscriber("eth.tx_failed")
@inject
async def handle_payment_failed(
    payload: dict, interactor: FromDishka[UpdateOrderStatusInteractor]
) -> None:
    """Listen for failed transactions."""
    tx_hash = payload.get("tx_hash")
    if tx_hash:
        await interactor(tx_hash=tx_hash, tx_status="failed")
