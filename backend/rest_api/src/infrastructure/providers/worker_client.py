"""rest_api/src/infrastructure/providers/worker_client.py."""

import logging

from faststream.rabbit import RabbitBroker

from src.application.ports.providers.worker_client import EthereumWorkerClient

logger = logging.getLogger(__name__)


class EthereumWorkerClientImpl(EthereumWorkerClient):
    """Ethereum worker client implementation using RabbitMQ RPC."""

    def __init__(self, broker: RabbitBroker) -> None:
        """Initialize the client with a RabbitMQ broker."""
        self.broker = broker

    async def create_wallet(self) -> dict[str, str]:
        """Request wallet generation from the worker."""
        logger.info("RPC Request: eth.create_wallet")
        return await self.broker.request({}, queue="eth.create_wallet")

    async def send_transaction(
        self,
        private_key_encrypted: str,
        from_address: str,
        to_address: str,
        value_eth: str,
    ) -> str:
        """Request that the transaction be sent."""
        payload = {
            "private_key_encrypted": private_key_encrypted,
            "from_address": from_address,
            "to_address": to_address,
            "value_eth": value_eth,
        }
        logger.info("RPC Request: eth.send_transaction")
        return await self.broker.request(payload, queue="eth.send_transaction")

    async def request_faucet(self, address: str) -> str:
        """Request test ETH from the worker faucet."""
        logger.info("RPC Request: eth.request_faucet for %s", address)
        return await self.broker.request(
            {"address": address}, queue="eth.request_faucet"
        )

    async def get_balance(self, address: str) -> str:
        """Retrieve the balance directly from the blockchain via a worker."""
        logger.info("RPC Request: eth.get_balance for %s", address)
        return await self.broker.request(address, queue="eth.get_balance")
