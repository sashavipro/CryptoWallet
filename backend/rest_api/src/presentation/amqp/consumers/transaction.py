"""rest_api/src/presentation/amqp/consumers/transaction.py."""

import logging
import uuid

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import ExchangeType
from faststream.rabbit import RabbitExchange
from faststream.rabbit import RabbitQueue
from faststream.rabbit import RabbitRouter

from src.application.interactors.transaction import ProcessTransactionCallbackInteractor

logger = logging.getLogger(__name__)
router = RabbitRouter()

tx_exchange = RabbitExchange("tx_events", type=ExchangeType.TOPIC)


@router.subscriber(
    RabbitQueue("rest_api_tx_queue", routing_key="eth.tx_initiated"),
    exchange=tx_exchange,
)
@inject
async def handle_tx_initiated(
    payload: dict, interactor: FromDishka[ProcessTransactionCallbackInteractor]
) -> None:
    """Process the event triggered when a transaction is successfully initiated."""
    await interactor(
        tx_id=uuid.UUID(payload["tx_id"]), status="pending", tx_hash=payload["tx_hash"]
    )


@router.subscriber(
    RabbitQueue("rest_api_tx_queue", routing_key="eth.tx_failed_initiation"),
    exchange=tx_exchange,
)
@inject
async def handle_tx_failed_initiation(
    payload: dict, interactor: FromDishka[ProcessTransactionCallbackInteractor]
) -> None:
    """Process the event triggered when a transaction fails to initiate."""
    await interactor(
        tx_id=uuid.UUID(payload["tx_id"]),
        status="failed",
        error=payload.get("error", "Unknown error"),
    )


@router.subscriber(
    RabbitQueue("rest_api_tx_queue", routing_key="eth.tx_success"), exchange=tx_exchange
)
@inject
async def handle_tx_success(
    payload: dict, interactor: FromDishka[ProcessTransactionCallbackInteractor]
) -> None:
    """Process the event triggered when a transaction is successfully mined."""
    tx_id_raw = payload.get("tx_id")
    tx_id = uuid.UUID(tx_id_raw) if tx_id_raw else None
    await interactor(tx_id=tx_id, tx_hash=payload.get("tx_hash"), status="success")


@router.subscriber(
    RabbitQueue("rest_api_tx_queue", routing_key="eth.tx_failed"), exchange=tx_exchange
)
@inject
async def handle_tx_failed(
    payload: dict, interactor: FromDishka[ProcessTransactionCallbackInteractor]
) -> None:
    """Process the event triggered when a transaction execution fails on-chain."""
    tx_id_raw = payload.get("tx_id")
    tx_id = uuid.UUID(tx_id_raw) if tx_id_raw else None
    await interactor(
        tx_id=tx_id,
        tx_hash=payload.get("tx_hash"),
        status="failed",
        error=payload.get("error", "Unknown error"),
    )
