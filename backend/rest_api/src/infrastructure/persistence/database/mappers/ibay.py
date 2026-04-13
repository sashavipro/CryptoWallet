"""rest_api/src/infrastructure/persistence/database/mappers/ibay.py."""

from decimal import Decimal

from src.domain.entities.ibay import Order as DomainOrder
from src.domain.entities.ibay import Product as DomainProduct
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.product import Price
from src.domain.value_objects.product import ProductName
from src.infrastructure.persistence.database.models.ibay import Order as DBOrder
from src.infrastructure.persistence.database.models.ibay import Product as DBProduct


def map_product_to_domain(model: DBProduct) -> DomainProduct:
    """Map a SQLAlchemy Product model to a Domain Product entity."""
    return DomainProduct(
        id=model.id,
        user_id=model.user_id,
        wallet_id=model.wallet_id,
        title=ProductName(model.title),
        price_eth=Price(Decimal(str(model.price_eth))),
        photo_url=model.photo_url,
        created_at=model.created_at,
    )


def map_domain_to_product_model(domain: DomainProduct) -> DBProduct:
    """Map a Domain Product entity to a SQLAlchemy Product model."""
    return DBProduct(
        id=domain.id,
        user_id=domain.user_id,
        wallet_id=domain.wallet_id,
        title=domain.title.value,
        price_eth=domain.price_eth.amount,
        photo_url=domain.photo_url,
        created_at=domain.created_at,
    )


def map_order_to_domain(model: DBOrder) -> DomainOrder:
    """Map a SQLAlchemy Order model to a Domain Order entity."""
    return DomainOrder(
        id=model.id,
        product_id=model.product_id,
        buyer_user_id=model.buyer_user_id,
        tx_hash=model.tx_hash,
        price_eth=Price(Decimal(str(model.price_eth))),
        status=OrderStatus(model.status),
        return_tx_hash=model.return_tx_hash,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def map_domain_to_order_model(domain: DomainOrder) -> DBOrder:
    """Map a Domain Order entity to a SQLAlchemy Order model."""
    return DBOrder(
        id=domain.id,
        product_id=domain.product_id,
        buyer_user_id=domain.buyer_user_id,
        tx_hash=domain.tx_hash,
        price_eth=domain.price_eth.amount,
        status=domain.status.value,
        return_tx_hash=domain.return_tx_hash,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
