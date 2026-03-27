"""ethereum/src/domain/exceptions.py."""


class DomainException(Exception):  # noqa: N818
    """Base domain exception for Ethereum service."""


class NegativeBalanceException(DomainException):
    """Balance cannot be negative."""


class InsufficientFundsException(DomainException):
    """Not enough funds to perform the transaction."""


class WalletNotFoundException(DomainException):
    """Wallet not found."""


class AssetNotFoundException(DomainException):
    """Cryptocurrency asset not found."""


class TransactionNotFoundException(DomainException):
    """Transaction not found."""


class InvalidAssetConfigurationException(DomainException):
    """ERC20 assets must have a contract address."""


class InvalidTransactionStateException(DomainException):
    """Transaction is not in a valid state for this operation."""


class NegativeFeeException(DomainException):
    """Transaction fee cannot be negative."""


class InvalidEthereumAddressException(DomainException):
    """Ethereum address format is invalid (must be 0x + 40 hex chars)."""


class InvalidPrivateKeyFormatException(DomainException):
    """Private key format is invalid (must be 64 hex chars)."""


class EmptyEncryptedKeyException(DomainException):
    """Encrypted private key cannot be empty."""


class InvalidTxHashException(DomainException):
    """Transaction hash format is invalid (must be 0x + 64 hex chars)."""


class NegativeTransactionValueException(DomainException):
    """Transaction value cannot be negative."""


class NegativeTransactionFeeException(DomainException):
    """Transaction fee cannot be negative."""


class InvalidNetworkNameException(DomainException):
    """Network name cannot be empty."""


class InvalidAssetSymbolException(DomainException):
    """Asset symbol must be 2-10 uppercase alphanumeric characters."""


class InvalidDecimalsException(DomainException):
    """Decimals must be between 0 and 36."""
