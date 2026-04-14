"""ibay/src/infrastructure/providers/google_checker.py."""

import asyncio
import logging
import time
from http import HTTPStatus

import aiohttp

from src.application.ports.providers.google_checker import GoogleCheckerProvider

logger = logging.getLogger(__name__)


class AiohttpGoogleChecker(GoogleCheckerProvider):
    """Implementation of GoogleCheckerProvider using aiohttp."""

    def __init__(self, target_url: str = "https://www.google.com") -> None:
        """Initialize the checker with a target URL."""
        self.target_url = target_url
        self.concurrency_limit = 200

    async def _make_request(
        self, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore
    ) -> bool:
        async with semaphore:
            try:
                async with session.get(self.target_url, timeout=10) as response:
                    return response.status == HTTPStatus.OK
            except (TimeoutError, aiohttp.ClientError):
                return False

    async def run_stress_test(self, requests_count: int) -> bool:
        """Execute a rapid burst of HTTP requests to test stability."""
        logger.info(
            "Starting %d requests to %s with concurrency limit %d.",
            requests_count,
            self.target_url,
            self.concurrency_limit,
        )

        semaphore = asyncio.Semaphore(self.concurrency_limit)

        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._make_request(session, semaphore) for _ in range(requests_count)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        success_count = sum(1 for r in results if r is True)

        logger.info(
            "Stress test finished: %d/%d successful. Duration: %.2f seconds.",
            success_count,
            requests_count,
            duration,
        )

        return success_count >= (requests_count * 0.5)
