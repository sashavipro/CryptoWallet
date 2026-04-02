"""rest_api/src/domain/entities/asset.py."""

from dataclasses import dataclass

from src.domain.exceptions import InvalidAssetConfigurationException
from src.domain.value_objects.asset import AssetType

from .base import BaseEntity


@dataclass(kw_only=True)
class Asset(BaseEntity):
    """Domain entity representing a cryptocurrency asset (Token or Native)."""

    ticker: str
    name: str
    network: str
    asset_type: AssetType
    decimals: int
    contract_address: str | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate asset configuration rules."""
        if self.asset_type == AssetType.ERC20 and not self.contract_address:
            raise InvalidAssetConfigurationException
