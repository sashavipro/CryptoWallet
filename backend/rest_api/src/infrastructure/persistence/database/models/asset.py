"""rest_api/src/infrastructure/persistence/database/models/asset.py."""

import uuid

from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base


class Asset(Base):
    """SQLAlchemy model for cryptocurrency assets."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    network: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)
    decimals: Mapped[int] = mapped_column(Integer, nullable=False, default=18)
    contract_address: Mapped[str | None] = mapped_column(String(42), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
