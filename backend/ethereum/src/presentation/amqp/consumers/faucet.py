"""ethereum/src/presentation/amqp/consumers/faucet.py."""

import asyncio

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors.faucet import RequestTestnetEthInteractor
from src.application.interactors.transaction_watcher import (
    BackgroundTransactionWatcherInteractor,
)

router = RabbitRouter()
background_tasks = set()


@router.subscriber("eth.request_faucet")
@inject
async def handle_request_faucet(
    payload: dict,
    interactor: FromDishka[RequestTestnetEthInteractor],
    watcher_interactor: FromDishka[BackgroundTransactionWatcherInteractor],
):
    """Handle a request to receive testnet ETH from the faucet."""
    tx_hash = await interactor(to_address=payload["address"])
    if tx_hash:
        task = asyncio.create_task(watcher_interactor(tx_hash=tx_hash))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
    return tx_hash
