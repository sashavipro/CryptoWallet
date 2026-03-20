"""rest_api/src/infrastructure/persistence/database/models/base.py."""

import datetime
import re
from typing import Annotated

from sqlalchemy import MetaData
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import mapped_column

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

IntPK = Annotated[int, mapped_column(primary_key=True)]

CreatedAt = Annotated[
    datetime.datetime,
    # pylint: disable=not-callable
    mapped_column(server_default=func.now()),
]

UpdatedAt = Annotated[
    datetime.datetime,
    # pylint: disable=not-callable
    mapped_column(server_default=func.now(), onupdate=func.now()),
]


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Automatically generates __tablename__ and configures indexes.
    """

    metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        """Generate table name automatically."""
        snake_case_name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()

        if not snake_case_name.endswith("s"):
            snake_case_name += "s"

        return snake_case_name
