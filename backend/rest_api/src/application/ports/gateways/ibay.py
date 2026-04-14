"""rest_api/src/application/ports/gateways/ibay.py."""

import uuid
from typing import Protocol

from src.domain.entities.ibay import Order
from src.domain.entities.ibay import Product
from src.domain.value_objects.order_status import OrderStatus


class ProductGateway(Protocol):
    """Port for iBay Product database operations."""

    async def add_product(self, product: Product) -> Product:
        """Add a new product to the database."""
        ...

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product | None:
        """Retrieve a product by its ID."""
        ...

    async def get_all_products(self) -> list[Product]:
        """Retrieve all active products."""
        ...


class OrderGateway(Protocol):
    """Port for iBay Order database operations."""

    async def add_order(self, order: Order) -> Order:
        """Add a new order to the database."""
        ...

    async def get_order_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Retrieve an order by its ID."""
        ...

    async def get_orders_by_buyer_id(self, buyer_id: uuid.UUID) -> list[Order]:
        """Retrieve all orders placed by a specific user."""
        ...

    async def get_oldest_order_by_status(self, status: OrderStatus) -> Order | None:
        """Retrieve the oldest order with a specific status.

        Useful for background workers processing queue-like states (e.g., DELIVERY).
        """
        ...

    async def update_order(self, order: Order) -> Order:
        """Update an existing order's data (e.g., status changes)."""
        ...

    async def get_order_by_tx_hash(self, tx_hash: str) -> Order | None:
        """Retrieve an order by its transaction hash."""
        ...
