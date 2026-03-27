"""ethereum/src/application/ports/gateways/uow.py."""

import types
from typing import Protocol


class UnitOfWork(Protocol):
    """Transaction Management Port (Unit of Work Pattern)."""

    async def __aenter__(self) -> "UnitOfWork":
        """Enter the transaction context."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit the transaction context, committing or rolling back."""
        ...

    async def commit(self) -> None:
        """Transaction confirmation (can still be used manually if needed)."""
        ...

    async def rollback(self) -> None:
        """Transaction reversal (can still be used manually if needed)."""
        ...
