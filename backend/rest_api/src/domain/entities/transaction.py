"""rest_api/src/domain/entities/transaction.py."""

import uuid
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from decimal import Decimal

from src.domain.exceptions import InvalidTransactionStateException
from src.domain.exceptions import NegativeFeeException
from src.domain.value_objects.transaction import TransactionStatus

from .base import BaseEntity


@dataclass(kw_only=True)
class Transaction(BaseEntity):
    """Domain entity representing an on-chain transaction."""

    wallet_id: uuid.UUID
    tx_hash: str
    from_address: str
    to_address: str
    value: Decimal
    tx_fee: Decimal = field(default_factory=lambda: Decimal("0.0"))
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def mark_success(self, fee: Decimal) -> None:
        """Mark transaction as successfully mined in the blockchain."""
        if self.status != TransactionStatus.PENDING:
            raise InvalidTransactionStateException

        if fee < 0:
            raise NegativeFeeException

        self.status = TransactionStatus.SUCCESS
        self.tx_fee = fee

    def mark_failed(self) -> None:
        """Mark transaction as failed."""
        if self.status != TransactionStatus.PENDING:
            raise InvalidTransactionStateException

        self.status = TransactionStatus.FAILED
