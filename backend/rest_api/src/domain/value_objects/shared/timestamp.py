"""rest_api/src/domain/value_objects/shared/timestamp.py."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Timestamp:
    """A time object that guarantees the existence of a time zone."""

    value: datetime

    def __post_init__(self) -> None:
        """Validate timezone awareness."""
        if self.value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware.")  # noqa: TRY003, EM101
