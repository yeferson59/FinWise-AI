from fastapi import APIRouter
from app.services import auth
from app.db.session import SessionDep
from app.schemas.auth import Login, LoginResponse, Register
from app.api.deps import CurrentSession

router = APIRouter()


@router.post("/login")
async def login(session: SessionDep, login_data: Login) -> LoginResponse:
    return await auth.login(session, login_data)


@router.post("/register")
async def register(session: SessionDep, register_data: Register) -> str:
    return await auth.register(session, register_data)


@router.post("/logout")
async def logout(session: SessionDep, current_session: CurrentSession) -> str:
    return await auth.logout(session, current_session)
