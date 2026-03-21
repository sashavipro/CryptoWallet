"""rest_api/src/domain/value_objects/user/email.py."""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@dataclass(frozen=True)
class Email:
    """Value object representing a valid email address."""

    value: str

    def __post_init__(self) -> None:
        """Validate the email format."""
        if not EMAIL_REGEX.match(self.value):
            logger.debug("Email validation failed for value: %s", self.value)
            raise ValueError(f"Invalid email format: {self.value}")  # noqa: TRY003, EM102
