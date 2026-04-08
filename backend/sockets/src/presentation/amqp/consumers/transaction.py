"""sockets/src/presentation/amqp/consumers/transaction.py."""

import logging

from faststream.rabbit import RabbitRouter

from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("ws.tx_updated")
async def handle_tx_status_update(payload: dict) -> None:
    """Listen for transaction status updates and broadcast to WS."""
    user_id = payload.get("user_id")
    tx_hash = payload.get("tx_hash")
    status = payload.get("status")
    wallet_id = payload.get("wallet_id")
    value = payload.get("value")

    if not user_id or not tx_hash:
        return

    await sio.emit(
        "transaction_status_changed",
        {
            "tx_hash": tx_hash,
            "status": status,
            "wallet_id": wallet_id,
            "value": value,
            "message": f"Транзакция перешла в статус {status}",
        },
        room=f"user_{user_id}",
        namespace="/chat",
    )
    logger.info("WS: Sent tx %s status (%s) to user %s", tx_hash, status, user_id)
