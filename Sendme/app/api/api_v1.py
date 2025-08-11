from fastapi import APIRouter
from .endpoints import users, messages

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(messages.router, prefix="/messages", tags=["messages"])