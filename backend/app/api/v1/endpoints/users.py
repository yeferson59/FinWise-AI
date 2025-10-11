from fastapi import APIRouter
from app.db.session import SessionDep
from app.models.user import User
from app.schemas.user import UserCreate
from app.services import user

router = APIRouter()


@router.get("")
async def get_users(session: SessionDep) -> list[User]:
    return await user.get_users(session)


@router.post("")
async def create_user(user_create: UserCreate, session: SessionDep) -> User:
    return await user.create_user(user_create, session)
