from datetime import datetime
from typing import Any, Dict, List

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, ForeignKey, Text, func
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    registry,
    relationship,
)

table_registry = registry()


@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    projects: Mapped[list['Project']] = relationship(
        init=False,
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='selectin',
    )


@table_registry.mapped_as_dataclass
class Project:
    __tablename__ = 'projects'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['User'] = relationship(init=False, back_populates='projects')
    title: Mapped[str]
    description: Mapped[str] = mapped_column(default='')
    llm_prompt: Mapped[str] = mapped_column(default='')
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    file_contents: Mapped[list['FileContent']] = relationship(
        init=False,
        back_populates='project',
        cascade='all, delete-orphan',
        lazy='selectin',
    )


@table_registry.mapped_as_dataclass
class FileContent:
    __tablename__ = 'file_contents'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[List[float]] = mapped_column(Vector(1024))
    file_metadata: Mapped[Dict[str, Any]] = mapped_column(
        type_=JSON, default_factory=dict
    )
    project: Mapped['Project'] = relationship(
        init=False, back_populates='file_contents'
    )
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
