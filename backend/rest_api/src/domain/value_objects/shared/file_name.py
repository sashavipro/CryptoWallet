"""rest_api/src/domain/value_objects/shared/file_name.py."""

import re
from dataclasses import dataclass

SAFE_CHARS_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
MAX_LENGTH = 255


@dataclass(frozen=True)
class FileName:
    """A safe filename for uploading to S3 (DO Spaces)."""

    value: str

    def __post_init__(self) -> None:
        """Validate filename structure and length."""
        if not self.value:
            raise ValueError("File name cannot be empty.")  # noqa: TRY003, EM101

        if len(self.value) > MAX_LENGTH:
            raise ValueError("File name must not exceed 255 characters.")  # noqa: TRY003, EM101

        if ".." in self.value or "/" in self.value or "\\" in self.value:
            raise ValueError("File name contains invalid paths (Path Traversal).")  # noqa: TRY003, EM101

        if not SAFE_CHARS_REGEX.match(self.value):
            raise ValueError("File name contains invalid characters.")  # noqa: TRY003, EM101
