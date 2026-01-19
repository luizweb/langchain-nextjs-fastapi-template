from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import cleanup_checkpointer, initialize_checkpointer
from app.routers import auth, chat, projects, users
from app.schemas import Message


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Startup: Initialize checkpointer and create tables
    Shutdown: Cleanup resources
    """
    # Startup
    await initialize_checkpointer()
    yield
    # Shutdown
    await cleanup_checkpointer()


app = FastAPI(
    title='langchain-nextjs-fastapi',
    version='0.0.1',
    lifespan=lifespan,
    # docs_url='/api/docs',
    # redoc_url='/api/redoc',
    # openapi_url='/api/openapi.json',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(users.router, prefix='/users', tags=['users'])
app.include_router(projects.router, prefix='/projects', tags=['projects'])
app.include_router(chat.router, prefix='/chat', tags=['chat'])


# Health Check
@app.get('/health_check', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'FastAPI is running!'}
