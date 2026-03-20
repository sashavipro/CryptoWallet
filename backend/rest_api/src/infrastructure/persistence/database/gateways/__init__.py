"""rest_api/src/infrastructure/persistence/database/gateways/__init__.py."""

from .sqla_permissions import PermissionGateway
from .sqla_user import UserGateway

__all__ = (
    "PermissionGateway",
    "UserGateway",
)
