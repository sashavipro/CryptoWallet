"""ibay/src/infrastructure/providers/google_checker.py."""

import asyncio
import logging
from http import HTTPStatus

import aiohttp

from src.application.ports.providers.google_checker import GoogleCheckerProvider

logger = logging.getLogger(__name__)


class AiohttpGoogleChecker(GoogleCheckerProvider):
    """Implementation of GoogleCheckerProvider using aiohttp."""

    def __init__(self, target_url: str = "https://httpbin.org/get") -> None:
        """Initialize the checker with a target URL and concurrency limit."""
        self.target_url = target_url
        self.semaphore = asyncio.Semaphore(50)

    async def _make_request(self, session: aiohttp.ClientSession) -> bool:
        async with self.semaphore:
            try:
                async with session.get(self.target_url, timeout=5) as response:
                    return response.status == HTTPStatus.OK
            except (TimeoutError, aiohttp.ClientError):
                return False

    async def run_stress_test(self, requests_count: int) -> bool:
        """Execute a rapid burst of HTTP requests to test stability."""
        logger.info("Starting %d requests to %s", requests_count, self.target_url)
        async with aiohttp.ClientSession() as session:
            tasks = [self._make_request(session) for _ in range(requests_count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        logger.info(
            "Stress test finished: %d/%d successful", success_count, requests_count
        )
        return success_count >= (requests_count * 0.5)
