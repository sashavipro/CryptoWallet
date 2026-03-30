"""ethereum/src/application/ports/gateways/wallet.py."""

import uuid
from typing import Protocol

from src.domain.entities.wallet import Wallet


class WalletGateway(Protocol):
    """Port for Wallet database operations."""

    async def add_wallet(self, wallet: Wallet) -> Wallet:
        """Add a new wallet to the database."""
        ...

    async def get_wallet_by_id(self, wallet_id: uuid.UUID) -> Wallet | None:
        """Retrieve a wallet by its ID."""
        ...

    async def get_wallets_by_user_id(self, user_id: uuid.UUID) -> list[Wallet]:
        """Retrieve all wallets for a specific user."""
        ...

    async def get_wallet_by_user_and_asset(
        self, user_id: uuid.UUID, asset_id: uuid.UUID
    ) -> Wallet | None:
        """Retrieve a specific asset wallet for a specific user."""
        ...

    async def update_wallet(self, wallet: Wallet) -> Wallet:
        """Update existing wallet records (e.g., balance updates)."""
        ...
