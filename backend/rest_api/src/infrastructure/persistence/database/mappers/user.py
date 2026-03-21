"""rest_api/src/infrastructure/persistence/database/mappers/user.py."""

import logging

from src.domain.entities.user import User as DomainUser
from src.infrastructure.persistence.database.models.user import User as DBUser

logger = logging.getLogger(__name__)


def map_user_to_domain(db_user: DBUser) -> DomainUser:
    """Convert SQLAlchemy User model to Domain User entity."""
    logger.debug("Mapping DBUser to DomainUser for user_id: %s", db_user.id)
    return DomainUser(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        password_hash=db_user.password_hash,
        avatar_url=db_user.avatar_url,
        is_active=db_user.is_active,
        created_at=db_user.created_at,
    )


def map_domain_to_model(domain_user: DomainUser) -> DBUser:
    """Convert Domain User entity to SQLAlchemy User model."""
    logger.debug("Mapping DomainUser to DBUser for user_id: %s", domain_user.id)
    return DBUser(
        id=domain_user.id,
        email=domain_user.email,
        username=domain_user.username,
        password_hash=domain_user.password_hash,
        avatar_url=domain_user.avatar_url,
        is_active=domain_user.is_active,
        created_at=domain_user.created_at,
    )
