"""ethereum/src/application/interactors/wallet.py."""

import logging
import uuid

from src.application.dtos.request import CreateWalletRequest
from src.application.dtos.request import ImportWalletRequest
from src.application.dtos.response import WalletBalanceResponse
from src.application.dtos.response import WalletResponse
from src.application.ports.gateways import AssetGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import WalletGateway
from src.application.ports.providers import BalanceCache
from src.application.ports.providers import Web3Provider
from src.application.ports.utils import Encryptor
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.wallet import Wallet
from src.domain.exceptions import AssetNotFoundException
from src.domain.exceptions import WalletNotFoundException
from src.domain.value_objects.shared import EthereumAddress
from src.domain.value_objects.wallet import EncryptedPrivateKey
from src.domain.value_objects.wallet import RawPrivateKey

logger = logging.getLogger(__name__)


class CreateWalletInteractor:
    """Use case for creating a brand new crypto wallet."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        asset_gateway: AssetGateway,
        uow: UnitOfWork,
        web3_provider: Web3Provider,
        encryptor: Encryptor,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
    ) -> None:
        """Initialize with required ports."""
        self.wallet_gateway = wallet_gateway
        self.asset_gateway = asset_gateway
        self.uow = uow
        self.web3_provider = web3_provider
        self.encryptor = encryptor
        self.id_generator = id_generator
        self.time_provider = time_provider

    async def __call__(self, request: CreateWalletRequest) -> WalletResponse:
        """Execute the wallet creation workflow."""
        logger.info(
            "Attempting to create wallet for user: %s, asset: %s",
            request.user_id,
            request.asset_id,
        )

        asset = await self.asset_gateway.get_asset_by_id(request.asset_id)
        if not asset:
            raise AssetNotFoundException

        account_data = self.web3_provider.create_account()

        eth_address = EthereumAddress(account_data["address"])
        raw_key = RawPrivateKey(account_data["private_key"])

        encrypted_str = self.encryptor.encrypt(raw_key.value)
        encrypted_key = EncryptedPrivateKey(encrypted_str)

        wallet = Wallet(
            id=self.id_generator.generate(),
            user_id=request.user_id,
            asset_id=request.asset_id,
            address=eth_address.value,
            private_key_encrypted=encrypted_key.value,
            created_at=self.time_provider.now(),
        )

        async with self.uow:
            saved_wallet = await self.wallet_gateway.add_wallet(wallet)

        logger.info("Successfully created wallet: %s", saved_wallet.id)

        return WalletResponse(
            id=saved_wallet.id,
            user_id=saved_wallet.user_id,
            asset_id=saved_wallet.asset_id,
            address=saved_wallet.address,
            balance=saved_wallet.balance,
            balance_updated_at=saved_wallet.balance_updated_at,
            created_at=saved_wallet.created_at,
        )


class ImportWalletInteractor:
    """Use case for importing an existing crypto wallet via private key."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        asset_gateway: AssetGateway,
        uow: UnitOfWork,
        web3_provider: Web3Provider,
        encryptor: Encryptor,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
    ) -> None:
        """Initialize with required ports."""
        self.wallet_gateway = wallet_gateway
        self.asset_gateway = asset_gateway
        self.uow = uow
        self.web3_provider = web3_provider
        self.encryptor = encryptor
        self.id_generator = id_generator
        self.time_provider = time_provider

    async def __call__(self, request: ImportWalletRequest) -> WalletResponse:
        """Execute the wallet import workflow."""
        logger.info(
            "Attempting to import wallet for user: %s, asset: %s",
            request.user_id,
            request.asset_id,
        )

        asset = await self.asset_gateway.get_asset_by_id(request.asset_id)
        if not asset:
            raise AssetNotFoundException

        raw_key = RawPrivateKey(request.private_key)

        derived_address_str = self.web3_provider.get_address_from_private_key(
            raw_key.value
        )
        eth_address = EthereumAddress(derived_address_str)

        encrypted_str = self.encryptor.encrypt(raw_key.value)
        encrypted_key = EncryptedPrivateKey(encrypted_str)

        wallet = Wallet(
            id=self.id_generator.generate(),
            user_id=request.user_id,
            asset_id=request.asset_id,
            address=eth_address.value,
            private_key_encrypted=encrypted_key.value,
            created_at=self.time_provider.now(),
        )

        async with self.uow:
            saved_wallet = await self.wallet_gateway.add_wallet(wallet)

        logger.info("Successfully imported wallet: %s", saved_wallet.id)

        return WalletResponse(
            id=saved_wallet.id,
            user_id=saved_wallet.user_id,
            asset_id=saved_wallet.asset_id,
            address=saved_wallet.address,
            balance=saved_wallet.balance,
            balance_updated_at=saved_wallet.balance_updated_at,
            created_at=saved_wallet.created_at,
        )


