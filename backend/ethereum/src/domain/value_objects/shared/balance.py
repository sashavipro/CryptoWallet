"""ethereum/src/domain/value_objects/shared/balance.py."""

from dataclasses import dataclass
from decimal import Decimal

from src.domain.exceptions import NegativeBalanceException


@dataclass(frozen=True)
class Balance:
    """Value object representing a non-negative cryptocurrency balance."""

    value: Decimal

    def __post_init__(self) -> None:
        """Validate that the balance is not negative."""
        if self.value < 0:
            raise NegativeBalanceException
