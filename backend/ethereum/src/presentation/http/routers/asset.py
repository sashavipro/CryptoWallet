"""ethereum/src/presentation/http/routers/asset.py."""

from typing import Any

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database.models.asset import Asset

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("")
@inject
async def get_assets(
    session: FromDishka[AsyncSession],
) -> list[dict[str, Any]]:
    """Retrieve all available assets."""
    result = await session.execute(select(Asset))
    assets = result.scalars().all()

    return [{"id": str(a.id), "ticker": a.ticker, "name": a.name} for a in assets]
