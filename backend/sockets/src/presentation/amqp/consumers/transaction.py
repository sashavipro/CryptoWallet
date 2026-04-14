"""sockets/src/presentation/amqp/consumers/transaction.py."""

import logging

from faststream.rabbit import ExchangeType
from faststream.rabbit import RabbitExchange
from faststream.rabbit import RabbitQueue
from faststream.rabbit import RabbitRouter

from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()
ws_exchange = RabbitExchange("ws_events", type=ExchangeType.TOPIC)


@router.subscriber(
    RabbitQueue("sockets_tx_queue", routing_key="ws.tx_updated"), exchange=ws_exchange
)
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
        namespace="/transaction",
    )
    logger.info("WS: Sent tx %s status (%s) to user %s", tx_hash, status, user_id)


@router.subscriber(
    RabbitQueue("sockets_tx_queue", routing_key="ws.balance_updated"),
    exchange=ws_exchange,
)
async def handle_balance_updated(payload: dict) -> None:
    """Listen for balance updates and broadcast to WS."""
    user_id = payload.get("user_id")
    wallet_id = payload.get("wallet_id")
    balance = payload.get("balance")

    if not user_id or not wallet_id:
        return

    await sio.emit(
        "balance_updated",
        {
            "wallet_id": wallet_id,
            "balance": balance,
        },
        room=f"user_{user_id}",
        namespace="/transaction",
    )
    logger.info("WS: Sent balance %s to wallet %s", balance, wallet_id)
