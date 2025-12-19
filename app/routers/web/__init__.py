from fastapi import APIRouter

from . import auth, pages, users

router = APIRouter()
router.include_router(users.router, prefix='/users', tags=['web-users'])
router.include_router(auth.router, prefix='/auth', tags=["web-auth"])
router.include_router(pages.router, tags=["web-pages"])
