"""rest_api/src/application/ports/gateways/uow.py."""

from typing import Protocol


class UnitOfWork(Protocol):
    """Transaction Management Port (Unit of Work Pattern)."""

    async def commit(self) -> None:
        """Transaction confirmation."""
        ...

    async def rollback(self) -> None:
        """Transaction reversal."""
        ...
