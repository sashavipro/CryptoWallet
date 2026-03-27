"""rest_api/src/application/ports/utils.py."""

import uuid
from datetime import datetime
from typing import Any
from typing import Protocol


class PasswordHasher(Protocol):
    """Port for password hashing and verification."""

    def hash(self, password: str) -> str:
        """Generate a hash from a raw password."""
        ...

    def verify(self, password: str, hashed_password: str) -> bool:
        """Verify a raw password against a hash."""
        ...


class IdGenerator(Protocol):
    """Port for generating unique identifiers."""

    def generate(self) -> uuid.UUID:
        """Generate a new UUID."""
        ...


class TimeProvider(Protocol):
    """Port for retrieving current time."""

    def now(self) -> datetime:
        """Return the current timezone-aware datetime."""
        ...


class Encryptor(Protocol):
    """Port for two-way encryption/decryption."""

    def encrypt(self, data: str) -> str:
        """Encrypt a plain string."""
        ...

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string."""
        ...


class Logger(Protocol):
    """Port for logging messages and exceptions."""

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'INFO'."""
        ...

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'ERROR'."""
        ...

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'WARNING'."""
        ...

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'DEBUG'."""
        ...

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'ERROR' along with exception information."""
        ...
