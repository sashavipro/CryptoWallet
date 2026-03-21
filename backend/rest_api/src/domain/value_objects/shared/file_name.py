"""rest_api/src/domain/value_objects/shared/file_name.py."""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SAFE_CHARS_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
MAX_LENGTH = 255


@dataclass(frozen=True)
class FileName:
    """A safe filename for uploading to S3 (DO Spaces)."""

    value: str

    def __post_init__(self) -> None:
        """Validate filename structure and length."""
        if not self.value:
            logger.debug("FileName validation failed: empty value")
            raise ValueError("File name cannot be empty.")  # noqa: TRY003, EM101

        if len(self.value) > MAX_LENGTH:
            logger.debug(
                "FileName validation failed: exceeds max length (%s)", MAX_LENGTH
            )
            raise ValueError("File name must not exceed 255 characters.")  # noqa: TRY003, EM101

        if ".." in self.value or "/" in self.value or "\\" in self.value:
            logger.warning(
                "Security Warning: Potential Path Traversal "
                "attack detected in filename: %s",
                self.value,
            )
            raise ValueError("File name contains invalid paths (Path Traversal).")  # noqa: TRY003, EM101

        if not SAFE_CHARS_REGEX.match(self.value):
            logger.debug(
                "FileName validation failed: contains invalid characters. Value: %s",
                self.value,
            )
            raise ValueError("File name contains invalid characters.")  # noqa: TRY003, EM101
