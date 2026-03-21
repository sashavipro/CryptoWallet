"""rest_api/src/application/ports/tasks.py."""

from collections.abc import Callable
from typing import Any
from typing import Protocol


class TaskScheduler(Protocol):
    """Port for scheduling background tasks."""

    def schedule(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Schedule a function to be executed as a background task."""
        ...
