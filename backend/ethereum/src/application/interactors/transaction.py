"""ethereum/src/application/interactors/transaction.py."""

import logging
from decimal import Decimal

from src.application.ports.providers.nonce_manager import NonceManager
from src.application.ports.providers.web3 import Web3Provider
from src.application.ports.publishers import EventPublisher
from src.application.ports.utils import Encryptor
from src.domain.value_objects.shared.address import EthereumAddress

logger = logging.getLogger(__name__)


class SendTransactionInteractor:
    """Interactor responsible for initiating and sending Ethereum transactions."""

    def __init__(
        self,
        web3_provider: Web3Provider,
        encryptor: Encryptor,
        nonce_manager: NonceManager,
        event_publisher: EventPublisher,
    ) -> None:
        """Initialize the SendTransactionInteractor."""
        self.web3_provider = web3_provider
        self.encryptor = encryptor
        self.nonce_manager = nonce_manager
        self.event_publisher = event_publisher

    async def __call__(
        self,
        tx_id: str,
        private_key_encrypted: str,
        from_address: str,
        to_address: str,
        value_eth: str,
    ) -> None:
        """Execute the transaction sending process.

        Decrypts the private key, retrieves the next nonce, signs and sends the
        transaction to the network, and publishes an event based on the result.
        """
        try:
            raw_pk = self.encryptor.decrypt(private_key_encrypted)
            nonce = await self.nonce_manager.get_and_increment_nonce(from_address)

            tx_hash = await self.web3_provider.send_transaction(
                raw_private_key=raw_pk,
                from_address=EthereumAddress(from_address),
                to_address=EthereumAddress(to_address),
                value=Decimal(value_eth),
                nonce=nonce,
            )

            if isinstance(tx_hash, bytes):
                tx_hash_str = tx_hash.hex()
                tx_hash = (
                    tx_hash_str if tx_hash_str.startswith("0x") else f"0x{tx_hash_str}"
                )
            else:
                tx_hash = str(tx_hash)

            logger.info("Transaction sent: %s", tx_hash)

            await self.event_publisher.publish_tx_initiated(tx_id, tx_hash)

        except Exception as e:
            logger.exception("Failed to send tx %s", tx_id)
            await self.event_publisher.publish_tx_failed_initiation(tx_id, str(e))
