"""rest_api/src/application/interactors/wallet.py."""

import logging
import uuid
from decimal import Decimal

from src.application.dtos.request.wallet import CreateWalletRequest
from src.application.dtos.request.wallet import ImportWalletRequest
from src.application.dtos.response.wallet import WalletBalanceResponse
from src.application.dtos.response.wallet import WalletResponse
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.gateways.wallet import WalletGateway
from src.application.ports.providers.worker_client import EthereumWorkerClient
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.wallet import Wallet
from src.domain.exceptions import WalletAlreadyExistsException
from src.domain.exceptions import WalletNotFoundException
from src.domain.value_objects.shared.address import EthereumAddress
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

        existing_wallet = await self.wallet_gateway.get_wallet_by_user_and_asset(
            user_id, request.asset_id
        )
        if existing_wallet:
            raise WalletAlreadyExistsException

        worker_data = await self.worker_client.create_wallet()
        now = self.time_provider.now()

        valid_address = EthereumAddress(worker_data["address"])
        valid_pk = EncryptedPrivateKey(worker_data["private_key_encrypted"])

        wallet = Wallet(
            id=self.id_generator.generate(),
            user_id=user_id,
            asset_id=request.asset_id,
            address=valid_address.value,
            private_key_encrypted=valid_pk.value,
            balance=Decimal("0.0"),
            created_at=now,
        )

        async with self.uow:
            await self.wallet_gateway.add_wallet(wallet)

        return WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            asset_id=wallet.asset_id,
            address=wallet.address,
            balance=wallet.balance,
            balance_updated_at=wallet.balance_updated_at,
            created_at=wallet.created_at,
        )


class GetWalletsInteractor:
    """Use case for retrieving all wallets of a specific user."""

    def __init__(self, wallet_gateway: WalletGateway) -> None:
        """Initialize the interactor with a wallet gateway."""
        self.wallet_gateway = wallet_gateway

    async def __call__(self, user_id: uuid.UUID) -> list[WalletResponse]:
        """Retrieve all wallets for the specified user."""
        logger.info("Retrieving wallets for user: %s", user_id)
        wallets = await self.wallet_gateway.get_wallets_by_user_id(user_id)

        return [
            WalletResponse(
                id=w.id,
                user_id=w.user_id,
                asset_id=w.asset_id,
                address=w.address,
                balance=w.balance,
                balance_updated_at=w.balance_updated_at,
                created_at=w.created_at,
            )
            for w in wallets
        ]


class GetBalanceInteractor:
    """Use case for retrieving wallet balance from the local database."""

    def __init__(self, wallet_gateway: WalletGateway) -> None:
        """Initialize the interactor with a wallet gateway."""
        self.wallet_gateway = wallet_gateway

    async def __call__(self, wallet_id: uuid.UUID) -> WalletBalanceResponse:
        """Retrieve the balance of a specific wallet from the database."""
        logger.info("Retrieving balance from DB for wallet: %s", wallet_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundException

        return WalletBalanceResponse(
            balance=wallet.balance, updated_at=wallet.balance_updated_at
        )


class DeleteWalletInteractor:
    """Use case for deleting a wallet."""

    def __init__(self, wallet_gateway: WalletGateway, uow: UnitOfWork) -> None:
        """Initialize the interactor with a wallet gateway and Unit of Work."""
        self.wallet_gateway = wallet_gateway
        self.uow = uow

    async def __call__(self, wallet_id: uuid.UUID) -> None:
        """Delete a specific wallet from the database."""
        logger.info("Deleting wallet: %s", wallet_id)
        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundException

        async with self.uow:
            await self.wallet_gateway.delete_wallet(wallet_id)


class ImportWalletInteractor:
    """Use case for importing an existing wallet using a private key."""

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
        self, user_id: uuid.UUID, request: ImportWalletRequest
    ) -> WalletResponse:
        """Import an existing wallet and save it to the database."""
        logger.info("Importing wallet for user: %s", user_id)

        existing_wallet = await self.wallet_gateway.get_wallet_by_user_and_asset(
            user_id, request.asset_id
        )
        if existing_wallet:
            raise WalletAlreadyExistsException

        worker_data = await self.worker_client.import_wallet(
            private_key=request.private_key
        )

        now = self.time_provider.now()

        wallet = Wallet(
            id=self.id_generator.generate(),
            user_id=user_id,
            asset_id=request.asset_id,
            address=worker_data["address"],
            private_key_encrypted=worker_data["private_key_encrypted"],
            balance=Decimal("0.0"),
            created_at=now,
        )

        async with self.uow:
            await self.wallet_gateway.add_wallet(wallet)

        return WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            asset_id=wallet.asset_id,
            address=wallet.address,
            balance=wallet.balance,
            balance_updated_at=wallet.balance_updated_at,
            created_at=wallet.created_at,
        )
