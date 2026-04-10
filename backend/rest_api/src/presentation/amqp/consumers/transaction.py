"""rest_api/src/presentation/amqp/consumers/transaction.py."""

import logging
import uuid

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors.transaction import ProcessTransactionCallbackInteractor

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.tx_initiated")
@inject
async def handle_tx_initiated(
    payload: dict, interactor: FromDishka[ProcessTransactionCallbackInteractor]
) -> None:
    """Process the event triggered when a transaction is successfully initiated."""
    await interactor(
        tx_id=uuid.UUID(payload["tx_id"]), status="pending", tx_hash=payload["tx_hash"]
    )


@router.subscriber("eth.tx_failed_initiation")
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


@router.subscriber("eth.tx_success")
@inject
async def handle_tx_success(
    payload: dict, interactor: FromDishka[ProcessTransactionCallbackInteractor]
) -> None:
    """Process the event triggered when a transaction is successfully mined."""
    tx_id_raw = payload.get("tx_id")
    tx_id = uuid.UUID(tx_id_raw) if tx_id_raw else None
    await interactor(tx_id=tx_id, tx_hash=payload.get("tx_hash"), status="success")


@router.subscriber("eth.tx_failed")
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
