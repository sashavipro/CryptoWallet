"""ethereum/src/presentation/amqp/consumers/transaction.py."""

import asyncio
import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors import CheckTransactionStatusInteractor
from src.application.interactors import SendTransactionInteractor
from src.application.interactors.transaction_watcher import (
    BackgroundTransactionWatcherInteractor,
)

logger = logging.getLogger(__name__)
router = RabbitRouter()

background_tasks = set()


@router.subscriber("eth.send_transaction")
@inject
async def handle_send_transaction(
    payload: dict,
    interactor: FromDishka[SendTransactionInteractor],
    watcher_interactor: FromDishka[BackgroundTransactionWatcherInteractor],
) -> None:
    """Process and execute an Ethereum transaction."""
    tx_hash = await interactor(
        tx_id=payload["tx_id"],
        private_key_encrypted=payload["private_key_encrypted"],
        from_address=payload["from_address"],
        to_address=payload["to_address"],
        value_eth=payload["value_eth"],
    )

    if tx_hash:
        task = asyncio.create_task(
            watcher_interactor(tx_hash=tx_hash, tx_id=payload["tx_id"])
        )
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)


@router.subscriber("eth.check_tx_status")
@inject
async def handle_check_tx_status(
    payload: dict, interactor: FromDishka[CheckTransactionStatusInteractor]
) -> dict | None:
    """Return tx status (SUCCESS/FAILED) or None if PENDING."""
    return await interactor(payload["tx_hash"])
