"""rest_api/src/domain/entities/base.py."""

import uuid
from dataclasses import dataclass
from dataclasses import field


@dataclass(kw_only=True)
class BaseEntity:
    """Базовый класс для всех доменных сущностей."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
