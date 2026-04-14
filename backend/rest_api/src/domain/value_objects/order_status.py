"""rest_api/src/domain/value_objects/order_status.py."""

from enum import Enum


class OrderStatus(str, Enum):
    """Enumeration representing the lifecycle states of an iBay order."""

    NEW = "NEW"
    DELIVERY = "DELIVERY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETURNED = "RETURNED"
