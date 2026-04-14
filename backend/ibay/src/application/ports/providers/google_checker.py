"""ibay/src/application/ports/providers/google_checker.py."""

from typing import Protocol


class GoogleCheckerProvider(Protocol):
    """Port defining the interface for the Google checker provider."""

    async def run_stress_test(self, requests_count: int) -> bool:
        """Execute a rapid burst of HTTP requests to Google to test stability."""
        ...
