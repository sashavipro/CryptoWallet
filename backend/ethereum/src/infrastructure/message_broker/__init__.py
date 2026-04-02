"""ethereum/src/infrastructure/message_broker/__init__.py."""

from .block_subscriber import listen_to_new_blocks

__all__ = ("listen_to_new_blocks",)
