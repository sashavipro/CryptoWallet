"""rest_api/src/application/ports/providers/worker_client.py."""

from typing import Protocol


class EthereumWorkerClient(Protocol):
    """Port for RPC communication with the Ethereum stateless worker."""

    async def create_wallet(self) -> dict[str, str]:
        """Request worker to generate a wallet."""
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

    async def import_wallet(self, private_key: str) -> dict[str, str]:
        """Request worker to recover address from a private key and encrypt it."""
        ...

    async def publish_send_transaction_event(
        self,
        tx_id: str,
        private_key_encrypted: str,
        from_address: str,
        to_address: str,
        value_eth: str,
    ) -> None:
        """Publish a transaction request asynchronously without waiting."""
        ...
