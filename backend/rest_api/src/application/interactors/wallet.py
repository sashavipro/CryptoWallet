"""rest_api/src/application/interactors/wallet.py."""

import logging
import uuid
from typing import Any

from src.application.dtos.request.wallet import CreateWalletRequest
from src.application.dtos.response.wallet import WalletResponse
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.gateways.wallet import WalletGateway
from src.application.ports.providers.worker_client import EthereumWorkerClient
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.wallet import Wallet
from src.domain.exceptions import WalletNotFoundException
from src.domain.value_objects.shared.address import EthereumAddress
from src.domain.value_objects.shared.balance import Balance
from src.domain.value_objects.wallet.private_key import EncryptedPrivateKey

logger = logging.getLogger(__name__)


class CreateWalletInteractor:
    """Use case for generating a new EVM wallet via RPC to stateless worker."""

    def __init__(
        self,
        wallet_gateway: WalletGateway,
        uow: UnitOfWork,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
        worker_client: EthereumWorkerClient,
    ) -> None:
        """Initialize the interactor with required gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.uow = uow
        self.id_generator = id_generator
        self.time_provider = time_provider
        self.worker_client = worker_client

    async def __call__(
        self, user_id: uuid.UUID, request: CreateWalletRequest
    ) -> WalletResponse:
        """Generate a new wallet through the worker and save it to the database."""
        logger.info(
            "Requesting new wallet generation from worker for user: %s", user_id
        )

        worker_data = await self.worker_client.create_wallet()

        now = self.time_provider.get_current_time()

        wallet = Wallet(
            id=self.id_generator.generate(),
            user_id=user_id,
            address=EthereumAddress(worker_data["address"]),
            encrypted_private_key=EncryptedPrivateKey(
                worker_data["private_key_encrypted"]
            ),
            balance=Balance(0),
            created_at=now,
            updated_at=now,
        )

        async with self.uow:
            await self.wallet_gateway.add_wallet(wallet)

        return WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            asset_id=request.asset_id,
            address=wallet.address.value,
            balance=wallet.balance.value,
            balance_updated_at=wallet.updated_at,
            created_at=wallet.created_at,
        )


class GetWalletsInteractor:
    """Use case for retrieving all wallets of a specific user."""

    def __init__(self, wallet_gateway: WalletGateway) -> None:
        """Initialize the interactor with a wallet gateway."""
        self.wallet_gateway = wallet_gateway

    async def __call__(self, user_id: uuid.UUID) -> list[WalletResponse]:
        """Retrieve all wallets for the specified user ID."""
        logger.info("Retrieving wallets for user: %s", user_id)
        wallets = await self.wallet_gateway.get_wallets_by_user_id(user_id)
        return [
            WalletResponse(
                id=w.id,
                user_id=w.user_id,
                address=w.address.value,
                balance=w.balance.value,
                created_at=w.created_at,
                updated_at=w.updated_at,
            )
            for w in wallets
        ]


class GetBalanceInteractor:
    """Use case for retrieving wallet balance from the local database."""

    def __init__(self, wallet_gateway: WalletGateway) -> None:
        """Initialize the interactor with a wallet gateway."""
        self.wallet_gateway = wallet_gateway

    async def __call__(self, wallet_id: uuid.UUID) -> dict[str, Any]:
        """Retrieve the balance of a specific wallet from the database."""
        logger.info("Retrieving balance from DB for wallet: %s", wallet_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundException

        return {"balance": str(wallet.balance.value)}
