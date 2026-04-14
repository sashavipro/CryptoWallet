"""rest_api/src/application/dtos/response/ibay.py."""

import datetime
import uuid
from dataclasses import dataclass
from decimal import Decimal

from src.domain.value_objects.order_status import OrderStatus


@dataclass(kw_only=True)
class ProductResponseDTO:
    """DTO representing a product returned to the presentation layer."""

    id: uuid.UUID
    user_id: uuid.UUID
    wallet_id: uuid.UUID
    seller_address: str
    title: str
    price_eth: Decimal
    photo_url: str | None
    created_at: datetime.datetime


@dataclass(kw_only=True)
class OrderResponseDTO:
    """DTO representing an order returned to the presentation layer."""

    id: uuid.UUID
    product_id: uuid.UUID
    buyer_user_id: uuid.UUID
    tx_hash: str
    price_eth: Decimal
    status: OrderStatus
    return_tx_hash: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
