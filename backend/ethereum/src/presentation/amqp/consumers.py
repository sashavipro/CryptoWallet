"""ethereum/src/presentation/amqp/consumers.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors.faucet import RequestTestnetEthInteractor
from src.application.interactors.transaction import SendTransactionInteractor
from src.application.interactors.transaction_watcher import (
    CheckTransactionStatusInteractor,
)
from src.application.interactors.wallet import CreateWalletInteractor
from src.application.interactors.wallet import GetBalanceInteractor
from src.application.interactors.wallet import ImportWalletInteractor

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.create_wallet")
@inject
async def handle_create_wallet(
    interactor: FromDishka[CreateWalletInteractor],
) -> dict[str, str]:
    """Handle the creation of a new Ethereum wallet."""
    return await interactor()


@router.subscriber("eth.import_wallet")
@inject
async def handle_import_wallet(
    payload: dict, interactor: FromDishka[ImportWalletInteractor]
) -> dict[str, str]:
    """Retrieve the address from the key and return it with the encrypted key."""
    return await interactor(payload["private_key"])


@router.subscriber("eth.get_balance")
@inject
async def handle_get_balance(
    address: str, interactor: FromDishka[GetBalanceInteractor]
) -> str:
    """Retrieve the balance of a specific Ethereum address."""
    return await interactor(address)


@router.subscriber("eth.send_transaction")
@inject
async def handle_send_transaction(
    payload: dict, interactor: FromDishka[SendTransactionInteractor]
) -> str:
    """Handle broadcasting a transaction to the Ethereum network."""
    return await interactor(
        private_key_encrypted=payload["private_key_encrypted"],
        from_address=payload["from_address"],
        to_address=payload["to_address"],
        value_eth=payload["value_eth"],
    )


@router.subscriber("eth.request_faucet")
@inject
async def handle_request_faucet(
    payload: dict, interactor: FromDishka[RequestTestnetEthInteractor]
) -> str:
    """Send test ETH to the specified address and return the tx_hash."""
    return await interactor(to_address=payload["address"])


@router.subscriber("eth.check_tx_status")
@inject
async def handle_check_tx_status(
    tx_hash: str, interactor: FromDishka[CheckTransactionStatusInteractor]
) -> dict | None:
    """Return tx status (SUCCESS/FAILED) or None if PENDING."""
    return await interactor(tx_hash)
