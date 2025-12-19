# routers/web/pages.py
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models import User
from app.security import get_current_user_from_cookie_optional
from app.settings import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.templates_dir))

CurrentWebUserOptional = Annotated[
    User,
    Depends(get_current_user_from_cookie_optional)
]


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    current_user: CurrentWebUserOptional,
):
    context = {
        "request": request,
        "current_user": current_user,
    }

    # Se for HTMX, retorna só o partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/home_partial.html",
            context
        )

    # Acesso direto: retorna página completa
    return templates.TemplateResponse(
        "index.html",  # ← já extende base.html
        context
    )
