"""ethereum/src/presentation/http/routers/transaction.py."""

import uuid
from typing import Any

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import status

from src.application.dtos.request import CreatePendingTransactionRequest
from src.application.dtos.response import TransactionResponse
from src.application.interactors.transaction import CreatePendingTransactionInteractor
from src.application.interactors.transaction import GetTransactionsInteractor
from src.domain.exceptions import AssetNotFoundException
from src.domain.exceptions import InsufficientFundsException
from src.domain.exceptions import WalletNotFoundException
from src.presentation.http.dependencies.auth import CurrentUserId
from src.presentation.http.responses import create_error_responses

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    responses=create_error_responses(
        WalletNotFoundException,
        AssetNotFoundException,
        InsufficientFundsException,
    ),
    summary="Send Transaction",
    description="Create and send a new pending transaction to the blockchain.",
)
@inject
async def send_transaction(
    request: CreatePendingTransactionRequest,
    user_id: CurrentUserId,
    interactor: FromDishka[CreatePendingTransactionInteractor],
) -> TransactionResponse:
    """Create and send a transaction."""
    request.user_id = user_id
    return await interactor(request)


@router.get(
    "/wallet/{wallet_id}",
    response_model=list[dict[str, Any]],
    responses=create_error_responses(
        WalletNotFoundException,
    ),
    summary="Get Wallet Transactions",
    description="Retrieve historical transactions for a wallet via Etherscan.",
)
@inject
async def get_wallet_transactions(
    wallet_id: uuid.UUID,
    user_id: CurrentUserId,
    interactor: FromDishka[GetTransactionsInteractor],
) -> list[dict[str, Any]]:
    """Get transaction history via Etherscan."""
    return await interactor(wallet_id)
