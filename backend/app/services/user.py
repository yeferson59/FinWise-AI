from app.models.user import User
from app.db.session import SessionDep
from app.schemas.user import FilterPagination, UserListResponse, CreateUser, UpdateUser

from app.core.security import hash_password
from app.utils.crud import CRUDService
from app.utils.db import (
    get_entity_by_field,
    get_total_count,
    entity_exists,
    get_entities_with_pagination,
)
import math

# Initialize CRUD service for User
_user_crud = CRUDService[User, CreateUser, UpdateUser](User)


async def get_users(
    session: SessionDep, filter_pagination: FilterPagination
) -> UserListResponse:
    offset = (filter_pagination.page - 1) * filter_pagination.limit
    total = get_total_count(User, session)
    users = await _user_crud.get_all(session, offset, filter_pagination.limit)
    return UserListResponse(
        users=list(users),
        pagination=filter_pagination,
        total=total,
        pages=math.ceil(total / filter_pagination.limit),
    )


async def get_user(user_id: int, session: SessionDep) -> User:
    return await _user_crud.get_by_id(session, user_id)


async def create_user(create_user: CreateUser, session: SessionDep) -> User:
    # Hash password before creating user
    create_user.password = await hash_password(create_user.password)
    return await _user_crud.create(session, create_user)


async def update_user(
    user_id: int, update_user: UpdateUser, session: SessionDep
) -> User:
    # Hash password if it's being updated
    if update_user.password is not None:
        hashed_password = await hash_password(update_user.password)
        # Create a new UpdateUser with the hashed password
        update_user = update_user.model_copy(update={"password": hashed_password})

    return await _user_crud.update(session, user_id, update_user)


async def delete_user(user_id: int, session: SessionDep) -> User:
    return await _user_crud.delete(session, user_id)


async def get_user_by_email(email: str, session: SessionDep) -> User | None:
    return get_entity_by_field(User, "email", email, session)


async def check_user_exists_by_email(email: str, session: SessionDep) -> bool:
    return entity_exists(User, "email", email, session)


async def get_users_paginated(
    session: SessionDep,
    page: int = 1,
    limit: int = 10,
    order_by: str | None = None,
    order_desc: bool = False,
):
    return get_entities_with_pagination(
        User, session, page=page, limit=limit, order_by=order_by, order_desc=order_desc
    )
