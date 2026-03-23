"""rest_api/src/presentation/http/routers/auth.py."""

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter

from src.application.dtos.request import LoginUserRequest
from src.application.dtos.request import RegisterUserRequest
from src.application.dtos.response import TokenResponse
from src.application.interactors import LoginUserInteractor
from src.application.interactors import RegisterUserInteractor

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginUserRequest,
    interactor: FromDishka[LoginUserInteractor],
) -> TokenResponse:
    """Authenticate user and return JWT token."""
    return await interactor(request)


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterUserRequest,
    interactor: FromDishka[RegisterUserInteractor],
) -> TokenResponse:
    """Register a new user and return JWT token."""
    return await interactor(request)
