"""ethereum/src/presentation/amqp/consumers.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitBroker
from faststream.rabbit import RabbitRouter

from src.application.interactors.faucet import RequestTestnetEthInteractor
from src.application.interactors.transaction import SendTransactionInteractor
from src.application.interactors.transaction_watcher import (
    CheckTransactionStatusInteractor,
)
from src.application.interactors.wallet import CreateWalletInteractor
from src.application.interactors.wallet import GetBalanceInteractor
from src.application.interactors.wallet import ImportWalletInteractor
from src.application.ports.providers import NonceManager

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
    payload: dict, interactor: FromDishka[GetBalanceInteractor]
) -> str:
    """Retrieve the balance of a specific Ethereum address."""
    return await interactor(payload["address"])


@router.subscriber("eth.send_transaction")
@inject
async def handle_send_transaction(
    payload: dict,
    broker: RabbitBroker,
    interactor: FromDishka[SendTransactionInteractor],
    nonce_manager: FromDishka[NonceManager],
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

        await nonce_manager.increment_nonce(from_address)

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
    payload: dict, interactor: FromDishka[CheckTransactionStatusInteractor]
) -> dict | None:
    """Return tx status (SUCCESS/FAILED) or None if PENDING."""
    return await interactor(payload["tx_hash"])
