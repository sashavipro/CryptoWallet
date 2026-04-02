"""ethereum/src/domain/exceptions.py."""


class DomainException(Exception):  # noqa: N818
    """Base domain exception for Ethereum service."""


class InvalidEthereumAddressException(DomainException):
    """Ethereum address format is invalid (must be 0x + 40 hex chars)."""


class InvalidPrivateKeyFormatException(DomainException):
    """Private key format is invalid (must be 64 hex chars)."""


class EmptyEncryptedKeyException(DomainException):
    """Encrypted private key cannot be empty."""


class InvalidTxHashException(DomainException):
    """Transaction hash format is invalid (must be 0x + 64 hex chars)."""
