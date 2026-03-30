"""rest_api/src/infrastructure/utils/datetime_generator.py."""

from datetime import UTC
from datetime import datetime


class DatetimeGenerator:
    """Time provider implementation."""

    def now(self) -> datetime:
        """Return current UTC datetime."""
        return datetime.now(UTC)
