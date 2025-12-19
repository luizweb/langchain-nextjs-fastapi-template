from http import HTTPStatus

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import auth, pages, todos, users
from app.schemas import Message

app = FastAPI()


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(pages.router)


@app.get('/health_check', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'FastAPI is running!'}


# Configurar arquivos estáticos e templates
app.mount(
    "/",
    StaticFiles(directory="frontend/static", html=True), name="static"
)
