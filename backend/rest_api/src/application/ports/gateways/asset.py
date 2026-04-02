"""rest_api/src/application/ports/gateways/asset.py."""

import uuid
from typing import Protocol

from src.domain.entities import Asset


class AssetGateway(Protocol):
    """Port for Asset database operations."""

    async def add_asset(self, asset: Asset) -> Asset:
        """Add a new cryptocurrency asset to the database."""
        ...

    async def get_asset_by_id(self, asset_id: uuid.UUID) -> Asset | None:
        """Retrieve an asset by its unique ID."""
        ...

    async def get_asset_by_ticker_and_network(
        self, ticker: str, network: str
    ) -> Asset | None:
        """Retrieve an asset by its ticker and network."""
        ...

    async def get_all_assets(self) -> list[Asset]:
        """Retrieve all available assets."""
        ...
