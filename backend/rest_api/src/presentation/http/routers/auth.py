"""rest_api/src/presentation/http/routers/auth.py."""

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import Depends

from src.application.dtos.request import LoginUserRequest
from src.application.dtos.request import RegisterUserRequest
from src.application.dtos.response import TokenResponse
from src.application.interactors import LoginUserInteractor
from src.application.interactors import RegisterUserInteractor
from src.presentation.http.dependencies.rate_limit import check_rate_limit

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
    dependencies=[Depends(check_rate_limit)],
)


@router.post("/login", response_model=TokenResponse)
@inject
async def login(
    request: LoginUserRequest,
    interactor: FromDishka[LoginUserInteractor],
) -> TokenResponse:
    """Authenticate user and return JWT token."""
    return await interactor(request)


@router.post("/register", response_model=TokenResponse)
@inject
async def register(
    request: RegisterUserRequest,
    interactor: FromDishka[RegisterUserInteractor],
) -> TokenResponse:
    """Register a new user and return JWT token."""
    return await interactor(request)
