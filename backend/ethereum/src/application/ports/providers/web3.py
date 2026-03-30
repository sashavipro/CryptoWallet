"""ethereum/src/application/ports/providers/web3.py."""

from decimal import Decimal
from typing import Any
from typing import Protocol

from src.domain.value_objects.shared.address import EthereumAddress


class Web3Provider(Protocol):
    """Port for direct interaction with an EVM-compatible blockchain node."""

    def create_account(self) -> dict[str, str]:
        """Generate a new wallet account (address and private key)."""
        ...

    def get_address_from_private_key(self, private_key: str) -> str:
        """Derive the public Ethereum address from a raw private key."""
        ...

    async def get_balance(self, address: EthereumAddress) -> Decimal:
        """Get the native currency balance of a given address."""
        ...

    async def get_transaction_count(self, address: EthereumAddress) -> int:
        """Get the number of transactions sent from an address (nonce)."""
        ...

    async def send_transaction(  # noqa: PLR0913
        self,
        raw_private_key: str,
        from_address: EthereumAddress,
        to_address: EthereumAddress,
        value: Decimal,
        nonce: int,
        gas_limit: int = 21000,
    ) -> str:
        """Send native currency and return the transaction hash."""
        ...

    async def get_transaction_receipt(self, tx_hash: str) -> dict[str, Any] | None:
        """Check the status of a transaction on the blockchain."""
        ...

    async def get_gas_price(self) -> Decimal:
        """Get the current gas price from the network."""
        ...
