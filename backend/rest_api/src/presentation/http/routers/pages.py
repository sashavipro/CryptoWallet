"""rest_api/src/presentation/http/routers/pages.py."""

import uuid
from pathlib import Path

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from src.application.interactors.profile import GetUserInteractor
from src.application.ports.providers import JwtProvider

router = APIRouter(tags=["pages"], include_in_schema=False)

# Вычисляем абсолютный путь до папки frontend/templates
# pages.py -> routers -> http -> presentation -> src ->
# rest_api -> backend -> CryptoWallet
PROJECT_ROOT = Path(__file__).resolve().parents[6]
TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


async def get_user_from_cookie(
    request: Request,
    jwt_provider: JwtProvider,
    interactor: GetUserInteractor,
):
    """Safely extract user from cookie for HTML rendering."""
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt_provider.verify(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        return await interactor(uuid.UUID(user_id_str))
    except Exception:  # noqa: BLE001
        return None


# --- Публичные страницы ---


@router.get("/login", response_class=HTMLResponse)
@inject
async def login_page(request: Request) -> HTMLResponse:
    """Render the login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
@inject
async def register_page(request: Request) -> HTMLResponse:
    """Render the registration page."""
    return templates.TemplateResponse("register.html", {"request": request})


# --- Защищенные страницы ---


@router.get("/profile", response_class=HTMLResponse, response_model=None)
@inject
async def profile_page(
    request: Request,
    jwt_provider: FromDishka[JwtProvider],
    interactor: FromDishka[GetUserInteractor],
) -> HTMLResponse | RedirectResponse:
    """Render the user profile page."""
    user = await get_user_from_cookie(request, jwt_provider, interactor)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "profile.html", {"request": request, "current_user": user}
    )


@router.get("/wallets", response_class=HTMLResponse, response_model=None)
@inject
async def wallets_page(
    request: Request,
    jwt_provider: FromDishka[JwtProvider],
    interactor: FromDishka[GetUserInteractor],
) -> HTMLResponse | RedirectResponse:
    """Render the user's wallets page."""
    user = await get_user_from_cookie(request, jwt_provider, interactor)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "wallets.html", {"request": request, "current_user": user}
    )


@router.get("/ibay", response_class=HTMLResponse, response_model=None)
@inject
async def ibay_page(
    request: Request,
    jwt_provider: FromDishka[JwtProvider],
    interactor: FromDishka[GetUserInteractor],
) -> HTMLResponse | RedirectResponse:
    """Render the iBay marketplace page."""
    user = await get_user_from_cookie(request, jwt_provider, interactor)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "ibay.html", {"request": request, "current_user": user}
    )


@router.get("/chat", response_class=HTMLResponse, response_model=None)
@inject
async def chat_page(
    request: Request,
    jwt_provider: FromDishka[JwtProvider],
    interactor: FromDishka[GetUserInteractor],
) -> HTMLResponse | RedirectResponse:
    """Render the global chat page."""
    user = await get_user_from_cookie(request, jwt_provider, interactor)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "chat.html", {"request": request, "current_user": user}
    )
