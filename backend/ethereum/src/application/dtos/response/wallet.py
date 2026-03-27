"""ethereum/src/application/dtos/responses/wallet.py."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class WalletResponse:
    """DTO for exposing wallet details to the presentation layer.

    Security note: Private key is strictly excluded from this response.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    asset_id: uuid.UUID
    address: str
    balance: Decimal
    balance_updated_at: datetime | None
    created_at: datetime
