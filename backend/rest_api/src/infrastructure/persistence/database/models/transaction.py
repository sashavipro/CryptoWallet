"""rest_api/src/infrastructure/persistence/database/models/transaction.py."""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .base import CreatedAt


class Transaction(Base):
    """SQLAlchemy model for blockchain transactions."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )

    tx_hash: Mapped[str] = mapped_column(
        String(66), unique=True, index=True, nullable=False
    )
    from_address: Mapped[str] = mapped_column(String(42), index=True, nullable=False)
    to_address: Mapped[str] = mapped_column(String(42), index=True, nullable=False)

    value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    tx_fee: Mapped[Decimal] = mapped_column(Numeric, default=0, nullable=False)

    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    created_at: Mapped[CreatedAt]
