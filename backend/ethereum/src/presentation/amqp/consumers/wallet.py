"""ethereum/src/presentation/amqp/consumers/wallet.py."""

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors.wallet import CreateWalletInteractor
from src.application.interactors.wallet import GetBalanceInteractor
from src.application.interactors.wallet import ImportWalletInteractor

router = RabbitRouter()


@router.subscriber("eth.create_wallet")
@inject
async def handle_create_wallet(interactor: FromDishka[CreateWalletInteractor]):
    """Handle a request to create a new Ethereum wallet."""
    return await interactor()


@router.subscriber("eth.import_wallet")
@inject
async def handle_import_wallet(
    payload: dict, interactor: FromDishka[ImportWalletInteractor]
):
    """Handle a request to import an existing Ethereum wallet by private key."""
    return await interactor(payload["private_key"])


@router.subscriber("eth.get_balance")
@inject
async def handle_get_balance(
    payload: dict, interactor: FromDishka[GetBalanceInteractor]
):
    """Handle a request to get the ETH balance of a specific address."""
    return await interactor(payload["address"])
