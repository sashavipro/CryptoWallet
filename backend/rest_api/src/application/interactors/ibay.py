"""rest_api/src/application/interactors/ibay.py."""

import logging
import uuid

from src.application.dtos.request.ibay import CreateOrderRequestDTO
from src.application.dtos.request.ibay import CreateProductRequestDTO
from src.application.dtos.response.ibay import OrderResponseDTO
from src.application.dtos.response.ibay import ProductResponseDTO
from src.application.ports.events import EventPublisher
from src.application.ports.gateways.ibay import OrderGateway
from src.application.ports.gateways.ibay import ProductGateway
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.gateways.wallet import WalletGateway
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.ibay import Order
from src.domain.entities.ibay import Product
from src.domain.exceptions import ProductNotFoundException
from src.domain.exceptions import WalletNotFoundException
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.product import Price
from src.domain.value_objects.product import ProductName

logger = logging.getLogger(__name__)


class CreateProductInteractor:
    """Use Case: Create a new product listing on iBay."""

    def __init__(  # noqa: PLR0913
        self,
        product_gateway: ProductGateway,
        wallet_gateway: WalletGateway,
        uow: UnitOfWork,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
        event_publisher: EventPublisher,
    ) -> None:
        """Initialize with necessary gateways and providers."""
        self.product_gateway = product_gateway
        self.wallet_gateway = wallet_gateway
        self.uow = uow
        self.id_generator = id_generator
        self.time_provider = time_provider
        self.event_publisher = event_publisher

    async def __call__(
        self, user_id: uuid.UUID, request: CreateProductRequestDTO
    ) -> ProductResponseDTO:
        """Execute the use case to create a new product."""
        logger.info("Creating new iBay product for user: %s", user_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(request.wallet_id)
        if not wallet or wallet.user_id != user_id:
            msg = "Invalid wallet specified for this product."
            raise WalletNotFoundException(msg)

        now = self.time_provider.now()
        product = Product(
            id=self.id_generator.generate(),
            user_id=user_id,
            wallet_id=request.wallet_id,
            title=ProductName(request.title),
            price_eth=Price(request.price_eth),
            photo_url=request.photo_url,
            created_at=now,
        )

        async with self.uow:
            saved_product = await self.product_gateway.add_product(product)

        await self.event_publisher.publish_ibay_product_created(
            product_id=str(saved_product.id),
            title=saved_product.title.value,
            price=str(saved_product.price_eth.amount),
            photo_url=saved_product.photo_url,
        )

        return ProductResponseDTO(
            id=saved_product.id,
            user_id=saved_product.user_id,
            wallet_id=saved_product.wallet_id,
            title=saved_product.title.value,
            price_eth=saved_product.price_eth.amount,
            photo_url=saved_product.photo_url,
            created_at=saved_product.created_at,
        )


class GetProductsInteractor:
    """Use Case: Retrieve all active iBay products."""

    def __init__(self, product_gateway: ProductGateway) -> None:
        """Initialize with the product gateway."""
        self.product_gateway = product_gateway

    async def __call__(self) -> list[ProductResponseDTO]:
        """Execute the use case to fetch all active products."""
        products = await self.product_gateway.get_all_products()
        return [
            ProductResponseDTO(
                id=p.id,
                user_id=p.user_id,
                wallet_id=p.wallet_id,
                title=p.title.value,
                price_eth=p.price_eth.amount,
                photo_url=p.photo_url,
                created_at=p.created_at,
            )
            for p in products
        ]


class CreateOrderInteractor:
    """Use Case: Create a new order for a product."""

    def __init__(  # noqa: PLR0913
        self,
        order_gateway: OrderGateway,
        product_gateway: ProductGateway,
        uow: UnitOfWork,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
        event_publisher: EventPublisher,
    ) -> None:
        """Initialize with necessary gateways and providers."""
        self.order_gateway = order_gateway
        self.product_gateway = product_gateway
        self.uow = uow
        self.id_generator = id_generator
        self.time_provider = time_provider
        self.event_publisher = event_publisher

    async def __call__(
        self, buyer_id: uuid.UUID, request: CreateOrderRequestDTO
    ) -> OrderResponseDTO:
        """Execute the use case to create a new order."""
        logger.info(
            "User %s is creating an order for product %s", buyer_id, request.product_id
        )

        product = await self.product_gateway.get_product_by_id(request.product_id)
        if not product:
            msg = "Product not found."
            raise ProductNotFoundException(msg)

        now = self.time_provider.now()

        order = Order(
            id=self.id_generator.generate(),
            product_id=product.id,
            buyer_user_id=buyer_id,
            tx_hash=request.tx_hash,
            price_eth=Price(request.price_eth),
            status=OrderStatus.NEW,
            return_tx_hash=None,
            created_at=now,
            updated_at=now,
        )

        async with self.uow:
            saved_order = await self.order_gateway.add_order(order)

        await self.event_publisher.publish_ibay_order_created(
            order_id=str(saved_order.id),
            product_id=str(saved_order.product_id),
            buyer_id=str(saved_order.buyer_user_id),
            status=saved_order.status.value,
            price=str(saved_order.price_eth.amount),
        )

        return OrderResponseDTO(
            id=saved_order.id,
            product_id=saved_order.product_id,
            buyer_user_id=saved_order.buyer_user_id,
            tx_hash=saved_order.tx_hash,
            price_eth=saved_order.price_eth.amount,
            status=saved_order.status,
            return_tx_hash=saved_order.return_tx_hash,
            created_at=saved_order.created_at,
            updated_at=saved_order.updated_at,
        )


class GetOrdersInteractor:
    """Use Case: Retrieve all orders for the current user."""

    def __init__(self, order_gateway: OrderGateway) -> None:
        """Initialize with the order gateway."""
        self.order_gateway = order_gateway

    async def __call__(self, buyer_id: uuid.UUID) -> list[OrderResponseDTO]:
        """Execute the use case to fetch a buyer's orders."""
        orders = await self.order_gateway.get_orders_by_buyer_id(buyer_id)
        return [
            OrderResponseDTO(
                id=o.id,
                product_id=o.product_id,
                buyer_user_id=o.buyer_user_id,
                tx_hash=o.tx_hash,
                price_eth=o.price_eth.amount,
                status=o.status,
                return_tx_hash=o.return_tx_hash,
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
            for o in orders
        ]
