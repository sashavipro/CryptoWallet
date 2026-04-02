"""ethereum/src/presentation/amqp/consumers.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors.transaction import SendTransactionInteractor
from src.application.interactors.wallet import CreateWalletInteractor
from src.application.interactors.wallet import GetBalanceInteractor

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.create_wallet")
@inject
async def handle_create_wallet(
    interactor: FromDishka[CreateWalletInteractor],
) -> dict[str, str]:
    """RPC Endpoint: Creates a wallet and returns data."""
    return await interactor()


@router.subscriber("eth.get_balance")
@inject
async def handle_get_balance(
    address: str, interactor: FromDishka[GetBalanceInteractor]
) -> str:
    """RPC Endpoint: Returns the balance for a given address."""
    return await interactor(address)


@router.subscriber("eth.send_transaction")
@inject
async def handle_send_transaction(
    payload: dict, interactor: FromDishka[SendTransactionInteractor]
) -> str:
    """RPC Endpoint: Sends a transaction and returns the tx_hash."""
    return await interactor(
        private_key_encrypted=payload["private_key_encrypted"],
        from_address=payload["from_address"],
        to_address=payload["to_address"],
        value_eth=payload["value_eth"],
    )
