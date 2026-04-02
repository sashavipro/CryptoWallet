"""rest_api/src/domain/entities/wallet.py."""

import uuid
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from decimal import Decimal

from src.domain.exceptions import NegativeBalanceException

from .base import BaseEntity


@dataclass(kw_only=True)
class Wallet(BaseEntity):
    """Domain entity representing a user's crypto wallet for a specific asset."""

    user_id: uuid.UUID
    asset_id: uuid.UUID
    address: str
    private_key_encrypted: str
    balance: Decimal = field(default_factory=lambda: Decimal("0.0"))
    balance_updated_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_balance(self, new_balance: Decimal, timestamp: datetime) -> None:
        """Update wallet balance with fresh timestamp validation."""
        if new_balance < 0:
            raise NegativeBalanceException

        self.balance = new_balance
        self.balance_updated_at = timestamp
