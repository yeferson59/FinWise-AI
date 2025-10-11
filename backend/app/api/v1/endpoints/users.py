from fastapi import APIRouter
from app.db.session import SessionDep
from app.models.user import User
from app.schemas.user import UserCreate
from sqlmodel import select

router = APIRouter()


@router.get("")
async def get_users(session: SessionDep) -> list[User]:
    users = session.exec(select(User).offset(0).limit(10)).all()
    return list(users)


@router.post("")
async def create_user(user_create: UserCreate, session: SessionDep) -> User:
    db_user = User(**user_create.model_dump())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
