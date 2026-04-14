"""ibay/src/application/interactors/ibay_worker.py."""

import logging
import secrets

from src.application.ports.events import EventPublisher
from src.application.ports.providers import GoogleCheckerProvider
from src.application.ports.providers import InternalApiClient

logger = logging.getLogger(__name__)

DELIVERY_SUCCESS_RATE = 1.0


class UpdateOrderStatusInteractor:
    """Interactor for updating order status based on blockchain transaction results."""

    def __init__(self, api_client: InternalApiClient, event_publisher: EventPublisher):
        """Initialize the interactor with an API client and event publisher."""
        self.api_client = api_client
        self.event_publisher = event_publisher

    async def __call__(self, tx_id: str, real_tx_hash: str, tx_status: str) -> None:
        """Execute the interactor to process a transaction status update."""
        pending_hash = f"pending_{tx_id}"
        order = await self.api_client.get_order_by_tx_hash(pending_hash)
        if not order:
            order = await self.api_client.get_order_by_tx_hash(real_tx_hash)

        if not order:
            return

        current_status = order.get("status")

        if current_status == "NEW":
            new_status = "DELIVERY" if tx_status == "success" else "FAILED"
        elif current_status == "FAILED":
            new_status = "RETURNED" if tx_status == "success" else "FAILED"
            if new_status == current_status:
                return
        else:
            return

        await self.api_client.update_order_status(
            order["id"], new_status, real_tx_hash=real_tx_hash
        )
        await self.event_publisher.publish_ibay_order_updated(
            order_id=order["id"],
            product_id=order["product_id"],
            status=new_status,
            buyer_id=order["buyer_user_id"],
        )


class ProcessDeliveryInteractor:
    """Interactor for simulating order delivery processing."""

    def __init__(
        self,
        api_client: InternalApiClient,
        event_publisher: EventPublisher,
        google_checker: GoogleCheckerProvider,
    ):
        """Initialize the interactor with required clients and providers."""
        self.api_client = api_client
        self.event_publisher = event_publisher
        self.google_checker = google_checker

    async def __call__(self) -> bool:
        """Execute the delivery process for the oldest pending order."""
        order = await self.api_client.get_oldest_delivery_order()
        if not order:
            return False

        logger.info("Processing delivery for order: %s", order["id"])

        is_success = secrets.SystemRandom().random() < DELIVERY_SUCCESS_RATE

        if is_success:
            logger.info(
                "Order %s Delivery Success. Running stress test...", order["id"]
            )
            test_passed = await self.google_checker.run_stress_test(requests_count=50)
            new_status = "COMPLETED" if test_passed else "FAILED"
        else:
            logger.info("Order %s Delivery Failed (Random chance).", order["id"])
            new_status = "FAILED"

        trigger_refund = new_status == "FAILED"

        await self.api_client.update_order_status(
            order_id=order["id"], status=new_status, trigger_refund=trigger_refund
        )

        await self.event_publisher.publish_ibay_order_updated(
            order_id=order["id"],
            product_id=order["product_id"],
            status=new_status,
            buyer_id=order["buyer_user_id"],
        )
        return True
