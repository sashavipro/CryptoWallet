"""ethereum/src/presentation/amqp/consumers/transaction.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors import CheckTransactionStatusInteractor
from src.application.interactors import SendTransactionInteractor

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.send_transaction")
@inject
async def handle_send_transaction(
    payload: dict,
    interactor: FromDishka[SendTransactionInteractor],
) -> None:
    """Process and execute an Ethereum transaction."""
    await interactor(
        tx_id=payload["tx_id"],
        private_key_encrypted=payload["private_key_encrypted"],
        from_address=payload["from_address"],
        to_address=payload["to_address"],
        value_eth=payload["value_eth"],
    )


@router.subscriber("eth.check_tx_status")
@inject
async def handle_check_tx_status(
    payload: dict, interactor: FromDishka[CheckTransactionStatusInteractor]
) -> dict | None:
    """Return tx status (SUCCESS/FAILED) or None if PENDING."""
    return await interactor(payload["tx_hash"])
