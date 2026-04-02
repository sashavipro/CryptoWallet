"""ethereum/src/domain/value_objects/shared/address.py."""

import re
from dataclasses import dataclass

from src.domain.exceptions import InvalidEthereumAddressException

ETH_ADDRESS_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")


@dataclass(frozen=True)
class EthereumAddress:
    """Value object representing a valid EVM blockchain address."""

    value: str

    def __post_init__(self) -> None:
        """Validate the Ethereum address format."""
        if not ETH_ADDRESS_REGEX.match(self.value):
            raise InvalidEthereumAddressException
