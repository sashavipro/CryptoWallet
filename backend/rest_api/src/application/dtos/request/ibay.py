"""rest_api/src/application/dtos/request/ibay.py."""

import uuid
from dataclasses import dataclass
from decimal import Decimal

from src.domain.value_objects.order_status import OrderStatus


@dataclass(kw_only=True)
class CreateProductSchema:
    """Schema for incoming product creation HTTP request."""

    wallet_id: uuid.UUID
    title: str
    price_eth: Decimal
    photo_url: str | None = None


@dataclass(kw_only=True)
class CreateOrderSchema:
    """Schema for incoming order creation HTTP request."""

    product_id: uuid.UUID
    tx_hash: str
    price_eth: Decimal


@dataclass(kw_only=True)
class UpdateStatusSchema:
    """Schema for internal order status updates."""

    status: str
    return_tx_hash: str | None = None
    tx_hash: str | None = None
    trigger_refund: bool = False


@dataclass(kw_only=True)
class CreateProductRequestDTO:
    """DTO for creating a new iBay product."""

    user_id: uuid.UUID
    wallet_id: uuid.UUID
    title: str
    price_eth: Decimal
    photo_url: str | None = None


@dataclass(kw_only=True)
class CreateOrderRequestDTO:
    """DTO for creating a new order."""

    product_id: uuid.UUID
    buyer_user_id: uuid.UUID
    tx_hash: str
    price_eth: Decimal


@dataclass(kw_only=True)
class UpdateOrderRequestDTO:
    """DTO for updating an existing order's status or details."""

    order_id: uuid.UUID
    status: OrderStatus
    return_tx_hash: str | None = None
    tx_hash: str | None = None
    trigger_refund: bool = False
