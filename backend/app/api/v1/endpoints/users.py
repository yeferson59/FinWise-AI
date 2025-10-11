from fastapi import APIRouter
from app.db.session import SessionDep
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services import user

router = APIRouter()


@router.get("")
async def get_users(session: SessionDep) -> list[User]:
    return await user.get_users(session)


@router.post("")
async def create_user(user_create: UserCreate, session: SessionDep) -> User:
    return await user.create_user(user_create, session)


@router.get("/{user_id}")
async def get_user(user_id: int, session: SessionDep) -> User:
    return await user.get_user(user_id, session)


@router.patch("/{user_id}")
async def update_user(
    user_id: int, user_update: UserUpdate, session: SessionDep
) -> User:
    return await user.update_user(user_id, user_update, session)


@router.delete("/{user_id}")
async def delete_user(user_id: int, session: SessionDep) -> User:
    return await user.delete_user(user_id, session)
