"""rest_api/src/presentation/http/routers/asset.py."""

from typing import Any

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi_cache.decorator import cache

from src.application.interactors.asset import GetAssetsInteractor

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("")
@cache(expire=3600)
@inject
async def get_assets(
    interactor: FromDishka[GetAssetsInteractor],
) -> list[dict[str, Any]]:
    """Retrieve all available assets."""
    return await interactor()
