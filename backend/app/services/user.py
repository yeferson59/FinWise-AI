from app.models.user import User
from app.db.session import SessionDep
from app.schemas.user import UserCreate, UserUpdate, FilterPagination, UserListResponse
from sqlmodel import select, func
from app.core.security import hash_password
from app.utils.db import get_db_entities, get_entity_by_id, create_db_entity
import math


async def get_users(
    session: SessionDep, filter_pagination: FilterPagination
) -> UserListResponse:
    offset = (filter_pagination.page - 1) * filter_pagination.limit
    total = session.exec(select(func.count()).select_from(User)).one()
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


async def create_user(user_create: UserCreate, session: SessionDep):
    user_create.password = await hash_password(user_create.password)
    user = User(**user_create.model_dump())
    return create_db_entity(user, session)


async def update_user(
    user_id: int, user_update: UserUpdate, session: SessionDep
) -> User:
    user = session.exec(select(User).where(User.id == user_id)).one()
    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password"] = await hash_password(update_data["password"])

    for key, value in update_data.items():
        setattr(user, key, value)

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


async def delete_user(user_id: int, session: SessionDep) -> User:
    user = session.exec(select(User).where(User.id == user_id)).one()
    session.delete(user)
    session.commit()
    return user


async def get_user_by_email(email: str, session: SessionDep) -> User:
    user = session.exec(select(User).where(User.email == email)).one()
    return user
