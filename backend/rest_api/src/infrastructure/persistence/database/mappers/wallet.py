"""ethereum/src/infrastructure/persistence/database/mappers/wallet.py."""

from src.domain.entities.wallet import Wallet as DomainWallet
from src.infrastructure.persistence.database.models.wallet import Wallet as DBWallet


def map_wallet_to_domain(db_wallet: DBWallet) -> DomainWallet:
    """Convert SQLAlchemy Wallet model to Domain Wallet entity."""
    return DomainWallet(
        id=db_wallet.id,
        user_id=db_wallet.user_id,
        asset_id=db_wallet.asset_id,
        address=db_wallet.address,
        private_key_encrypted=db_wallet.private_key_encrypted,
        balance=db_wallet.balance,
        balance_updated_at=db_wallet.balance_updated_at,
        created_at=db_wallet.created_at,
    )


def map_domain_to_model(domain_wallet: DomainWallet) -> DBWallet:
    """Convert Domain Wallet entity to SQLAlchemy Wallet model."""
    return DBWallet(
        id=domain_wallet.id,
        user_id=domain_wallet.user_id,
        asset_id=domain_wallet.asset_id,
        address=domain_wallet.address,
        private_key_encrypted=domain_wallet.private_key_encrypted,
        balance=domain_wallet.balance,
        balance_updated_at=domain_wallet.balance_updated_at,
        created_at=domain_wallet.created_at,
    )
