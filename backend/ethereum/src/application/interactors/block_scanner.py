"""ethereum/src/application/interactors/block_scanner.py."""

import asyncio
import json
import logging
from collections.abc import Mapping

import websockets
from redis.asyncio import Redis

from src.application.ports.providers.web3 import Web3Provider
from src.application.ports.publishers import EventPublisher
from src.infrastructure.settings import Web3Settings

logger = logging.getLogger(__name__)


class BlockScannerInteractor:
    """Use Case: Scan Ethereum blocks via WebSockets to detect relevant transactions."""

    def __init__(
        self,
        web3_provider: Web3Provider,
        redis: Redis,
        event_publisher: EventPublisher,
        settings: Web3Settings,
    ):
        """Initialize the scanner with providers, redis cache, and publisher."""
        self.web3_provider = web3_provider
        self.redis = redis
        self.event_publisher = event_publisher
        self.wss_url = next(
            (
                url
                for url in settings.WEB3_PROVIDER_URI.split(",")
                if url.startswith("ws")
            ),
            None,
        )
        self._background_tasks = set()

    async def __call__(self):
        """Start the infinite loop to subscribe to new block headers."""
        if not self.wss_url:
            logger.error("WSS URL not provided! Block Scanner disabled.")
            return

        logger.info("Starting Block Scanner on %s", self.wss_url)
        while True:
            try:
                async with websockets.connect(self.wss_url) as ws:
                    subscribe_msg = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "eth_subscribe",
                        "params": ["newHeads"],
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    response = await ws.recv()
                    logger.info("Subscribed to newHeads: %s", response)

                    while True:
                        message = await asyncio.wait_for(ws.recv(), timeout=60)
                        data = json.loads(message)
                        if "params" in data and "result" in data["params"]:
                            block_number_hex = data["params"]["result"].get("number")
                            if block_number_hex:
                                task = asyncio.create_task(
                                    self.process_block(block_number_hex)
                                )
                                self._background_tasks.add(task)
                                task.add_done_callback(self._background_tasks.discard)
            except Exception:
                logger.exception(
                    "Block scanner WSS connection error. Reconnecting in 5s..."
                )
                await asyncio.sleep(5)

    async def process_block(self, block_number_hex: str):
        """Fetch full block data and emit events for tracked wallet transactions."""
        try:
            w3 = await self.web3_provider._get_working_w3()  # noqa: SLF001

            block_number = int(block_number_hex, 16)

            block = await w3.eth.get_block(block_number, full_transactions=True)
            if not block or not block.get("transactions"):
                return

            tracked_wallets = await self.redis.smembers("tracked_wallets")
            if not tracked_wallets:
                return

            logger.info(
                "Scanning block %s (%d txs)",
                block.get("number"),
                len(block["transactions"]),
            )

            for tx in block["transactions"]:
                if not isinstance(tx, Mapping):
                    continue

                to_addr = (tx.get("to") or "").lower()
                from_addr = (tx.get("from") or "").lower()

                if to_addr in tracked_wallets or from_addr in tracked_wallets:
                    tx_hash_obj = tx.get("hash")
                    tx_hash = (
                        tx_hash_obj.hex()
                        if isinstance(tx_hash_obj, bytes)
                        else str(tx_hash_obj)
                    )

                    if not tx_hash.startswith("0x"):
                        tx_hash = f"0x{tx_hash}"

                    receipt = await w3.eth.get_transaction_receipt(tx_hash)
                    if receipt and receipt.get("status") == 1:
                        value_wei = tx.get("value", 0)
                        value_eth = w3.from_wei(value_wei, "ether")
                        gas_used = receipt.get("gasUsed", 0)
                        effective_gas_price = receipt.get("effectiveGasPrice", 0)
                        fee_eth = w3.from_wei(gas_used * effective_gas_price, "ether")

                        logger.info(
                            "FOUND tracked TX: %s. Value: %s ETH", tx_hash, value_eth
                        )

                        await self.event_publisher.publish_tx_discovered(
                            tx_hash=tx_hash,
                            from_address=from_addr,
                            to_address=to_addr,
                            value=str(value_eth),
                            fee=str(fee_eth),
                        )
        except Exception:
            logger.exception("Error processing block %s", block_number_hex)
