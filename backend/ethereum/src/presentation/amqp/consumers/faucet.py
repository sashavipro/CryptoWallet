"""ethereum/src/presentation/amqp/consumers/faucet.py."""

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.interactors.faucet import RequestTestnetEthInteractor

router = RabbitRouter()


@router.subscriber("eth.request_faucet")
@inject
async def handle_request_faucet(
    payload: dict, interactor: FromDishka[RequestTestnetEthInteractor]
) -> str:
    """Send test ETH to the specified address and return the tx_hash."""
    return await interactor(to_address=payload["address"])
