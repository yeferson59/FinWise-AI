from fastapi import APIRouter
from app.api.v1.endpoints import (
    users,
    agents,
    auth,
    ai_assistant,
    health,
    notifications,
    reports,
    transactions,
    categories,
    files,
)

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(
    ai_assistant.router, prefix="/ai-assistant", tags=["ai-assistant"]
)
router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
router.include_router(reports.router, prefix="/reports", tags=["reports"])
router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)
router.include_router(categories.router, prefix="/categories", tags=["categories"])
router.include_router(files.router, prefix="/files", tags=["files"])
