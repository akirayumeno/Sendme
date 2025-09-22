from app.api.auth import *
from app.api.files import *
from app.api.messages import *
from fastapi import APIRouter

router = APIRouter()
router.include_router(router_files, tags=["files"])
router.include_router(router_message, tags=["messages"])