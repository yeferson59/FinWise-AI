from fastapi import APIRouter
from app.api.v1.endpoints import users, agents

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(agents.router, prefix="/agents", tags=["agents"])
