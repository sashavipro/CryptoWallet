"""ethereum/src/presentation/http/routers/faucet.py."""

import uuid

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import status

from src.application.dtos.response import TransactionResponse
from src.application.interactors.faucet import RequestTestnetEthInteractor
from src.domain.exceptions import AssetNotFoundException
from src.domain.exceptions import WalletNotFoundException
from src.presentation.http.dependencies.auth import CurrentUserId
from src.presentation.http.responses import create_error_responses

router = APIRouter(prefix="/api/v1/faucet", tags=["faucet"])


@router.post(
    "/{wallet_id}/request-eth",
    response_model=TransactionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses=create_error_responses(
        WalletNotFoundException,
        AssetNotFoundException,
    ),
    summary="Request Testnet ETH",
    description=(
        "Request a small amount of test ETH from the faucet for a user's wallet."
    ),
)
@inject
async def request_testnet_eth(
    wallet_id: uuid.UUID,
    user_id: CurrentUserId,
    interactor: FromDishka[RequestTestnetEthInteractor],
) -> TransactionResponse:
    """Request testnet ETH from the faucet."""
    return await interactor(wallet_id)
