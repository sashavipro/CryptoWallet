"""rest_api/src/infrastructure/providers/google_checker.py."""

import asyncio
import logging
from http import HTTPStatus

import aiohttp

from src.application.ports.providers.google_checker import GoogleCheckerProvider

logger = logging.getLogger(__name__)


class AiohttpGoogleChecker(GoogleCheckerProvider):
    """Implementation of GoogleCheckerProvider using aiohttp."""

    async def run_stress_test(self, requests_count: int = 10000) -> bool:
        """Execute a stress test against Google to check network stability."""
        logger.info("Starting stress test: %d requests to google.com", requests_count)
        url = "https://www.google.com"

        async def fetch(session: aiohttp.ClientSession) -> bool:
            try:
                async with session.get(url) as response:
                    return response.status == HTTPStatus.OK
            except (TimeoutError, aiohttp.ClientError):
                return False

        connector = aiohttp.TCPConnector(limit=1000)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [fetch(session) for _ in range(requests_count)]
            results = await asyncio.gather(*tasks)

        success_count = sum(results)
        logger.info(
            "Stress test finished. Successful: %d/%d",
            success_count,
            requests_count,
        )

        return success_count == requests_count
