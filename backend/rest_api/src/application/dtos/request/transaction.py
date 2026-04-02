"""ethereum/src/application/dtos/requests/transaction.py."""

import uuid
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class CreatePendingTransactionRequest:
    """DTO for initiating a new transaction by a user."""

    wallet_id: uuid.UUID
    to_address: str
    value: Decimal


@dataclass
class CompleteTransactionRequest:
    """DTO for a background worker to report transaction completion/failure."""

    tx_id: uuid.UUID
    fee: Decimal
    is_success: bool
