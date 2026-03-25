"""rest_api/src/infrastructure/cache/user_cache.py."""

import json
import logging
import uuid
from datetime import datetime

from redis.asyncio import Redis

from src.application.ports.gateways.user import UserGateway
from src.domain.entities.user import User

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300


class CachedUserGateway(UserGateway):
    """The Proxy/Decorator pattern for caching database requests."""

    def __init__(self, db_gateway: UserGateway, redis_client: Redis) -> None:
        """Initialize the caching gateway."""
        self.db_gateway = db_gateway
        self.redis = redis_client

    def _serialize(self, user: User) -> str:
        """Serialize the domain entity to JSON for Redis."""
        return json.dumps(
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "password_hash": user.password_hash,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
            }
        )

    def _deserialize(self, data_str: str) -> User:
        """Deserialize data from Redis back into a domain entity."""
        data = json.loads(data_str)
        return User(
            id=uuid.UUID(data["id"]),
            email=data["email"],
            username=data["username"],
            password_hash=data["password_hash"],
            avatar_url=data.get("avatar_url"),
            is_active=data["is_active"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve the user by their ID.

        First check the cache; if not found, query the database.
        """
        cache_key = f"cache:user:id:{user_id}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            logger.debug("Cache hit for user id: %s", user_id)
            return self._deserialize(cached_data)

        logger.debug("Cache miss for user id: %s", user_id)
        user = await self.db_gateway.get_user_by_id(user_id)

        if user:
            await self.redis.setex(cache_key, CACHE_TTL_SECONDS, self._serialize(user))

        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve the user by their email address from cache or database."""
        cache_key = f"cache:user:email:{email}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            logger.debug("Cache hit for user email: %s", email)
            return self._deserialize(cached_data)

        logger.debug("Cache miss for user email: %s", email)
        user = await self.db_gateway.get_user_by_email(email)

        if user:
            await self.redis.setex(cache_key, CACHE_TTL_SECONDS, self._serialize(user))

        return user

    async def add_user(self, user: User) -> User:
        """Add user data to the database and update the cache.

        We insert it into the database and immediately save it to the cache.
        """
        added_user = await self.db_gateway.add_user(user)

        await self.redis.setex(
            f"cache:user:id:{added_user.id}",
            CACHE_TTL_SECONDS,
            self._serialize(added_user),
        )
        await self.redis.setex(
            f"cache:user:email:{added_user.email}",
            CACHE_TTL_SECONDS,
            self._serialize(added_user),
        )

        return added_user

    async def update_user(self, user: User) -> User:
        """Cache invalidation (overwrite) when updating a profile or password."""
        updated_user = await self.db_gateway.update_user(user)

        await self.redis.setex(
            f"cache:user:id:{updated_user.id}",
            CACHE_TTL_SECONDS,
            self._serialize(updated_user),
        )
        await self.redis.setex(
            f"cache:user:email:{updated_user.email}",
            CACHE_TTL_SECONDS,
            self._serialize(updated_user),
        )

        return updated_user
