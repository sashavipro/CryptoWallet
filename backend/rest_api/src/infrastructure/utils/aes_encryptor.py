"""rest_api/src/infrastructure/utils/aes_encryptor.py."""

import logging

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

from src.infrastructure.settings import security_settings

logger = logging.getLogger(__name__)


class AesEncryptor:
    """Two-way encryptor implementation using AES (Fernet)."""

    def __init__(self) -> None:
        """Initialize encryptor with the secret key."""
        self._fernet = Fernet(security_settings.AES_SECRET_KEY)

    def encrypt(self, data: str) -> str:
        """Encrypt a plain string."""
        logger.debug("Encrypting data")
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string."""
        logger.debug("Decrypting data")
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except InvalidToken as e:
            logger.exception("Failed to decrypt data: Invalid or corrupted token")
            raise ValueError(f"Invalid or corrupted encrypted data: {e}") from e  # noqa: TRY003, EM102
