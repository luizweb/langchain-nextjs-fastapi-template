from contextlib import contextmanager
from datetime import datetime

import factory
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.database import get_session
from app.main import app
from app.models import Project, User, table_registry
from app.security import get_password_hash


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'test{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    password = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')


class ProjectFactory(factory.Factory):
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: f'Projeto {n}')
    description = factory.Faker('sentence')
    llm_prompt = factory.Faker('text', max_nb_chars=200)


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def session():
    # ✅ Usar imagem pgvector
    with PostgresContainer(
        'pgvector/pgvector:pg16',
        driver='psycopg'
    ) as postgres:
        engine = create_async_engine(postgres.get_connection_url())

        async with engine.begin() as conn:
            # ✅ Criar extensão pgvector ANTES das tabelas
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(table_registry.metadata.create_all)

        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session

        async with engine.begin() as conn:
            await conn.run_sync(table_registry.metadata.drop_all)

    await engine.dispose()


@contextmanager
def _mock_db_time(*, model, time=datetime(2024, 1, 1)):
    def fake_time_handler(mapper, connection, target):
        if hasattr(target, 'created_at'):
            target.created_at = time
        if hasattr(target, 'updated_at'):
            target.updated_at = time

    event.listen(model, 'before_insert', fake_time_handler)

    yield time

    event.remove(model, 'before_insert', fake_time_handler)


@pytest.fixture
def mock_db_time():
    return _mock_db_time


@pytest_asyncio.fixture
async def user(session):
    password = 'testtest'
    user = UserFactory(password=get_password_hash(password))

    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password

    return user


@pytest_asyncio.fixture
async def other_user(session):
    password = 'testtest'
    user = UserFactory(password=get_password_hash(password))

    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password

    return user


@pytest_asyncio.fixture
async def project(user, session):
    project = ProjectFactory(user_id=user.id)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@pytest_asyncio.fixture
async def other_project(other_user, session):
    project = ProjectFactory(user_id=other_user.id)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@pytest.fixture
def token(client, user):
    response = client.post(
        '/auth/token/',
        data={'username': user.email, 'password': user.clean_password},
    )
    return response.json()['access_token']
