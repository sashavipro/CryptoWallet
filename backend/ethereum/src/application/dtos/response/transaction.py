"""ethereum/src/application/dtos/responses/transaction.py."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class TransactionResponse:
    """DTO for exposing transaction details."""

    id: uuid.UUID
    wallet_id: uuid.UUID
    tx_hash: str
    from_address: str
    to_address: str
    value: Decimal
    tx_fee: Decimal
    status: str  # "PENDING", "SUCCESS", or "FAILED"
    created_at: datetime
