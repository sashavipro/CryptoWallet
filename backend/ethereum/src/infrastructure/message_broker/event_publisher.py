"""ethereum/src/infrastructure/message_broker/event_publisher.py."""

import logging

from src.application.ports.publishers import EventPublisher
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


class EventPublisherImpl(EventPublisher):
    """Implementation of EventPublisher using a message broker."""

    async def publish_tx_initiated(self, tx_id: str, tx_hash: str) -> None:
        """Publish an event indicating a transaction was successfully initiated."""
        payload = {"tx_id": tx_id, "tx_hash": tx_hash, "status": "PENDING"}
        logger.info("Publishing tx initiated: %s", tx_hash)
        await broker.publish(payload, queue="eth.tx_initiated")

    async def publish_tx_failed_initiation(self, tx_id: str, error: str) -> None:
        """Publish an event indicating a transaction failed to initiate."""
        payload = {"tx_id": tx_id, "status": "FAILED", "error": error}
        logger.warning("Publishing tx failed initiation: %s", error)
        await broker.publish(payload, queue="eth.tx_failed_initiation")
