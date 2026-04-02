"""rest_api/src/domain/value_objects/asset/network.py."""

from dataclasses import dataclass

from src.domain.exceptions import InvalidNetworkNameException


@dataclass(frozen=True)
class AssetNetwork:
    """Value object representing the blockchain network name.

    Examples: Ethereum, Sepolia.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate that the network name is not empty."""
        if not self.value or not self.value.strip():
            raise InvalidNetworkNameException
