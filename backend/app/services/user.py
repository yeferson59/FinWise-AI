from app.models.user import User
from app.db.session import SessionDep
from app.schemas.user import UserCreate, UserUpdate
from sqlmodel import select
from app.core.security import hash_password


async def get_users(session: SessionDep) -> list[User]:
    users = session.exec(select(User).offset(0).limit(10)).all()
    return list(users)


async def get_user(user_id: int, session: SessionDep) -> User:
    user = session.exec(select(User).where(User.id == user_id)).one()
    return user


async def create_user(user_create: UserCreate, session: SessionDep):
    user_create.password = await hash_password(user_create.password)
    user = User(**user_create.model_dump())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


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
