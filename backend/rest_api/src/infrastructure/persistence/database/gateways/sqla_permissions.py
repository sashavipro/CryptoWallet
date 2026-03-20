"""rest_api/src/infrastructure/persistence/database/gateways/sqla_permissions.py."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.permissions import UserPermission as DomainPermission
from src.infrastructure.persistence.database.mappers.permission import (
    map_domain_to_model,
)
from src.infrastructure.persistence.database.mappers.permission import (
    map_permission_to_domain,
)
from src.infrastructure.persistence.database.models.permission import (
    UserPermission as DBPermission,
)


class PermissionGateway:
    """Gateway for user permissions database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize gateway with active database session."""
        self.session = session

    async def add_permission(self, permission: DomainPermission) -> DomainPermission:
        """Add new permission records for a user."""
        db_permission = map_domain_to_model(permission)
        self.session.add(db_permission)
        await self.session.flush()
        return map_permission_to_domain(db_permission)

    async def get_by_user_id(self, user_id: uuid.UUID) -> DomainPermission | None:
        """Retrieve permissions for a specific user."""
        query = select(DBPermission).where(DBPermission.user_id == user_id)
        result = await self.session.execute(query)
        db_permission = result.scalar_one_or_none()

        if db_permission is None:
            return None
        return map_permission_to_domain(db_permission)

    async def update_permission(self, permission: DomainPermission) -> DomainPermission:
        """Update existing permission records."""
        db_permission = map_domain_to_model(permission)
        merged_permission = await self.session.merge(db_permission)
        await self.session.flush()
        return map_permission_to_domain(merged_permission)
