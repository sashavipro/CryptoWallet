"""ethereum/src/application/ports/utils.py."""

from typing import Protocol


class Encryptor(Protocol):
    """Port for two-way encryption/decryption of private keys."""

    def encrypt(self, data: str) -> str:
        """Encrypt a plain string."""
        ...

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string."""
        ...
