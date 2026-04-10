"""rest_api/src/infrastructure/message_broker/event_publisher.py."""

import logging
import uuid

from src.application.ports.events import EventPublisher
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


class EventPublisherImpl(EventPublisher):
    """Implementation of EventPublisher using FastStream."""

    async def publish_user_registered(
        self, user_id: uuid.UUID, email: str, username: str
    ) -> None:
        """Publish an event to RabbitMQ when a user registers."""
        payload = {
            "user_id": str(user_id),
            "email": email,
            "username": username,
        }
        logger.info("Publishing event: user_events.registered for %s", email)
        await broker.publish(payload, queue="user_events.registered")

    async def publish_stats_updated(
        self,
        user_id: uuid.UUID,
        messages_count: int | None = None,
        wallets_count: int | None = None,
    ) -> None:
        """Publish an event to notify that user statistics have been updated."""
        payload = {"user_id": str(user_id)}

        if messages_count is not None:
            payload["messages_count"] = messages_count
        if wallets_count is not None:
            payload["wallets_count"] = wallets_count

        logger.info("Publishing stats update for user: %s", user_id)
        await broker.publish(payload, queue="stats.updated")

    async def publish_tx_status_updated(  # noqa: PLR0913
        self,
        user_id: str,
        wallet_id: str,
        tx_hash: str,
        status: str,
        value: str,
        error: str | None = None,
    ) -> None:
        """Publish a transaction status update event to the WebSocket queue."""
        payload = {
            "user_id": user_id,
            "wallet_id": wallet_id,
            "tx_hash": tx_hash,
            "status": status,
            "value": value,
        }
        if error:
            payload["error"] = error

        logger.info("Publishing tx status update to WS: %s", tx_hash)
        await broker.publish(payload, queue="ws.tx_updated")

    async def publish_balance_updated(
        self, user_id: str, wallet_id: str, balance: str
    ) -> None:
        """Publish a wallet balance update event to the WebSocket queue."""
        payload = {
            "user_id": user_id,
            "wallet_id": wallet_id,
            "balance": balance,
        }
        logger.info("Publishing balance update to WS for wallet: %s", wallet_id)
        await broker.publish(payload, queue="ws.balance_updated")
