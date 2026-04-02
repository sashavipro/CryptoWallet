"""ethereum/src/application/interactors/faucet.py."""

import logging

from src.application.ports.providers import FaucetProvider
from src.domain.value_objects.shared import EthereumAddress

logger = logging.getLogger(__name__)


class RequestTestnetEthInteractor:
    """Stateless worker use case for requesting testnet ETH."""

    def __init__(self, faucet_provider: FaucetProvider) -> None:
        """Initialize the interactor with a faucet provider."""
        self.faucet_provider = faucet_provider

    async def __call__(self, to_address: str) -> str:
        """Request the broadcast and return the tx_hash. No database."""
        logger.info("Requesting testnet ETH for address: %s", to_address)

        return await self.faucet_provider.request_testnet_eth(
            to_address=EthereumAddress(to_address)
        )
