"""sockets/src/presentation/amqp/consumers/stats.py."""

import logging

from faststream.rabbit import RabbitRouter

from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("stats.updated")
async def handle_stats_updated(payload: dict) -> None:
    """Listen for stats updates and push them to the specific user via WS."""
    user_id = payload.get("user_id")
    messages_count = payload.get("messages_count")
    wallets_count = payload.get("wallets_count")

    if not user_id:
        return

    await sio.emit(
        "stats_updated",
        {
            "messages_count": messages_count,
            "wallets_count": wallets_count,
        },
        room=f"user_{user_id}",
        namespace="/transaction",
    )
    logger.info("WS: Pushed stats update to user %s", user_id)
