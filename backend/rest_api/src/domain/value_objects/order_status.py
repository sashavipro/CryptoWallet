"""rest_api/src/domain/value_objects/order_status.py."""

import enum


class OrderStatus(enum.Enum):
    """Enumeration representing the various states of an iBay order."""

    NEW = "new"
    DELIVERY = "delivery"
    COMPLETED = "completed"
    FAILED = "failed"
    RETURNED = "returned"
