"""rest_api/src/infrastructure/message_broker/worker_client.py."""

import logging

from src.application.ports.providers.worker_client import EthereumWorkerClient
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


class EthereumWorkerClientImpl(EthereumWorkerClient):
    """Implementation of EthereumWorkerClient using FastStream RPC."""

    async def create_wallet(self) -> dict[str, str]:
        """Send an RPC request to create a wallet."""
        logger.info("Sending RPC request: eth.create_wallet")
        return await broker.publish({}, queue="eth.create_wallet", rpc=True)

    async def send_transaction(
        self,
        private_key_encrypted: str,
        from_address: str,
        to_address: str,
        value_eth: str,
    ) -> str:
        """Send an RPC request to execute a transaction."""
        payload = {
            "private_key_encrypted": private_key_encrypted,
            "from_address": from_address,
            "to_address": to_address,
            "value_eth": value_eth,
        }
        logger.info("Sending RPC request: eth.send_transaction")
        return await broker.publish(payload, queue="eth.send_transaction", rpc=True)

    async def get_balance(self, address: str) -> str:
        """Retrieve the balance directly from the worker."""
        logger.info("Sending RPC request: eth.get_balance for %s", address)
        return await broker.publish(address, queue="eth.get_balance", rpc=True)
