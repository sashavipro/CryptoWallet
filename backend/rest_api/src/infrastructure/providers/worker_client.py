"""rest_api/src/infrastructure/providers/worker_client.py."""

import json
import logging

from faststream.rabbit import RabbitBroker

from src.application.ports.providers.worker_client import EthereumWorkerClient

logger = logging.getLogger(__name__)


class EthereumWorkerClientImpl(EthereumWorkerClient):
    """Ethereum worker client implementation using RabbitMQ RPC."""

    def __init__(self, broker: RabbitBroker) -> None:
        """Initialize the client with a RabbitMQ broker."""
        self.broker = broker

    def _decode_message(self, response):
        """Safely decode the RabbitMessage body into a Python dict/string."""
        if hasattr(response, "body"):
            body = response.body

            if isinstance(body, bytes):
                body_str = body.decode("utf-8")
            elif isinstance(body, str):
                body_str = body
            else:
                return body

            try:
                return json.loads(body_str)
            except json.JSONDecodeError:
                return body_str

        return response

    async def create_wallet(self) -> dict[str, str]:
        """Request wallet generation from the worker."""
        logger.info("RPC Request: eth.create_wallet")
        response = await self.broker.request(
            {}, queue="eth.create_wallet", timeout=15.0
        )
        return self._decode_message(response)

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
        response = await self.broker.request(
            payload, queue="eth.send_transaction", timeout=15.0
        )
        return self._decode_message(response)

    async def request_faucet(self, address: str) -> str:
        """Request test ETH from the worker faucet."""
        logger.info("RPC Request: eth.request_faucet for %s", address)
        response = await self.broker.request(
            {"address": address}, queue="eth.request_faucet", timeout=15.0
        )
        return self._decode_message(response)

    async def get_balance(self, address: str) -> str:
        """Retrieve the balance directly from the blockchain via a worker."""
        logger.info("RPC Request: eth.get_balance for %s", address)
        try:
            response = await self.broker.request(
                address, queue="eth.get_balance", timeout=15.0
            )
            return self._decode_message(response)
        except TimeoutError:
            logger.exception("Worker timeout: couldn't get balance for %s", address)
            return "0.0"

    async def import_wallet(self, private_key: str) -> dict[str, str]:
        """Request existing wallet import/validation from the worker."""
        logger.info("RPC Request: eth.import_wallet")
        response = await self.broker.request(
            {"private_key": private_key}, queue="eth.import_wallet", timeout=15.0
        )
        return self._decode_message(response)

    async def check_tx_status(self, tx_hash: str) -> dict | None:
        """Check real-time transaction status from Web3."""
        logger.info("RPC Request: eth.check_tx_status for %s", tx_hash)
        response = await self.broker.request(
            tx_hash, queue="eth.check_tx_status", timeout=15.0
        )
        return self._decode_message(response)

    async def publish_send_transaction_event(
        self,
        tx_id: str,
        private_key_encrypted: str,
        from_address: str,
        to_address: str,
        value_eth: str,
    ) -> None:
        """Publish transaction to RabbitMQ (Fire and forget)."""
        payload = {
            "tx_id": tx_id,
            "private_key_encrypted": private_key_encrypted,
            "from_address": from_address,
            "to_address": to_address,
            "value_eth": value_eth,
        }
        logger.info("Publishing async event: eth.send_transaction for tx_id %s", tx_id)
        await self.broker.publish(payload, queue="eth.send_transaction")
