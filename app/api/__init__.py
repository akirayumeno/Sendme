from app.api.messages import *
from fastapi import APIRouter

router = APIRouter()
router.include_router(router_message, tags=["messages"])