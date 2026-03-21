"""rest_api/src/infrastructure/persistence/database/mappers/permission.py."""

import logging

from src.domain.entities.permissions import UserPermission as DomainPermission
from src.infrastructure.persistence.database.models.permission import (
    UserPermission as DBPermission,
)

logger = logging.getLogger(__name__)


def map_permission_to_domain(db_permission: DBPermission) -> DomainPermission:
    """Convert SQLAlchemy Permission model to Domain Permission entity."""
    logger.debug(
        "Mapping DBPermission to DomainPermission for user_id: %s",
        db_permission.user_id,
    )
    return DomainPermission(
        id=db_permission.id,
        user_id=db_permission.user_id,
        has_chat_access=db_permission.has_chat_access,
        granted_at=db_permission.granted_at,
    )


def map_domain_to_model(domain_permission: DomainPermission) -> DBPermission:
    """Convert Domain Permission entity to SQLAlchemy Permission model."""
    logger.debug(
        "Mapping DomainPermission to DBPermission for user_id: %s",
        domain_permission.user_id,
    )
    return DBPermission(
        id=domain_permission.id,
        user_id=domain_permission.user_id,
        has_chat_access=domain_permission.has_chat_access,
        granted_at=domain_permission.granted_at,
    )
