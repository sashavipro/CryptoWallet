"""sockets/src/presentation/amqp/consumers/chat.py."""

import logging

from faststream.rabbit import RabbitRouter

from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("chat.broadcast_message")
async def handle_broadcast_message(payload: dict) -> None:
    """Retrieve a saved message from the broker and instantly broadcast it."""
    room_id = payload.get("room_id")

    if not room_id:
        return

    await sio.emit("new_message", payload, room=room_id, namespace="/chat")
    logger.info("WS: Broadcasted new message to chat room %s", room_id)
