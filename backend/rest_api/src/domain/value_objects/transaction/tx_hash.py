"""rest_api/src/domain/value_objects/transaction/tx_hash.py."""

import re
from dataclasses import dataclass

from src.domain.exceptions import InvalidTxHashException

TX_HASH_REGEX = re.compile(r"^0x[a-fA-F0-9]{64}$")


@dataclass(frozen=True)
class TxHash:
    """Value object representing an EVM transaction hash."""

    value: str

    def __post_init__(self) -> None:
        """Validate the transaction hash format."""
        if not TX_HASH_REGEX.match(self.value):
            raise InvalidTxHashException
