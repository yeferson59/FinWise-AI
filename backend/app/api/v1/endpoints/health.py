from fastapi import APIRouter
from app.services import health

router = APIRouter()


@router.get("")
def get_health() -> dict[str, str]:
    return health.get_health_status_app()
