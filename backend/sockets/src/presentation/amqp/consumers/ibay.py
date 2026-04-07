"""sockets/src/presentation/amqp/consumers/ibay.py."""

import logging

from faststream.rabbit import RabbitRouter

from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("ibay.product_created")
async def handle_ibay_product_created(payload: dict) -> None:
    """Broadcast new iBay products to all connected users."""
    await sio.emit("product_created", payload, room="ibay_global")
    logger.info("WS: Broadcasted new iBay product: %s", payload.get("product_id"))


@router.subscriber("ibay.order_status_updated")
async def handle_ibay_order_updated(payload: dict) -> None:
    """Notify a user about their iBay order status (DELIVERY, COMPLETED, etc.)."""
    buyer_id = payload.get("buyer_id")
    status = payload.get("status")
    order_id = payload.get("order_id")

    if not buyer_id:
        return

    await sio.emit(
        "order_updated",
        {
            "order_id": order_id,
            "status": status,
            "message": f"Your order status has been updated: {status}",
        },
        room=f"user_{buyer_id}",
    )
    logger.info("WS: Sent order %s update (%s) to user %s", order_id, status, buyer_id)
