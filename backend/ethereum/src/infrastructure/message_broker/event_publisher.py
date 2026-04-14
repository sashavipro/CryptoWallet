"""ethereum/src/infrastructure/message_broker/event_publisher.py."""

import logging

from faststream.rabbit import ExchangeType
from faststream.rabbit import RabbitExchange

from src.application.ports.publishers import EventPublisher
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)

tx_exchange = RabbitExchange("tx_events", type=ExchangeType.TOPIC)


class EventPublisherImpl(EventPublisher):
    """Implementation of EventPublisher using a message broker."""

    async def publish_tx_initiated(self, tx_id: str, tx_hash: str) -> None:
        """Publish an event indicating a transaction was successfully initiated."""
        payload = {"tx_id": tx_id, "tx_hash": tx_hash, "status": "PENDING"}
        logger.info("Publishing tx initiated: %s", tx_hash)

        await broker.publish(
            payload, exchange=tx_exchange, routing_key="eth.tx_initiated"
        )

    async def publish_tx_failed_initiation(self, tx_id: str, error: str) -> None:
        """Publish an event indicating a transaction failed to initiate."""
        payload = {"tx_id": tx_id, "status": "FAILED", "error": error}
        logger.warning("Publishing tx failed initiation: %s", error)

        await broker.publish(
            payload, exchange=tx_exchange, routing_key="eth.tx_failed_initiation"
        )

    async def publish_tx_processed(
        self, tx_id: str | None, tx_hash: str, status: str, fee: str
    ) -> None:
        """Publish an event indicating a transaction was processed on-chain."""
        payload = {"tx_id": tx_id, "tx_hash": tx_hash, "fee": fee}

        if status.lower() == "success":
            logger.info("Publishing tx success: %s", tx_hash)

            await broker.publish(
                payload, exchange=tx_exchange, routing_key="eth.tx_success"
            )
        else:
            payload["error"] = "Transaction reverted on chain"
            logger.info("Publishing tx failed: %s", tx_hash)

            await broker.publish(
                payload, exchange=tx_exchange, routing_key="eth.tx_failed"
            )
