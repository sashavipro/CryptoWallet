"""rest_api/src/domain/services/ibay_order.py."""

from decimal import Decimal

from src.domain.entities.ibay import Order
from src.domain.exceptions import OrderStateMachineError
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.product import Price


class OrderDomainService:
    """Domain service encapsulating business rules for iBay orders.

    This service handles state transitions and related domain logic.
    """

    @staticmethod
    def start_delivery(order: Order) -> None:
        """Transition order to DELIVERY state."""
        if order.status != OrderStatus.NEW:
            msg = (
                f"Cannot transition to DELIVERY from {order.status.value}. "
                "Expected NEW."
            )
            raise OrderStateMachineError(msg)

        order.status = OrderStatus.DELIVERY

    @staticmethod
    def complete_order(order: Order) -> None:
        """Transition order to COMPLETED state."""
        if order.status != OrderStatus.DELIVERY:
            msg = (
                f"Cannot transition to COMPLETED from {order.status.value}. "
                "Expected DELIVERY."
            )
            raise OrderStateMachineError(msg)

        order.status = OrderStatus.COMPLETED

    @staticmethod
    def fail_order_and_calculate_refund(order: Order, tx_fee_eth: Decimal) -> Price:
        """Fail the order and calculate the refund amount based on business rules.

        Refund logic: Order Price - (Payment Transaction Fee * 1.5).
        Returns a validated Price Value Object.
        """
        if order.status not in (OrderStatus.NEW, OrderStatus.DELIVERY):
            msg = f"Cannot fail order from status {order.status.value}."
            raise OrderStateMachineError(msg)

        order.status = OrderStatus.FAILED

        commission = tx_fee_eth * Decimal("1.5")
        refund_amount = order.price_eth.amount - commission

        refund_amount = max(refund_amount, Decimal("0"))

        return Price(refund_amount)

    @staticmethod
    def mark_as_returned(order: Order, return_tx_hash: str) -> None:
        """Transition order to RETURNED state after successful refund transaction."""
        if order.status != OrderStatus.FAILED:
            msg = (
                f"Cannot transition to RETURNED from {order.status.value}. "
                "Expected FAILED."
            )
            raise OrderStateMachineError(msg)

        order.status = OrderStatus.RETURNED
        order.return_tx_hash = return_tx_hash
