"""rest_api/src/application/ports/providers/worker_client.py."""

from typing import Protocol


class EthereumWorkerClient(Protocol):
    """Port for RPC communication with the Ethereum stateless worker."""

    async def create_wallet(self) -> dict[str, str]:
        """Request worker to generate a wallet.

        Returns dict with address and private_key_encrypted.
        """
        ...

    async def send_transaction(
        self,
        private_key_encrypted: str,
        from_address: str,
        to_address: str,
        value_eth: str,
    ) -> str:
        """Request worker to send a transaction. Returns tx_hash."""
        ...

    async def request_faucet(self, address: str) -> str:
        """Request testnet ETH from worker's faucet. Returns tx_hash."""
        ...

    async def get_balance(self, address: str) -> str:
        """Request live balance from Web3."""
        ...
