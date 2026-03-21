"""rest_api/src/domain/value_objects/user/username.py."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MIN_LENGTH = 3
MAX_LENGTH = 50


@dataclass(frozen=True)
class Username:
    """Value object representing a user's display name."""

    value: str

    def __post_init__(self) -> None:
        """Validate the username length."""
        if not (MIN_LENGTH <= len(self.value) <= MAX_LENGTH):
            logger.debug(
                "Username validation failed for value '%s' (length %s)",
                self.value,
                len(self.value),
            )
            raise ValueError("Your username must be between 3 and 50 characters long.")  # noqa: TRY003, EM101
