"""rest_api/src/infrastructure/persistence/database/mappers/transaction.py."""

from src.domain.entities.transaction import Transaction as DomainTransaction
from src.domain.entities.transaction import TransactionStatus
from src.infrastructure.persistence.database.models.transaction import (
    Transaction as DBTransaction,
)


def map_transaction_to_domain(db_tx: DBTransaction) -> DomainTransaction:
    """Convert SQLAlchemy Transaction model to Domain Transaction entity."""
    return DomainTransaction(
        id=db_tx.id,
        wallet_id=db_tx.wallet_id,
        tx_hash=db_tx.tx_hash,
        from_address=db_tx.from_address,
        to_address=db_tx.to_address,
        value=db_tx.value,
        tx_fee=db_tx.tx_fee,
        status=TransactionStatus(db_tx.status),
        created_at=db_tx.created_at,
    )


def map_domain_to_model(domain_tx: DomainTransaction) -> DBTransaction:
    """Convert Domain Transaction entity to SQLAlchemy Transaction model."""
    return DBTransaction(
        id=domain_tx.id,
        wallet_id=domain_tx.wallet_id,
        tx_hash=domain_tx.tx_hash,
        from_address=domain_tx.from_address,
        to_address=domain_tx.to_address,
        value=domain_tx.value,
        tx_fee=domain_tx.tx_fee,
        status=domain_tx.status.value,
        created_at=domain_tx.created_at,
    )
