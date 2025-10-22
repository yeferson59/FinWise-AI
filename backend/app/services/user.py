from app.models.user import User
from app.db.session import SessionDep
from app.schemas.user import FilterPagination, UserListResponse, CreateUser, UpdateUser

from app.core.security import hash_password
from app.utils.db import (
    get_db_entities,
    get_entity_by_id,
    create_db_entity,
    update_db_entity,
    delete_db_entity,
    get_entity_by_field,
    get_total_count,
    entity_exists,
    get_entities_with_pagination,
)
import math


async def get_users(
    session: SessionDep, filter_pagination: FilterPagination
) -> UserListResponse:
    offset = (filter_pagination.page - 1) * filter_pagination.limit
    total = get_total_count(User, session)
    users = get_db_entities(
        entity=User, offset=offset, limit=filter_pagination.limit, session=session
    )
    return UserListResponse(
        users=list(users),
        pagination=filter_pagination,
        total=total,
        pages=math.ceil(total / filter_pagination.limit),
    )


async def get_user(user_id: int, session: SessionDep) -> User:
    return get_entity_by_id(User, user_id, session)


async def create_user(create_user: CreateUser, session: SessionDep) -> User:
    create_user.password = await hash_password(create_user.password)
    user = User(**create_user.model_dump())
    create_db_entity(user, session)
    return user


async def update_user(
    user_id: int, update_user: UpdateUser, session: SessionDep
) -> User:
    update_data = update_user.model_dump(exclude_unset=True)

    if "password" in update_data and isinstance(update_data["password"], str):
        update_data["password"] = await hash_password(update_data["password"])

    return update_db_entity(User, user_id, update_data, session)


async def delete_user(user_id: int, session: SessionDep) -> User:
    user = get_entity_by_id(User, user_id, session)
    delete_db_entity(User, user_id, session)
    return user


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
