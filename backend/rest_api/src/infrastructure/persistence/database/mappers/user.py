"""rest_api/src/infrastructure/persistence/database/mappers/user.py."""

from src.domain.entities.user import User as DomainUser
from src.infrastructure.persistence.database.models.user import User as DBUser


def map_user_to_domain(db_user: DBUser) -> DomainUser:
    """Convert SQLAlchemy User model to Domain User entity."""
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
    return DBUser(
        id=domain_user.id,
        email=domain_user.email,
        username=domain_user.username,
        password_hash=domain_user.password_hash,
        avatar_url=domain_user.avatar_url,
        is_active=domain_user.is_active,
        created_at=domain_user.created_at,
    )
