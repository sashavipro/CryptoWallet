"""ethereum/src/infrastructure/persistence/database/gateways/sqla_wallet.py."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.wallet import Wallet as DomainWallet
from src.infrastructure.persistence.database.mappers.wallet import map_domain_to_model
from src.infrastructure.persistence.database.mappers.wallet import map_wallet_to_domain
from src.infrastructure.persistence.database.models.wallet import Wallet as DBWallet

logger = logging.getLogger(__name__)


class WalletGateway:
    """Gateway for Wallet database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize gateway with an active database session."""
        self.session = session

    async def add_wallet(self, wallet: DomainWallet) -> DomainWallet:
        """Add a new wallet to the database."""
        db_wallet = map_domain_to_model(wallet)
        self.session.add(db_wallet)
        await self.session.flush()
        logger.info("Wallet added for user: %s", wallet.user_id)
        return map_wallet_to_domain(db_wallet)

    async def get_wallet_by_id(self, wallet_id: uuid.UUID) -> DomainWallet | None:
        """Retrieve a wallet by its ID."""
        query = select(DBWallet).where(DBWallet.id == wallet_id)
        result = await self.session.execute(query)
        db_wallet = result.scalar_one_or_none()

        return map_wallet_to_domain(db_wallet) if db_wallet else None

    async def get_wallets_by_user_id(self, user_id: uuid.UUID) -> list[DomainWallet]:
        """Retrieve all wallets for a specific user."""
        query = select(DBWallet).where(DBWallet.user_id == user_id)
        result = await self.session.execute(query)
        db_wallets = result.scalars().all()

        return [map_wallet_to_domain(w) for w in db_wallets]

    async def get_wallet_by_user_and_asset(
        self, user_id: uuid.UUID, asset_id: uuid.UUID
    ) -> DomainWallet | None:
        """Retrieve a specific asset wallet for a specific user."""
        query = select(DBWallet).where(
            DBWallet.user_id == user_id, DBWallet.asset_id == asset_id
        )
        result = await self.session.execute(query)
        db_wallet = result.scalar_one_or_none()

        return map_wallet_to_domain(db_wallet) if db_wallet else None

    async def update_wallet(self, wallet: DomainWallet) -> DomainWallet:
        """Update existing wallet records (e.g., balance updates)."""
        db_wallet = map_domain_to_model(wallet)
        merged_wallet = await self.session.merge(db_wallet)
        await self.session.flush()
        logger.debug("Wallet updated: %s", wallet.id)
        return map_wallet_to_domain(merged_wallet)
