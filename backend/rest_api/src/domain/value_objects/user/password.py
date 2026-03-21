"""rest_api/src/domain/value_objects/user/password.py."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MIN_LENGTH = 8
MAX_LENGTH = 20


@dataclass(frozen=True)
class RawPassword:
    """A raw password object with strict validation rules."""

    value: str

    def __post_init__(self) -> None:
        """Validate password strength."""
        if not (MIN_LENGTH <= len(self.value) <= MAX_LENGTH):
            logger.debug("RawPassword validation failed: invalid length")
            raise ValueError("The password must be between 8 and 20 characters long.")  # noqa: TRY003, EM101
        if not any(c.islower() for c in self.value):
            logger.debug("RawPassword validation failed: missing lowercase letter")
            raise ValueError("The password must contain at least one lowercase letter.")  # noqa: TRY003, EM101
        if not any(c.isupper() for c in self.value):
            logger.debug("RawPassword validation failed: missing uppercase letter")
            raise ValueError("The password must contain at least one uppercase letter.")  # noqa: TRY003, EM101
        if not any(c.isdigit() for c in self.value):
            logger.debug("RawPassword validation failed: missing digit")
            raise ValueError("The password must contain at least one number.")  # noqa: TRY003, EM101


@dataclass(frozen=True)
class PasswordHash:
    """Hash of the password."""

    value: str

    def __post_init__(self) -> None:
        """Validate password hash format."""
        if not self.value.startswith("$argon2"):
            logger.error(
                "PasswordHash validation failed: Invalid hash format. Expected argon2."
            )
            raise ValueError("Invalid password hash format.")  # noqa: TRY003, EM101
