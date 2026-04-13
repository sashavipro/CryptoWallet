"""ibay/src/application/interactors/ibay_worker.py."""

import logging
import secrets
from decimal import Decimal

from src.application.ports.events import EventPublisher
from src.application.ports.gateways.ibay import OrderGateway
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.providers.google_checker import GoogleCheckerProvider
from src.application.ports.providers.worker_client import EthereumWorkerClient
from src.domain.services.ibay_order import OrderDomainService
from src.domain.value_objects.order_status import OrderStatus

logger = logging.getLogger(__name__)


class UpdateOrderStatusInteractor:
    """Managing Order Status Upon Payment Transaction Confirmation."""

    def __init__(
        self,
        order_gateway: OrderGateway,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
    ) -> None:
        """Initialize the interactor with required gateways and publishers."""
        self.order_gateway = order_gateway
        self.uow = uow
        self.event_publisher = event_publisher

    async def __call__(self, tx_hash: str, tx_status: str) -> None:
        """Handle transaction events (success/failure)."""
        logger.info(
            "Updating order status for tx_hash: %s. Network status: %s",
            tx_hash,
            tx_status,
        )

        async with self.uow:
            order = await self.order_gateway.get_order_by_tx_hash(tx_hash)
            if not order:
                return

            if order.status != OrderStatus.NEW:
                logger.warning("Order %s is not in NEW state, skipping.", order.id)
                return

            if tx_status == "success":
                OrderDomainService.start_delivery(order)
            elif tx_status == "failed":
                order.status = OrderStatus.FAILED

            await self.order_gateway.update_order(order)

        await self.event_publisher.publish_ibay_order_updated(
            order_id=str(order.id),
            product_id=str(order.product_id),
            status=order.status.value,
            buyer_id=str(order.buyer_user_id),
        )


class ProcessDeliveryInteractor:
    """A background task that simulates logistics and delivery."""

    def __init__(
        self,
        order_gateway: OrderGateway,
        uow: UnitOfWork,
        google_checker: GoogleCheckerProvider,
        event_publisher: EventPublisher,
        eth_client: EthereumWorkerClient,
    ) -> None:
        """Initialize the delivery processing interactor."""
        self.order_gateway = order_gateway
        self.uow = uow
        self.google_checker = google_checker
        self.event_publisher = event_publisher
        self.eth_client = eth_client

    async def __call__(self) -> None:
        """Берет самый старый заказ в доставке и бросает кубик."""
        async with self.uow:
            order = await self.order_gateway.get_oldest_order_by_status(
                OrderStatus.DELIVERY
            )

        if not order:
            return

        logger.info("Processing delivery for order: %s", order.id)

        is_success = secrets.choice([True, False])

        if is_success:
            logger.info(
                "Order %s Delivery Success. Running 10k stress test...", order.id
            )
            test_passed = await self.google_checker.run_stress_test(
                requests_count=10000
            )

            if test_passed:
                OrderDomainService.complete_order(order)
            else:
                logger.warning(
                    "Stress test failed for order %s. Failing order.", order.id
                )
                is_success = False

        if not is_success:
            logger.info("Order %s Delivery Failed. Initiating refund...", order.id)

            tx_data = await self.eth_client.check_tx_status(order.tx_hash)
            tx_fee = (
                Decimal(tx_data.get("tx_fee", "0.0001"))
                if tx_data
                else Decimal("0.0001")
            )

            OrderDomainService.fail_order_and_calculate_refund(order, tx_fee)

            try:
                return_tx_hash = await self.eth_client.request_faucet(
                    "BUYER_ADDRESS_HERE"
                )
                OrderDomainService.mark_as_returned(order, return_tx_hash)
            except Exception:
                logger.exception(
                    "Failed to process refund transaction for order %s", order.id
                )

        async with self.uow:
            await self.order_gateway.update_order(order)

        await self.event_publisher.publish_ibay_order_updated(
            order_id=str(order.id),
            product_id=str(order.product_id),
            status=order.status.value,
            buyer_id=str(order.buyer_user_id),
        )
