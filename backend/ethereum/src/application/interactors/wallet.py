"""ethereum/src/application/interactors/wallet.py."""

import logging

from src.application.ports.providers.web3 import Web3Provider
from src.application.ports.utils import Encryptor

logger = logging.getLogger(__name__)


class CreateWalletInteractor:
    """Generates a new wallet and returns the encrypted data."""

    def __init__(self, web3_provider: Web3Provider, encryptor: Encryptor) -> None:
        """Initialize the interactor with Web3 and encryption providers."""
        self.web3_provider = web3_provider
        self.encryptor = encryptor

    async def __call__(self) -> dict[str, str]:
        """Generate a new wallet and return the encrypted credentials."""
        account_data = self.web3_provider.create_account()
        encrypted_pk = self.encryptor.encrypt(account_data["private_key"])

        logger.info("Generated new wallet address: %s", account_data["address"])
        return {
            "address": account_data["address"],
            "private_key_encrypted": encrypted_pk,
        }


class GetBalanceInteractor:
    """Get the balance for a specific Ethereum address."""

    def __init__(self, web3_provider: Web3Provider) -> None:
        """Initialize the interactor with a Web3 provider."""
        self.web3_provider = web3_provider

    async def __call__(self, address: str) -> str:
        """Retrieve the balance of the specified address from the blockchain."""
        from src.domain.value_objects.shared.address import EthereumAddress

        balance = await self.web3_provider.get_balance(EthereumAddress(address))
        return str(balance)
