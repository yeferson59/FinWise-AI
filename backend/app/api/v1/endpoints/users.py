from fastapi import APIRouter, Query, Depends
from typing import Annotated
from app.db.session import SessionDep
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, FilterPagination, UserListResponse
from app.services import user
from app.api.deps import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
async def get_users(
    session: SessionDep, filter_pagination: Annotated[FilterPagination, Query()]
) -> UserListResponse:
    return await user.get_users(session, filter_pagination)


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


@router.get("/email/{email}")
async def get_user_by_email(email: str, session: SessionDep) -> User | None:
    return await user.get_user_by_email(email, session)
