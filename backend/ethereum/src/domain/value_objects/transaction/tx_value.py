"""ethereum/src/domain/value_objects/transaction/tx_value.py."""

from dataclasses import dataclass
from decimal import Decimal

from src.domain.exceptions import NegativeTransactionValueException


@dataclass(frozen=True)
class TxValue:
    """Value object representing the amount of crypto transferred."""

    value: Decimal

    def __post_init__(self) -> None:
        """Validate that the transaction value is non-negative."""
        if self.value < 0:
            raise NegativeTransactionValueException
