"""ethereum/src/domain/value_objects/transaction/tx_fee.py."""

from dataclasses import dataclass
from decimal import Decimal

from src.domain.exceptions import NegativeTransactionFeeException


@dataclass(frozen=True)
class TxFee:
    """Value object representing the blockchain network fee (Gas)."""

    value: Decimal

    def __post_init__(self) -> None:
        """Validate that the fee is non-negative."""
        if self.value < 0:
            raise NegativeTransactionFeeException
