from fastapi import APIRouter, Query, Path, Depends
from typing import Annotated
from app.db.session import SessionDep
from app.models.user import User
from app.schemas.user import FilterPagination, UserListResponse, CreateUser, UpdateUser
from app.services import user
from app.api.deps import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
async def get_users(
    session: SessionDep, filter_pagination: Annotated[FilterPagination, Query]
) -> UserListResponse:
    return await user.get_users(session, filter_pagination)


@router.post("")
async def create_user(session: SessionDep, create_user: CreateUser) -> User:
    return await user.create_user(create_user, session)


@router.get("/{user_id}")
async def get_user(session: SessionDep, user_id: Annotated[int, Path(ge=1)]) -> User:
    return await user.get_user(user_id, session)


@router.patch("/{user_id}")
async def update_user(
    session: SessionDep,
    user_id: Annotated[int, Path(ge=1)],
    update_user: UpdateUser,
) -> User:
    return await user.update_user(user_id, update_user, session)


@router.delete("/{user_id}")
async def delete_user(session: SessionDep, user_id: Annotated[int, Path(ge=1)]) -> User:
    return await user.delete_user(user_id, session)


@router.get("/email/{email}")
async def get_user_by_email(
    session: SessionDep,
    email: Annotated[
        str,
        Path(
            max_length=300,
            min_length=1,
            regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        ),
    ],
) -> User | None:
    return await user.get_user_by_email(email, session)
