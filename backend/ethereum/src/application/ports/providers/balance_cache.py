"""ethereum/src/application/ports/providers/balance_cache.py."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from src.application.dtos.response import CachedBalance


class BalanceCache(Protocol):
    """Port for caching wallet balances."""

    async def get_balance(self, wallet_id: uuid.UUID) -> CachedBalance | None:
        """Retrieve cached balance and its last update timestamp."""
        ...

    async def set_balance(
        self, wallet_id: uuid.UUID, balance: Decimal, updated_at: datetime
    ) -> None:
        """Set/update cached balance with its update timestamp."""
        ...

    async def invalidate_balance(self, wallet_id: uuid.UUID) -> None:
        """Remove cached balance for a wallet."""
        ...
