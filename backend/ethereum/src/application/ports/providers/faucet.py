"""ethereum/src/application/ports/providers/faucet.py."""

from typing import Protocol

from src.domain.value_objects.shared.address import EthereumAddress


class FaucetProvider(Protocol):
    """Port for the testnet ETH faucet functionality."""

    async def request_testnet_eth(self, to_address: EthereumAddress) -> str:
        """Send a small amount of test ETH from the master wallet.

        Returns the transaction hash.
        """
        ...
