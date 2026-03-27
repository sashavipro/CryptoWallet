"""ethereum/src/application/ports/providers/web3.py."""

from decimal import Decimal
from typing import Any
from typing import Protocol

from src.domain.entities import Wallet
from src.domain.value_objects.shared import EthereumAddress


class Web3Provider(Protocol):
    """Port for direct interaction with an EVM-compatible blockchain node."""

    def create_account(self) -> dict[str, str]:
        """Generate a new wallet account (address and private key)."""
        ...

    async def get_balance(self, address: EthereumAddress) -> Decimal:
        """Get the native currency balance of a given address."""
        ...

    async def send_transaction(
        self, from_wallet: Wallet, to_address: EthereumAddress, value: Decimal
    ) -> str:
        """Send native currency and return the transaction hash."""
        ...

    async def get_transaction_receipt(self, tx_hash: str) -> dict[str, Any] | None:
        """Check the status of a transaction on the blockchain."""
        ...

    def get_address_from_private_key(self, private_key: str) -> str:
        """Derive the public Ethereum address from a raw private key."""
        ...
