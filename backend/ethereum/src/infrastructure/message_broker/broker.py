"""backend/ethereum/src/infrastructure/message_broker/broker.py."""

import asyncio
import logging

from dishka.integrations.taskiq import setup_dishka
from taskiq import TaskiqState

from src.application.ports.providers.web3 import Web3Provider
from src.infrastructure.message_broker.block_subscriber import listen_to_new_blocks
from src.infrastructure.message_broker.broker_instance import broker
from src.ioc.container import create_container

logger = logging.getLogger(__name__)

container = create_container()
setup_dishka(container, broker)


@broker.on_event("startup")
async def startup_event(state: TaskiqState) -> None:
    """Hooks into worker startup to launch the blockchain listener."""
    logger.info("Initializing TaskIQ Worker Background Tasks...")

    state.container = container

    async with container() as request_container:
        web3_provider = await request_container.get(Web3Provider)
        await web3_provider._check_connection()  # noqa: SLF001
        w3 = web3_provider.w3

    state.block_listener_task = asyncio.create_task(listen_to_new_blocks(w3, container))


@broker.on_event("shutdown")
async def shutdown_event(state: TaskiqState) -> None:
    """Cleanup resources on worker shutdown."""
    logger.info("Shutting down TaskIQ Worker Background Tasks...")

    if hasattr(state, "block_listener_task"):
        state.block_listener_task.cancel()

    await state.container.close()
