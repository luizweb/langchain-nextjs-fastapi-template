# routers/web/auth.py
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.security import (
    create_access_token,
    get_current_user_from_cookie_optional,
    verify_password,
)
from app.settings import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.templates_dir))

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentWebUserOptional = Annotated[
    User,
    Depends(get_current_user_from_cookie_optional)
]


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    current_user: CurrentWebUserOptional,
):
    # Se já estiver logado, redireciona para home
    if current_user:
        return RedirectResponse(url="/web/", status_code=HTTPStatus.SEE_OTHER)

    # Se for HTMX, retorna só o partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/login_partial.html",
            {"request": request}
        )

    # Acesso direto (favoritos, digitando URL): retorna página completa
    # Criamos um template "wrapper" que extende base.html
    return templates.TemplateResponse(
        "login.html",  # ← vamos criar esse
        {"request": request, "current_user": current_user}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    session: Session,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    user = await session.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(password, user.password):
        # SEMPRE retorna o partial (porque o form está dentro do partial)
        return templates.TemplateResponse(
            "partials/login_partial.html",
            {
                "request": request,
                "error": "E-mail ou senha inválidos",
                "email": email,
            },
            status_code=HTTPStatus.OK,  # ← mudei para 200 para HTMX processar
        )

    access_token = create_access_token(data={"sub": user.email})

    # Verifica se é uma requisição HTMX
    if request.headers.get("HX-Request"):
        response = Response(status_code=HTTPStatus.NO_CONTENT)
        response.headers["HX-Redirect"] = "/web/"
    else:
        response = RedirectResponse(
            url="/web/",
            status_code=HTTPStatus.SEE_OTHER,
        )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.post("/logout")
async def logout(request: Request):
    # Verifica se é requisição HTMX
    if request.headers.get("HX-Request"):
        response = Response(status_code=HTTPStatus.NO_CONTENT)
        response.headers["HX-Redirect"] = "/web/"
    else:
        # Fallback para requisições normais (se houver)
        response = RedirectResponse(
            url="/web/",
            status_code=HTTPStatus.SEE_OTHER,
        )

    response.delete_cookie(key="access_token")
    return response
