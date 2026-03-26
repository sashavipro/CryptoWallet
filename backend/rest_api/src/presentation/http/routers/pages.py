"""rest_api/src/presentation/http/routers/pages.py."""

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"], include_in_schema=False)


@router.get("/login", response_class=HTMLResponse)
@inject
async def login_page(
    request: Request, templates: FromDishka[Jinja2Templates]
) -> HTMLResponse:
    """Render the login HTML page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
@inject
async def register_page(
    request: Request, templates: FromDishka[Jinja2Templates]
) -> HTMLResponse:
    """Render the registration HTML page."""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/profile", response_class=HTMLResponse)
@inject
async def profile_page(
    request: Request, templates: FromDishka[Jinja2Templates]
) -> HTMLResponse:
    """Render the user profile HTML page."""
    return templates.TemplateResponse("profile.html", {"request": request})


@router.get("/wallets", response_class=HTMLResponse)
@inject
async def wallets_page(
    request: Request, templates: FromDishka[Jinja2Templates]
) -> HTMLResponse:
    """Render the wallets management HTML page."""
    return templates.TemplateResponse("wallets.html", {"request": request})


@router.get("/ibay", response_class=HTMLResponse)
@inject
async def ibay_page(
    request: Request, templates: FromDishka[Jinja2Templates]
) -> HTMLResponse:
    """Render the iBay marketplace HTML page."""
    return templates.TemplateResponse("ibay.html", {"request": request})


@router.get("/chat", response_class=HTMLResponse)
@inject
async def chat_page(
    request: Request, templates: FromDishka[Jinja2Templates]
) -> HTMLResponse:
    """Render the global chat HTML page."""
    return templates.TemplateResponse("chat.html", {"request": request})
