"""ethereum/src/domain/entities/base.py."""

import uuid
from dataclasses import dataclass
from dataclasses import field


@dataclass(kw_only=True)
class BaseEntity:
    """Base class for all domain entities."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
