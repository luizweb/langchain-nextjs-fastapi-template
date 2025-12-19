from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas import FilterPage
from app.security import get_current_user_from_cookie
from app.settings import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.templates_dir))

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user_from_cookie)]


@router.get('/', response_class=HTMLResponse)
async def read_users(
    request: Request,
    session: Session,
    current_user: CurrentUser,
    filter_users: Annotated[FilterPage, Query()],
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )

    query = await session.scalars(
        select(User).offset(filter_users.offset).limit(filter_users.limit)
    )
    users = query.all()

    context = {
        "request": request,
        "users": users,
        "offset": filter_users.offset,
        "limit": filter_users.limit,
        "current_user": current_user,
    }

    # Se for HTMX, retorna só o partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/users_partial.html",
            context
        )

    # Acesso direto: retorna página completa
    return templates.TemplateResponse(
        "users.html",  # ← vamos criar esse
        context
    )
