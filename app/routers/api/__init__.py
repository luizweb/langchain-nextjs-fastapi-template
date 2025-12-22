from fastapi import APIRouter

from . import auth, todos, users

router = APIRouter()
router.include_router(auth.router, prefix='/auth', tags=['auth'])
router.include_router(users.router, prefix='/users', tags=['users'])
router.include_router(todos.router, prefix='/todos', tags=['todos'])
