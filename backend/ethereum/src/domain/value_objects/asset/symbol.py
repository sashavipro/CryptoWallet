"""ethereum/src/domain/value_objects/asset/symbol.py."""

import re
from dataclasses import dataclass

from src.domain.exceptions import InvalidAssetSymbolException

SYMBOL_REGEX = re.compile(r"^[A-Z0-9]{2,10}$")


@dataclass(frozen=True)
class AssetSymbol:
    """Value object representing a cryptocurrency ticker/symbol (e.g., ETH, USDT)."""

    value: str

    def __post_init__(self) -> None:
        """Validate the symbol format."""
        if not SYMBOL_REGEX.match(self.value):
            raise InvalidAssetSymbolException
