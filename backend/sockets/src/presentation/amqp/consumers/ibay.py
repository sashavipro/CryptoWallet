"""sockets/src/presentation/amqp/consumers/ibay.py."""

import logging

from faststream.rabbit import ExchangeType
from faststream.rabbit import RabbitExchange
from faststream.rabbit import RabbitQueue
from faststream.rabbit import RabbitRouter

from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()
ibay_exchange = RabbitExchange("ibay_events", type=ExchangeType.TOPIC, durable=True)


@router.subscriber(
    RabbitQueue("sockets_ibay_product_queue", routing_key="ibay.product_created"),
    exchange=ibay_exchange,
)
async def handle_product_created(payload: dict) -> None:
    """Broadcast new product events to all subscribed customers."""
    product_id = payload.get("product_id")
    if not product_id:
        return

    await sio.emit(
        "ibay_product_created",
        payload,
        room="ibay_global",
        namespace="/ibay",
    )
    logger.info("WS: Broadcasted new product %s to all users", product_id)


@router.subscriber(
    RabbitQueue("sockets_ibay_order_created_queue", routing_key="ibay.order_created"),
    exchange=ibay_exchange,
)
async def handle_order_created(payload: dict) -> None:
    """Track order creation and send a notification only to the buyer."""
    buyer_id = payload.get("buyer_id")
    if not buyer_id:
        return

    await sio.emit(
        "ibay_order_created",
        payload,
        room=f"user_{buyer_id}",
        namespace="/ibay",
    )
    logger.info(
        "WS: Sent order_created for %s to user %s", payload.get("order_id"), buyer_id
    )


@router.subscriber(
    RabbitQueue("sockets_ibay_order_updated_queue", routing_key="ibay.order_updated"),
    exchange=ibay_exchange,
)
async def handle_order_updated(payload: dict) -> None:
    """Monitor order status updates (DELIVERY, COMPLETED, FAILED, RETURNED)."""
    buyer_id = payload.get("buyer_id")
    status = payload.get("status")

    if not buyer_id:
        return

    await sio.emit(
        "ibay_order_updated",
        payload,
        room=f"user_{buyer_id}",
        namespace="/ibay",
    )
    logger.info("WS: Sent order_updated (status: %s) to user %s", status, buyer_id)
