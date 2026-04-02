"""rest_api/src/infrastructure/persistence/database/gateways/sqla_asset.py."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.asset import Asset as DomainAsset
from src.infrastructure.persistence.database.mappers.asset import map_asset_to_domain
from src.infrastructure.persistence.database.mappers.asset import map_domain_to_model
from src.infrastructure.persistence.database.models.asset import Asset as DBAsset

logger = logging.getLogger(__name__)


class AssetGateway:
    """Gateway for Asset database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize gateway with an active database session."""
        self.session = session

    async def add_asset(self, asset: DomainAsset) -> DomainAsset:
        """Add a new cryptocurrency asset to the database."""
        db_asset = map_domain_to_model(asset)
        self.session.add(db_asset)
        await self.session.flush()
        logger.info("Asset added: %s (%s)", asset.ticker, asset.network)
        return map_asset_to_domain(db_asset)

    async def get_asset_by_id(self, asset_id: uuid.UUID) -> DomainAsset | None:
        """Retrieve an asset by its unique ID."""
        query = select(DBAsset).where(DBAsset.id == asset_id)
        result = await self.session.execute(query)
        db_asset = result.scalar_one_or_none()

        return map_asset_to_domain(db_asset) if db_asset else None

    async def get_all_assets(self) -> list[DomainAsset]:
        """Retrieve all assets from the database."""
        query = select(DBAsset)
        result = await self.session.execute(query)
        db_assets = result.scalars().all()

        return [map_asset_to_domain(a) for a in db_assets]
