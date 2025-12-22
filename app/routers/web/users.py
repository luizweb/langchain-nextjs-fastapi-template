from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas import FilterPage
from app.security import (
    get_current_user_from_cookie,
    get_current_user_from_cookie_optional,
    get_password_hash,
)
from app.settings import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.templates_dir))

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user_from_cookie)]
CurrentUserOptional = Annotated[
    User, Depends(get_current_user_from_cookie_optional)
]


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


@router.get('/register', response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user: CurrentUserOptional,
):
    # Se já estiver logado, redireciona para home
    if current_user:
        if request.headers.get("HX-Request"):
            response = Response(status_code=HTTPStatus.NO_CONTENT)
            response.headers["HX-Redirect"] = "/web/"
            return response
        else:
            return RedirectResponse(
                url="/web/",
                status_code=HTTPStatus.SEE_OTHER
            )

    # Se for HTMX, retorna só o partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/register_partial.html",
            {"request": request}
        )

    # Acesso direto: retorna página completa
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "current_user": current_user}
    )


@router.post('/')
async def create_user(
    request: Request,
    session: Session,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    # Verifica se usuário já existe
    db_user = await session.scalar(
        select(User).where(
            (User.username == username) | (User.email == email)
        )
    )

    if db_user:
        if db_user.username == username:
            error_message = "Username já existe"
        else:
            error_message = "Email já existe"
        return templates.TemplateResponse(
            "partials/register_partial.html",
            {
                "request": request,
                "error": error_message,
                "username": username,
                "email": email,
            },
            status_code=HTTPStatus.OK,
        )

    # Cria novo usuário
    hashed_password = get_password_hash(password)

    db_user = User(
        username=username,
        password=hashed_password,
        email=email,
        is_admin=False  # Usuários criados via web não são admin por padrão
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    # Retorna partial de sucesso ou redireciona
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/register_success_partial.html",
            {"request": request},
            status_code=HTTPStatus.CREATED,
        )
    else:
        return RedirectResponse(
            url="/web/auth/login",
            status_code=HTTPStatus.SEE_OTHER,
        )


@router.get('/profile', response_class=HTMLResponse)
async def user_profile(
    request: Request,
    current_user: CurrentUser,
):
    # Se for HTMX, retorna só o partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/user_profile_partial.html",
            {"request": request, "user": current_user}
        )

    # Acesso direto: retorna página completa
    return templates.TemplateResponse(
        "user_profile.html",
        {
            "request": request,
            "user": current_user,
            "current_user": current_user
        }
    )


@router.get('/profile/edit', response_class=HTMLResponse)
async def user_profile_edit(
    request: Request,
    current_user: CurrentUser,
):
    # Se for HTMX, retorna só o partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/user_profile_edit_partial.html",
            {"request": request, "user": current_user}
        )

    # Acesso direto: retorna página completa
    return templates.TemplateResponse(
        "user_profile_edit.html",
        {
            "request": request,
            "user": current_user,
            "current_user": current_user
        }
    )


@router.put('/profile')
async def update_user_profile(  # noqa: PLR0913, PLR0917 #!todo
    request: Request,
    session: Session,
    current_user: CurrentUser,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()] = "",
):
    # Verifica se username ou email já existem (exceto para o próprio usuário)
    db_user = await session.scalar(
        select(User).where(
            ((User.username == username) |
             (User.email == email)) &
             (User.id != current_user.id)
        )
    )

    if db_user:
        if db_user.username == username:
            error_message = "Username já existe"
        else:
            error_message = "Email já existe"
        return templates.TemplateResponse(
            "partials/user_profile_edit_partial.html",
            {
                "request": request,
                "user": current_user,
                "error": error_message,
            },
            status_code=HTTPStatus.OK,
        )

    # Atualiza os dados do usuário
    current_user.username = username
    current_user.email = email

    # Só atualiza a senha se foi fornecida
    if password.strip():
        current_user.password = get_password_hash(password)

    await session.commit()
    await session.refresh(current_user)

    # Retorna partial com mensagem de sucesso
    return templates.TemplateResponse(
        "partials/user_profile_edit_partial.html",
        {
            "request": request,
            "user": current_user,
            "success": "Perfil atualizado com sucesso!",
        },
        status_code=HTTPStatus.OK,
    )


@router.delete('/{user_id}')
async def delete_user(
    user_id: int,
    session: Session,
    current_user: CurrentUser,
):
    # Verifica se o usuário atual é admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Not enough permissions'
        )

    # Verifica se o usuário está tentando deletar a si mesmo
    if current_user.id == user_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Você não pode deletar sua própria conta'
        )

    # Busca o usuário a ser deletado
    user_to_delete = await session.scalar(
        select(User).where(User.id == user_id)
    )

    if not user_to_delete:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Usuário não encontrado'
        )

    # Deleta o usuário
    await session.delete(user_to_delete)
    await session.commit()

    # Retorna 200 OK para que HTMX processe o swap/delete corretamente
    return Response(status_code=HTTPStatus.OK)
