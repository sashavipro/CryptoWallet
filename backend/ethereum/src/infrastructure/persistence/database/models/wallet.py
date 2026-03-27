"""ethereum/src/infrastructure/persistence/database/models/wallet.py."""

import datetime
import uuid
from decimal import Decimal

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .base import CreatedAt


class Wallet(Base):
    """SQLAlchemy model for user crypto wallets."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )

    address: Mapped[str] = mapped_column(String(42), index=True, nullable=False)
    private_key_encrypted: Mapped[str] = mapped_column(String, nullable=False)

    balance: Mapped[Decimal] = mapped_column(Numeric, default=0, nullable=False)
    balance_updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[CreatedAt]

    __table_args__ = (
        UniqueConstraint("user_id", "asset_id", name="uq_wallet_user_asset"),
    )
