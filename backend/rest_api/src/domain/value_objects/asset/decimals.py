"""ethereum/src/domain/value_objects/asset/decimals.py."""

from dataclasses import dataclass

from src.domain.exceptions import InvalidDecimalsException

MAX_EVM_DECIMALS = 36


@dataclass(frozen=True)
class AssetDecimals:
    """Value object representing the number of decimal places for a token."""

    value: int

    def __post_init__(self) -> None:
        """Validate that decimals are within a reasonable EVM range (0-36)."""
        if not (0 <= self.value <= MAX_EVM_DECIMALS):
            raise InvalidDecimalsException
