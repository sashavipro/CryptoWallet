"""sockets/src/presentation/amqp/consumers/transaction.py."""

import logging

from faststream.rabbit import RabbitRouter

from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.tx_status_updated")
async def handle_tx_status_update(payload: dict) -> None:
    """Listen for transaction status updates (PENDING -> SUCCESS/FAILED)."""
    user_id = payload.get("user_id")
    tx_id = payload.get("tx_id")
    status = payload.get("status")
    wallet_id = payload.get("wallet_id")

    if not user_id:
        return

    await sio.emit(
        "transaction_updated",
        {
            "tx_id": tx_id,
            "status": status,
            "message": f"Транзакция перешла в статус {status}",
        },
        room=f"user_{user_id}",
    )
    logger.info("WS: Sent tx %s status (%s) to user %s", tx_id, status, user_id)

    if status == "SUCCESS" and wallet_id:
        await sio.emit(
            "balance_update_required",
            {"wallet_id": wallet_id},
            room=f"user_{user_id}",
        )
        logger.info("WS: Requested balance update for wallet %s", wallet_id)
