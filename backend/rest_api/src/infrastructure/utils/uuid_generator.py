"""rest_api/src/infrastructure/utils/uuid_generator.py."""

import logging
import uuid

logger = logging.getLogger(__name__)


class UuidGenerator:
    """UUID generator implementation."""

    def generate(self) -> uuid.UUID:
        """Generate a random UUID version 4."""
        new_uuid = uuid.uuid4()
        logger.debug("Generated new UUID: %s", new_uuid)
        return new_uuid
