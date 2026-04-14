"""sockets/src/presentation/amqp/consumers/stats.py."""

import logging

from faststream.rabbit import ExchangeType
from faststream.rabbit import RabbitExchange
from faststream.rabbit import RabbitQueue
from faststream.rabbit import RabbitRouter

from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()
chat_exchange = RabbitExchange("chat_events", type=ExchangeType.TOPIC)


@router.subscriber(
    RabbitQueue("sockets_chat_queue", routing_key="chat.broadcast_message"),
    exchange=chat_exchange,
)
async def handle_stats_updated(payload: dict) -> None:
    """Listen for stats updates and push them to the specific user via WS."""
    user_id = payload.pop("user_id", None)

    if not user_id:
        return

    if payload:
        await sio.emit(
            "stats_updated",
            payload,
            room=f"user_{user_id}",
            namespace="/transaction",
        )
        logger.info("WS: Pushed stats update to user %s: %s", user_id, payload)
