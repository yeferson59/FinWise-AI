from app.models.user import User
from app.db.session import SessionDep
from app.schemas.user import UserCreate
from sqlmodel import select


async def get_users(session: SessionDep) -> list[User]:
    users = session.exec(select(User).offset(0).limit(10)).all()
    return list(users)


async def create_user(user_create: UserCreate, session: SessionDep):
    user = User(**user_create.model_dump())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
