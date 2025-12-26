from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Project, User
from app.schemas import Message, ProjectCreate, ProjectList, ProjectPublic
from app.security import get_current_user

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post('/', status_code=HTTPStatus.CREATED, response_model=ProjectPublic)
async def create_project(
    project: ProjectCreate,
    session: Session,
    current_user: CurrentUser,
):
    db_project = Project(
        user_id=current_user.id,
        title=project.title,
        description=project.description,
        llm_prompt=project.llm_prompt,
    )
    session.add(db_project)
    await session.commit()
    await session.refresh(db_project)

    return db_project


@router.get('/', response_model=ProjectList)
async def read_projects(
    session: Session,
    current_user: CurrentUser,
):
    query = select(Project).where(Project.user_id == current_user.id)
    result = await session.execute(query)
    projects = result.scalars().all()

    return ProjectList(projects=projects)


@router.put('/{project_id}', response_model=ProjectPublic)
async def update_project(
    project_id: int,
    project: ProjectCreate,
    session: Session,
    current_user: CurrentUser,
):
    db_project = await session.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )

    if not db_project:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Project not found'
        )

    db_project.title = project.title
    db_project.description = project.description
    db_project.llm_prompt = project.llm_prompt

    await session.commit()
    await session.refresh(db_project)

    return db_project


@router.delete('/{project_id}', response_model=Message)
async def delete_project(
    project_id: int,
    session: Session,
    current_user: CurrentUser,
):
    db_project = await session.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )

    if not db_project:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Project not found'
        )

    await session.delete(db_project)
    await session.commit()

    return {'message': 'Project deleted'}
