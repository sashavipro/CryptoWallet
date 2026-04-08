"""ethereum/src/presentation/amqp/consumers/transaction.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream import Context
from faststream.rabbit import RabbitBroker
from faststream.rabbit import RabbitRouter

from src.application.interactors.transaction import SendTransactionInteractor
from src.application.interactors.transaction_watcher import (
    CheckTransactionStatusInteractor,
)
from src.application.ports.providers import NonceManager

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.send_transaction")
@inject
async def handle_send_transaction(
    payload: dict,
    interactor: FromDishka[SendTransactionInteractor],
    nonce_manager: FromDishka[NonceManager],
    broker: RabbitBroker = Context(),  # noqa: B008
) -> None:
    """Process and execute an Ethereum transaction."""
    tx_id = payload["tx_id"]
    from_address = payload["from_address"]

    try:
        tx_hash = await interactor(
            private_key_encrypted=payload["private_key_encrypted"],
            from_address=from_address,
            to_address=payload["to_address"],
            value_eth=payload["value_eth"],
        )

        await broker.publish(
            {"tx_id": tx_id, "tx_hash": tx_hash, "status": "PENDING"},
            queue="eth.tx_initiated",
        )
    except Exception as e:
        logger.exception("Failed to send tx %s", tx_id)

        await broker.publish(
            {"tx_id": tx_id, "status": "FAILED", "error": str(e)},
            queue="eth.tx_failed_initiation",
        )


@router.subscriber("eth.check_tx_status")
@inject
async def handle_check_tx_status(
    payload: dict, interactor: FromDishka[CheckTransactionStatusInteractor]
) -> dict | None:
    """Return tx status (SUCCESS/FAILED) or None if PENDING."""
    return await interactor(payload["tx_hash"])
