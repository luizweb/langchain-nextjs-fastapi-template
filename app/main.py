from http import HTTPStatus

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.routers import api, web
from app.schemas import Message
from app.settings import settings

app = FastAPI(
    title="FastAPI-FullStack-Starter",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Static files
app.mount(
    "/static",
    StaticFiles(directory=str(settings.static_dir)),
    name="static"
)

# Routers
app.include_router(api.router, prefix="/api")
app.include_router(web.router, prefix="/web")


@app.get("/", include_in_schema=False)
async def root():
    # Pode ser 302, 303 ou 307; 307 é bem ok aqui
    return RedirectResponse(url="/web/", status_code=307)


# Health Check
@app.get('/health_check', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'FastAPI is running!'}
