"""rest_api/src/infrastructure/persistence/database/models/ibay.py."""

import datetime
import uuid

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.domain.value_objects.order_status import OrderStatus
from src.infrastructure.persistence.database.models.base import Base


class Product(Base):
    """SQLAlchemy model representing the ibay_products table."""

    __tablename__ = "ibay_products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wallets.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    price_eth: Mapped[float] = mapped_column(Numeric(36, 18), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.UTC)
    )


class Order(Base):
    """SQLAlchemy model representing the ibay_orders table."""

    __tablename__ = "ibay_orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ibay_products.id"), nullable=False
    )
    buyer_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    tx_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    price_eth: Mapped[float] = mapped_column(Numeric(36, 18), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), default=OrderStatus.NEW, nullable=False
    )
    return_tx_hash: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.UTC)
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )
