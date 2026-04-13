"""rest_api/src/domain/entities/ibay.py."""

import datetime
import uuid
from dataclasses import dataclass

from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.product import Price
from src.domain.value_objects.product import ProductName


@dataclass
class Product:
    """Domain entity representing a product (lot) listed on iBay."""

    id: uuid.UUID
    user_id: uuid.UUID
    wallet_id: uuid.UUID
    title: ProductName
    price_eth: Price
    photo_url: str | None
    created_at: datetime.datetime


@dataclass
class Order:
    """Domain entity representing a user's order for an iBay product."""

    id: uuid.UUID
    product_id: uuid.UUID
    buyer_user_id: uuid.UUID
    tx_hash: str
    price_eth: Price
    status: OrderStatus
    return_tx_hash: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
