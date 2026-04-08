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
