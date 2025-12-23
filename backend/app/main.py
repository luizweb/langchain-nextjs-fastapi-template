from http import HTTPStatus

from fastapi import FastAPI

from app.routers import auth, users
from app.schemas import Message

app = FastAPI(
    title='langchain-nextjs-fastapi',
    version='0.0.1',
    docs_url='/api/docs',
    redoc_url='/api/redoc',
    openapi_url='/api/openapi.json',
)


# Routers
app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(users.router, prefix='/users', tags=['users'])


# Health Check
@app.get('/health_check', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'FastAPI is running!'}
