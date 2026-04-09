"""rest_api/src/application/interactors/wallet.py."""

import logging
import uuid
from decimal import Decimal

from src.application.dtos.request.wallet import CreateWalletRequest
from src.application.dtos.request.wallet import ImportWalletRequest
from src.application.dtos.response.wallet import WalletBalanceResponse
from src.application.dtos.response.wallet import WalletResponse
from src.application.ports.events import EventPublisher
from src.application.ports.gateways import StatsGateway
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

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        uow: UnitOfWork,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
        worker_client: EthereumWorkerClient,
        event_publisher: EventPublisher,
        stats_gateway: StatsGateway,
    ) -> None:
        """Initialize the interactor with required gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.uow = uow
        self.id_generator = id_generator
        self.time_provider = time_provider
        self.worker_client = worker_client
        self.event_publisher = event_publisher
        self.stats_gateway = stats_gateway

    async def __call__(
        self, user_id: uuid.UUID, request: CreateWalletRequest
    ) -> WalletResponse:
        """Generate a new wallet through the worker and save it to the database."""
        logger.info(
            "Requesting new wallet generation from worker for user: %s", user_id
        )

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

        m_count = await self.stats_gateway.get_total_messages(user_id)
        w_count = await self.stats_gateway.get_wallets_count(user_id)
        await self.event_publisher.publish_stats_updated(user_id, m_count, w_count)

        return WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            asset_id=wallet.asset_id,
            address=wallet.address,
            balance=wallet.balance,
            balance_updated_at=wallet.balance_updated_at,
            created_at=wallet.created_at,
        )


class ImportWalletInteractor:
    """Use case for importing an existing wallet using a private key."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        uow: UnitOfWork,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
        worker_client: EthereumWorkerClient,
        event_publisher: EventPublisher,
        stats_gateway: StatsGateway,
    ) -> None:
        """Initialize the interactor with required gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.uow = uow
        self.id_generator = id_generator
        self.time_provider = time_provider
        self.worker_client = worker_client
        self.event_publisher = event_publisher
        self.stats_gateway = stats_gateway

    async def __call__(
        self, user_id: uuid.UUID, request: ImportWalletRequest
    ) -> WalletResponse:
        """Import an existing wallet and save it to the database."""
        logger.info("Importing wallet for user: %s", user_id)

        worker_data = await self.worker_client.import_wallet(
            private_key=request.private_key
        )
        address = worker_data["address"]

        existing_wallet = (
            await self.wallet_gateway.get_wallet_by_user_asset_and_address(
                user_id, request.asset_id, address
            )
        )
        if existing_wallet:
            logger.warning(
                "User %s tried to import duplicate wallet %s", user_id, address
            )
            raise WalletAlreadyExistsException

        now = self.time_provider.now()

        wallet = Wallet(
            id=self.id_generator.generate(),
            user_id=user_id,
            asset_id=request.asset_id,
            address=address,
            private_key_encrypted=worker_data["private_key_encrypted"],
            balance=Decimal("0.0"),
            created_at=now,
        )

        async with self.uow:
            await self.wallet_gateway.add_wallet(wallet)

        m_count = await self.stats_gateway.get_total_messages(user_id)
        w_count = await self.stats_gateway.get_wallets_count(user_id)
        await self.event_publisher.publish_stats_updated(user_id, m_count, w_count)

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
    """Use case for retrieving wallet balance from the local database and Web3."""

    def __init__(
        self,
        wallet_gateway: WalletGateway,
        uow: UnitOfWork,
        time_provider: TimeProvider,
        worker_client: EthereumWorkerClient,
    ) -> None:
        """Initialize the interactor with gateways and worker client."""
        self.wallet_gateway = wallet_gateway
        self.uow = uow
        self.time_provider = time_provider
        self.worker_client = worker_client

    async def __call__(
        self, wallet_id: uuid.UUID, user_id: uuid.UUID
    ) -> WalletBalanceResponse:
        """Retrieve the live balance from Web3 via worker and update the database."""
        logger.info(
            "Retrieving live balance for wallet: %s (User: %s)", wallet_id, user_id
        )

        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)

        if not wallet or wallet.user_id != user_id:
            raise WalletNotFoundException

        live_balance_str = await self.worker_client.get_balance(wallet.address)

        live_balance = Decimal(str(live_balance_str))

        now = self.time_provider.now()

        wallet.update_balance(live_balance, now)

        async with self.uow:
            await self.wallet_gateway.update_wallet(wallet)

        return WalletBalanceResponse(
            wallet_id=wallet.id,
            address=wallet.address,
            balance=wallet.balance,
            balance_updated_at=wallet.balance_updated_at,
        )


class DeleteWalletInteractor:
    """Use case for deleting a wallet."""

    def __init__(
        self,
        wallet_gateway: WalletGateway,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        stats_gateway: StatsGateway,
    ) -> None:
        """Initialize the interactor with a wallet gateway and Unit of Work."""
        self.wallet_gateway = wallet_gateway
        self.uow = uow
        self.event_publisher = event_publisher
        self.stats_gateway = stats_gateway

    async def __call__(self, wallet_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a specific wallet from the database."""
        logger.info("Deleting wallet: %s for user: %s", wallet_id, user_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)

        if not wallet or wallet.user_id != user_id:
            raise WalletNotFoundException

        async with self.uow:
            await self.wallet_gateway.delete_wallet(wallet_id)

        m_count = await self.stats_gateway.get_total_messages(user_id)
        w_count = await self.stats_gateway.get_wallets_count(user_id)
        await self.event_publisher.publish_stats_updated(user_id, m_count, w_count)
