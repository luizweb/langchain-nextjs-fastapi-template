from http import HTTPStatus
from typing import Annotated, Union

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas import FilterPage
from app.security import get_current_user

router = APIRouter(prefix='/pages', tags=['pages-users'])
templates = Jinja2Templates(directory="frontend/templates")

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get('/', response_class=HTMLResponse)
async def read_users(
    request: Request,
    session: Session,
    current_user: CurrentUser,
    filter_users: Annotated[FilterPage, Query()],
    hx_request: Annotated[Union[str, None], Header()] = None,
):

    # Verificação de permissão:
    # apenas administradores podem ver a lista de usuários

    if not current_user.is_admin:
        if hx_request:
            return templates.TemplateResponse(
                "unauthorized.jinja",
                {"request": request, "message": "Você não tem permissão."},
                status_code=HTTPStatus.OK
            )
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )

    query = await session.scalars(
        select(User).offset(filter_users.offset).limit(filter_users.limit)
    )
    users = query.all()

    if hx_request:
        return templates.TemplateResponse(
            "users.jinja",
            {
                "request": request,
                "users": users,
                "offset": filter_users.offset,
                "limit": filter_users.limit,
                "current_user": current_user  # Adicionado para uso no template
            }
        )
    return JSONResponse(
        content=jsonable_encoder(
            {"users": users,
             "current_user": current_user.email
            }
        )
    )
