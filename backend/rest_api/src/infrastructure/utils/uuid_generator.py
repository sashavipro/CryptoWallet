"""rest_api/src/infrastructure/utils/uuid_generator.py."""

import uuid


class UuidGenerator:
    """UUID generator implementation."""

    def generate(self) -> uuid.UUID:
        """Generate a random UUID version 4."""
        return uuid.uuid4()
