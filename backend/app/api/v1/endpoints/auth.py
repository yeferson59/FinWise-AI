from fastapi import APIRouter

from app.api.deps import CurrentSession
from app.db.session import SessionDep
from app.schemas.auth import Login, LoginResponse, Register, RegisterResponse
from app.services import auth

router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"description": "Unauthorized - Invalid credentials"},
        500: {"description": "Internal Server Error"},
    },
)
async def login(session: SessionDep, login_data: Login) -> LoginResponse:
    return await auth.login(session, login_data)


@router.post(
    "/register",
    response_model=RegisterResponse,
    responses={
        400: {"description": "Bad Request - Validation error"},
        500: {"description": "Internal Server Error"},
    },
)
async def register(session: SessionDep, register_data: Register) -> RegisterResponse:
    return await auth.register(session, register_data)


@router.post("/logout")
async def logout(session: SessionDep, current_session: CurrentSession) -> dict:
    await auth.logout(session, current_session)
    return {"message": "Sesión cerrada exitosamente", "success": True}
