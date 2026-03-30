"""ethereum/src/infrastructure/message_broker/block_subscriber.py."""

import asyncio
import json
import logging

from dishka import AsyncContainer
from web3 import AsyncWeb3

from src.application.interactors import ProcessNewBlockInteractor

logger = logging.getLogger(__name__)


async def listen_to_new_blocks(w3: AsyncWeb3, container: AsyncContainer) -> None:
    """Infinite loop subscribing to new block headers via WSS."""
    logger.info("Starting Web3 Block Header Subscriber...")

    while True:
        try:
            if not await w3.is_connected():
                logger.warning("Web3 not connected. Reconnecting in 5s...")
                await asyncio.sleep(5)
                continue

            sub_id = await w3.eth.subscribe("newHeads")
            logger.info(
                "Successfully subscribed to newHeads! Subscription ID: %s", sub_id
            )

            async for message in w3.ws.listen_to_websocket():
                data = json.loads(message)

                if "params" in data and "result" in data["params"]:
                    block_hash = data["params"]["result"]["hash"]
                    logger.debug("New block detected! Hash: %s", block_hash)

                    async with container() as request_container:
                        interactor = await request_container.get(
                            ProcessNewBlockInteractor
                        )
                        await interactor(block_hash)

        except Exception:
            logger.exception("Web3 Subscription dropped or failed. Retrying...")
            await asyncio.sleep(5)
