"""rest_api/src/presentation/http/dependencies/rate_limit.py."""

from dishka.integrations.fastapi import FromDishka
from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from src.infrastructure.cache.rate_limiter import RedisRateLimiter


async def check_rate_limit(
    request: Request,
    rate_limiter: FromDishka[RedisRateLimiter],
) -> None:
    """Check if the client IP has exceeded the allowed request rate.

    Raises HTTP 429 Too Many Requests if the limit is exceeded.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    is_allowed = await rate_limiter.is_allowed(client_ip)

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )
