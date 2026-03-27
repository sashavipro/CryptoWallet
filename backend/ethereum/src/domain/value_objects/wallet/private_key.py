"""ethereum/src/domain/value_objects/wallet/private_key.py."""

import re
from dataclasses import dataclass

from src.domain.exceptions import EmptyEncryptedKeyException
from src.domain.exceptions import InvalidPrivateKeyFormatException

PRIVATE_KEY_REGEX = re.compile(r"^(0x)?[a-fA-F0-9]{64}$")


@dataclass(frozen=True)
class RawPrivateKey:
    """Value object for an unencrypted Ethereum private key.

    WARNING: Highly sensitive. Output is masked to prevent log leaks.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate the private key format."""
        if not PRIVATE_KEY_REGEX.match(self.value):
            raise InvalidPrivateKeyFormatException

    def __repr__(self) -> str:
        """Mask the private key in repr output."""
        return "<RawPrivateKey: [MASKED]>"

    def __str__(self) -> str:
        """Mask the private key in string output."""
        return "<RawPrivateKey: [MASKED]>"


@dataclass(frozen=True)
class EncryptedPrivateKey:
    """Value object representing an AES-encrypted private key."""

    value: str

    def __post_init__(self) -> None:
        """Validate that the encrypted string is not empty."""
        if not self.value or not self.value.strip():
            raise EmptyEncryptedKeyException
