"""rest_api/src/domain/value_objects/shared/entity_id.py."""

import uuid
from dataclasses import dataclass
from dataclasses import field


@dataclass(frozen=True)
class EntityId:
    """Universal Object Identifier."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        """Return string representation of the UUID."""
        return str(self.value)
