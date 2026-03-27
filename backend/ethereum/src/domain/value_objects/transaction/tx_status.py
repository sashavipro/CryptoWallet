"""ethereum/src/domain/value_objects/transaction/tx_status.py."""

from enum import Enum


class TransactionStatus(str, Enum):
    """Value object (Enum) representing the transaction state."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
