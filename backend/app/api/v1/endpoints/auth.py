from fastapi import APIRouter
from app.services import auth
from app.db.session import SessionDep
from app.schemas.auth import Login, LoginResponse

router = APIRouter()


@router.post("/login")
async def login(login_data: Login, session: SessionDep) -> LoginResponse:
    return await auth.login(session, login_data)
