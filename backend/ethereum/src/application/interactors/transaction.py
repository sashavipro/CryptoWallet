"""ethereum/src/application/interactors/transaction.py."""

import logging
from decimal import Decimal

from src.application.ports.providers.nonce_manager import NonceManager
from src.application.ports.providers.web3 import Web3Provider
from src.application.ports.utils import Encryptor
from src.domain.value_objects.shared.address import EthereumAddress

logger = logging.getLogger(__name__)


class SendTransactionInteractor:
    """Decrypts the key and sends the transaction to Web3."""

    def __init__(
        self,
        web3_provider: Web3Provider,
        encryptor: Encryptor,
        nonce_manager: NonceManager,
    ) -> None:
        """Initialize the interactor with required providers and utilities."""
        self.web3_provider = web3_provider
        self.encryptor = encryptor
        self.nonce_manager = nonce_manager

    async def __call__(
        self,
        private_key_encrypted: str,
        from_address: str,
        to_address: str,
        value_eth: str,
    ) -> str:
        """Decrypt the private key and broadcast the transaction to the network."""
        raw_pk = self.encryptor.decrypt(private_key_encrypted)
        nonce = await self.nonce_manager.get_and_increment_nonce(from_address)

        tx_hash = await self.web3_provider.send_transaction(
            raw_private_key=raw_pk,
            from_address=EthereumAddress(from_address),
            to_address=EthereumAddress(to_address),
            value=Decimal(value_eth),
            nonce=nonce,
        )
        logger.info("Transaction sent: %s", tx_hash)
        return tx_hash