class GetWalletsInteractor:
    """Use case for retrieving all wallets for a specific user."""

    def __init__(self, wallet_gateway: WalletGateway) -> None:
        """Initialize with required ports."""
        self.wallet_gateway = wallet_gateway

    async def __call__(self, user_id: uuid.UUID) -> list[WalletResponse]:
        """Execute the workflow to get user's wallets."""
        logger.info("Retrieving wallets for user: %s", user_id)

        db_wallets = await self.wallet_gateway.get_wallets_by_user_id(user_id)
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
            for w in db_wallets
        ]


class GetBalanceInteractor:
    """Use case for retrieving wallet balance with Redis cache and Web3 fallback."""

    def __init__(
        self,
        wallet_gateway: WalletGateway,
        web3_provider: Web3Provider,
        balance_cache: BalanceCache,
        time_provider: TimeProvider,
        uow: UnitOfWork,
    ) -> None:
        """Initialize with required ports."""
        self.wallet_gateway = wallet_gateway
        self.web3_provider = web3_provider
        self.balance_cache = balance_cache
        self.time_provider = time_provider
        self.uow = uow

    async def __call__(self, wallet_id: uuid.UUID) -> WalletBalanceResponse:
        """Execute the balance retrieval workflow.

        Checks cache first, then Web3, then updates cache and DB.
        """
        logger.info("Retrieving balance for wallet: %s", wallet_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundException

        cached_data = await self.balance_cache.get_balance(wallet.id)

        if cached_data:
            logger.debug("Cache hit for balance of wallet: %s", wallet.id)
            return WalletBalanceResponse(
                wallet_id=wallet.id,
                address=wallet.address,
                balance=cached_data.balance,
                balance_updated_at=cached_data.updated_at,
            )
        logger.debug("Cache miss or expired for balance of wallet: %s", wallet.id)

        logger.info("Fetching fresh balance from Web3 for wallet: %s", wallet.id)
        balance_from_web3 = await self.web3_provider.get_balance(
            EthereumAddress(wallet.address)
        )
        updated_at_time = self.time_provider.now()

        wallet.update_balance(balance_from_web3, updated_at_time)
        async with self.uow:
            updated_db_wallet = await self.wallet_gateway.update_wallet(wallet)

        await self.balance_cache.set_balance(
            wallet.id, updated_db_wallet.balance, updated_at_time
        )

        return WalletBalanceResponse(
            wallet_id=updated_db_wallet.id,
            address=updated_db_wallet.address,
            balance=updated_db_wallet.balance,
            balance_updated_at=updated_db_wallet.balance_updated_at,
        )


class DeleteWalletInteractor:
    """Use case for deleting a wallet."""

    def __init__(self, wallet_gateway: WalletGateway, uow: UnitOfWork) -> None:
        """Initialize the interactor with required gateways."""
        self.wallet_gateway = wallet_gateway
        self.uow = uow

    async def __call__(self, wallet_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Execute the use case to delete a wallet."""
        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet or wallet.user_id != user_id:
            raise WalletNotFoundException

        async with self.uow:
            await self.wallet_gateway.delete_wallet(wallet)
