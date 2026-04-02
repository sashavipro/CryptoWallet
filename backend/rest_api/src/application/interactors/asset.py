"""rest_api/src/application/interactors/asset.py."""

import logging
from typing import Any

from src.application.ports.gateways.asset import AssetGateway

logger = logging.getLogger(__name__)


class GetAssetsInteractor:
    """Use case for retrieving all available crypto assets."""

    def __init__(self, asset_gateway: AssetGateway) -> None:
        """Initialize the interactor with an asset gateway."""
        self.asset_gateway = asset_gateway

    async def __call__(self) -> list[dict[str, Any]]:
        """Retrieve all available crypto assets from the gateway."""
        logger.info("Retrieving all assets")
        assets = await self.asset_gateway.get_all_assets()

        return [{"id": str(a.id), "ticker": a.ticker, "name": a.name} for a in assets]
