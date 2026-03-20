"""rest_api/src/domain/value_objects/permissions/chat_access.py."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HasChatAccess:
    """A setting that determines whether global chat is available."""

    value: bool = False

    def __bool__(self) -> bool:
        """Return boolean representation."""
        return self.value
