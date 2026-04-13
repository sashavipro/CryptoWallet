"""rest_api/src/domain/value_objects/product.py."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ProductName:
    """Value object representing a valid product name."""

    value: str

    def __post_init__(self) -> None:
        """Validate the product name."""
        max_length = 255
        clean_value = self.value.strip()
        if not clean_value:
            msg = "Product name cannot be empty or just whitespace."
            raise ValueError(msg)
        if len(clean_value) > max_length:
            msg = "Product name cannot exceed 255 characters."
            raise ValueError(msg)

        object.__setattr__(self, "value", clean_value)


@dataclass(frozen=True)
class Price:
    """Value object representing a price amount in cryptocurrency."""

    amount: Decimal

    def __post_init__(self) -> None:
        """Validate that the price is not negative."""
        if self.amount < Decimal("0"):
            msg = "Price cannot be negative."
            raise ValueError(msg)
