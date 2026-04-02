"""ethereum/src/infrastructure/persistence/database/mappers/asset.py."""

from src.domain.entities.asset import Asset as DomainAsset
from src.domain.entities.asset import AssetType
from src.infrastructure.persistence.database.models.asset import Asset as DBAsset


def map_asset_to_domain(db_asset: DBAsset) -> DomainAsset:
    """Convert SQLAlchemy Asset model to Domain Asset entity."""
    return DomainAsset(
        id=db_asset.id,
        ticker=db_asset.ticker,
        name=db_asset.name,
        network=db_asset.network,
        asset_type=AssetType(db_asset.asset_type),
        decimals=db_asset.decimals,
        contract_address=db_asset.contract_address,
        is_active=db_asset.is_active,
    )


def map_domain_to_model(domain_asset: DomainAsset) -> DBAsset:
    """Convert Domain Asset entity to SQLAlchemy Asset model."""
    return DBAsset(
        id=domain_asset.id,
        ticker=domain_asset.ticker,
        name=domain_asset.name,
        network=domain_asset.network,
        asset_type=domain_asset.asset_type.value,
        decimals=domain_asset.decimals,
        contract_address=domain_asset.contract_address,
        is_active=domain_asset.is_active,
    )
