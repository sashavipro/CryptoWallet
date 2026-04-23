"""sockets/src/presentation/amqp/consumers/stats.py."""

import logging

from faststream.rabbit import RabbitQueue
from faststream.rabbit import RabbitRouter

from src.infrastructure.message_broker.event_publisher import stats_exchange
from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber(
    RabbitQueue("sockets_stats_queue", routing_key="stats.updated"),
    exchange=stats_exchange,
)
async def handle_stats_updated(payload: dict) -> None:
    """Push updated user statistics to the specific user via WebSocket."""
    user_id = payload.pop("user_id", None)
    if not user_id:
        return
    await sio.emit(
        "stats_updated", payload, room=f"user_{user_id}", namespace="/transaction"
    )
    logger.info("WS: Pushed stats update to user %s", user_id)
