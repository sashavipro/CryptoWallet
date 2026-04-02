"""ethereum/src/presentation/http/routers/wallet.py."""

import uuid

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import Body
from fastapi import status

from src.application.dtos.request import CreateWalletRequest
from src.application.dtos.request import ImportWalletRequest
from src.application.dtos.response import WalletBalanceResponse
from src.application.dtos.response import WalletResponse
from src.application.interactors.wallet import CreateWalletInteractor
from src.application.interactors.wallet import DeleteWalletInteractor
from src.application.interactors.wallet import GetBalanceInteractor
from src.application.interactors.wallet import GetWalletsInteractor
from src.application.interactors.wallet import ImportWalletInteractor
from src.domain.exceptions import AssetNotFoundException
from src.domain.exceptions import InvalidPrivateKeyFormatException
from src.domain.exceptions import WalletAlreadyExistsException
from src.domain.exceptions import WalletNotFoundException
from src.presentation.http.dependencies.auth import CurrentUserId
from src.presentation.http.responses import create_error_responses

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.post(
    "",
    response_model=WalletResponse,
    status_code=status.HTTP_201_CREATED,
    responses=create_error_responses(
        AssetNotFoundException,
        WalletAlreadyExistsException,
    ),
    summary="Create New Wallet",
    description="Create a new crypto wallet for a user.",
)
@inject
async def create_wallet(
    user_id: CurrentUserId,
    interactor: FromDishka[CreateWalletInteractor],
    request: CreateWalletRequest = Body(...),  # noqa: B008
) -> WalletResponse:
    """Create a new wallet."""
    request.user_id = user_id
    return await interactor(request)


@router.post(
    "/import",
    response_model=WalletResponse,
    responses=create_error_responses(
        AssetNotFoundException,
        WalletAlreadyExistsException,
        InvalidPrivateKeyFormatException,
    ),
    summary="Import Existing Wallet",
    description="Import an existing crypto wallet for a user using its private key.",
)
@inject
async def import_existing_wallet(
    user_id: CurrentUserId,
    interactor: FromDishka[ImportWalletInteractor],
    request: ImportWalletRequest = Body(...),  # noqa: B008
) -> WalletResponse:
    """Import an existing wallet."""
    request.user_id = user_id
    return await interactor(request)


@router.get(
    "",
    response_model=list[WalletResponse],
    responses=create_error_responses(
        WalletNotFoundException,
    ),
    summary="Get User Wallets",
    description="Retrieve all crypto wallets for the current user.",
)
@inject
async def get_user_wallets(
    user_id: CurrentUserId,
    interactor: FromDishka[GetWalletsInteractor],
) -> list[WalletResponse]:
    """Get all wallets for the current user."""
    return await interactor(user_id)


@router.get(
    "/{wallet_id}/balance",
    response_model=WalletBalanceResponse,
    responses=create_error_responses(
        WalletNotFoundException,
    ),
    summary="Get Wallet Balance",
    description="Retrieve the current balance for a specific wallet.",
)
@inject
async def get_wallet_balance(
    wallet_id: uuid.UUID,
    user_id: CurrentUserId,
    interactor: FromDishka[GetBalanceInteractor],
) -> WalletBalanceResponse:
    """Get the balance of a specific wallet."""
    return await interactor(wallet_id)


@router.delete(
    "/{wallet_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=create_error_responses(WalletNotFoundException),
    summary="Delete Wallet",
    description="Delete a specific crypto wallet for the current user.",
)
@inject
async def delete_wallet(
    wallet_id: uuid.UUID,
    user_id: CurrentUserId,
    interactor: FromDishka[DeleteWalletInteractor],
) -> None:
    """Delete a user's wallet."""
    await interactor(wallet_id=wallet_id, user_id=user_id)
