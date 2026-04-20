"""rest_api/src/infrastructure/persistence/database/gateways/sqla_ibay.py."""

import uuid

from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.gateways import OrderGateway
from src.application.ports.gateways import ProductGateway
from src.domain.entities import Order as DomainOrder
from src.domain.entities import Product as DomainProduct
from src.domain.value_objects.order_status import OrderStatus
from src.infrastructure.persistence.database.mappers.ibay import (
    map_domain_to_order_model,
)
from src.infrastructure.persistence.database.mappers.ibay import (
    map_domain_to_product_model,
)
from src.infrastructure.persistence.database.mappers.ibay import map_order_to_domain
from src.infrastructure.persistence.database.mappers.ibay import map_product_to_domain
from src.infrastructure.persistence.database.models.ibay import Order as DBOrder
from src.infrastructure.persistence.database.models.ibay import Product as DBProduct


class SqlaProductGateway(ProductGateway):
    """SQLAlchemy implementation of the ProductGateway."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize gateway with an AsyncSession."""
        self.session = session

    async def add_product(self, product: DomainProduct) -> DomainProduct:
        """Save a new domain product to the DB."""
        db_product = map_domain_to_product_model(product)
        self.session.add(db_product)
        await self.session.flush()
        return map_product_to_domain(db_product)

    async def get_product_by_id(self, product_id: uuid.UUID) -> DomainProduct | None:
        """Fetch a product by ID and return the domain entity."""
        stmt = select(DBProduct).where(DBProduct.id == product_id)
        result = await self.session.execute(stmt)
        db_product = result.scalars().first()

        if not db_product:
            return None
        return map_product_to_domain(db_product)

    async def get_all_products(self) -> list[DomainProduct]:
        """Fetch all products."""
        stmt = select(DBProduct).order_by(DBProduct.created_at.desc())
        result = await self.session.execute(stmt)
        db_products = result.scalars().all()
        return [map_product_to_domain(p) for p in db_products]


class SqlaOrderGateway(OrderGateway):
    """SQLAlchemy implementation of the OrderGateway."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize gateway with an AsyncSession."""
        self.session = session

    async def add_order(self, order: DomainOrder) -> DomainOrder:
        """Save a new domain order to the DB."""
        db_order = map_domain_to_order_model(order)
        self.session.add(db_order)
        await self.session.flush()
        return map_order_to_domain(db_order)

    async def get_order_by_id(self, order_id: uuid.UUID) -> DomainOrder | None:
        """Fetch an order by ID."""
        stmt = select(DBOrder).where(DBOrder.id == order_id)
        result = await self.session.execute(stmt)
        db_order = result.scalars().first()

        if not db_order:
            return None
        return map_order_to_domain(db_order)

    async def get_order_by_tx_hash(self, tx_hash: str) -> DomainOrder | None:
        """Fetch an order strictly by its transaction hash OR return_tx_hash."""
        stmt = select(DBOrder).where(
            or_(DBOrder.tx_hash == tx_hash, DBOrder.return_tx_hash == tx_hash)
        )
        result = await self.session.execute(stmt)
        db_order = result.scalars().first()

        if not db_order:
            return None
        return map_order_to_domain(db_order)

    async def get_orders_by_buyer_id(self, buyer_id: uuid.UUID) -> list[DomainOrder]:
        """Fetch all orders for a specific buyer."""
        stmt = (
            select(DBOrder)
            .where(DBOrder.buyer_user_id == buyer_id)
            .order_by(DBOrder.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_orders = result.scalars().all()
        return [map_order_to_domain(o) for o in db_orders]

    async def get_oldest_order_by_status(
        self, status: OrderStatus
    ) -> DomainOrder | None:
        """Fetch the oldest order in a specific status."""
        stmt = (
            select(DBOrder)
            .where(DBOrder.status == status)
            .order_by(DBOrder.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        db_order = result.scalars().first()

        if not db_order:
            return None
        return map_order_to_domain(db_order)

    async def update_order(self, order: DomainOrder) -> DomainOrder:
        """Update an existing order in the DB."""
        db_order = map_domain_to_order_model(order)
        merged_order = await self.session.merge(db_order)
        await self.session.flush()
        return map_order_to_domain(merged_order)
