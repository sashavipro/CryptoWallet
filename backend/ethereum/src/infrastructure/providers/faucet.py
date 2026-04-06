"""ethereum/src/infrastructure/providers/faucet.py."""

import logging
from decimal import Decimal

from src.application.ports.providers.faucet import FaucetProvider
from src.application.ports.providers.nonce_manager import NonceManager
from src.application.ports.providers.web3 import Web3Provider
from src.application.ports.utils import Encryptor
from src.domain.value_objects.shared.address import EthereumAddress
from src.infrastructure.settings import Web3Settings

logger = logging.getLogger(__name__)


class FaucetProviderImpl(FaucetProvider):
    """Implementation of FaucetProvider for Sepolia testnet."""

    def __init__(
        self,
        settings: Web3Settings,
        web3_provider: Web3Provider,
        encryptor: Encryptor,
        nonce_manager: NonceManager,
    ) -> None:
        """Initialize with Web3 settings, Web3Provider, Encryptor, and NonceManager."""
        self.settings = settings
        self.web3_provider = web3_provider
        self.encryptor = encryptor
        self.nonce_manager = nonce_manager

        self._master_private_key = self.encryptor.decrypt(
            self.settings.FAUCET_PRIVATE_KEY_ENCRYPTED
        )

        self._master_address = EthereumAddress(self.settings.FAUCET_MASTER_ADDRESS)
        self._faucet_amount_eth = Decimal(str(self.settings.FAUCET_AMOUNT_ETH))

        logger.info(
            "FaucetProvider initialized with master address: %s, amount: %s ETH",
            self._master_address.value,
            self._faucet_amount_eth,
        )

    async def request_testnet_eth(self, to_address: EthereumAddress) -> str:
        """Send test ETH from the master wallet to a user's address."""
        logger.info(
            "Sending %s ETH from faucet to %s",
            self._faucet_amount_eth,
            to_address.value,
        )

        nonce = await self.nonce_manager.get_and_increment_nonce(
            self._master_address.value
        )

        tx_hash = await self.web3_provider.send_transaction(
            raw_private_key=self._master_private_key,
            from_address=self._master_address,
            to_address=to_address,
            value=self._faucet_amount_eth,
            nonce=nonce,
        )

        logger.info("Faucet transaction sent. Hash: %s", tx_hash)
        return tx_hash
