"""ethereum/src/application/interactors/wallet.py."""

import logging

from src.application.dtos.request import CreateWalletRequest
from src.application.dtos.request import ImportWalletRequest
from src.application.dtos.response import WalletResponse
from src.application.ports.gateways.asset import AssetGateway
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.gateways.wallet import WalletGateway
from src.application.ports.providers.web3 import Web3Provider
from src.application.ports.utils import Encryptor
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.wallet import Wallet
from src.domain.exceptions import AssetNotFoundException
from src.domain.exceptions import WalletAlreadyExistsException
from src.domain.value_objects.shared.address import EthereumAddress
from src.domain.value_objects.wallet.private_key import EncryptedPrivateKey
from src.domain.value_objects.wallet.private_key import RawPrivateKey

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

        existing_wallet = await self.wallet_gateway.get_wallet_by_user_and_asset(
            user_id=request.user_id, asset_id=request.asset_id
        )
        if existing_wallet:
            logger.warning("Wallet already exists for user %s", request.user_id)
            raise WalletAlreadyExistsException

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

        existing_wallet = await self.wallet_gateway.get_wallet_by_user_and_asset(
            user_id=request.user_id, asset_id=request.asset_id
        )
        if existing_wallet:
            logger.warning("Wallet already exists for user %s", request.user_id)
            raise WalletAlreadyExistsException

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
