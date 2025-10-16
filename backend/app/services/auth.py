from app.services import user
from app.schemas import auth, user as user_schemas
from app.db.session import SessionDep
from app.core.security import verify_password, create_token
from app.models.auth import Session
from datetime import datetime, timedelta
from app.config import get_settings
from app.utils.db import create_db_entity

settings = get_settings()


async def login(session: SessionDep, login_data: auth.Login) -> auth.LoginResponse:
    user_data = await user.get_user_by_email(login_data.email, session)

    if not user_data:
        return auth.LoginResponse(success=False)

    if not user_data.password:
        return auth.LoginResponse(success=False)

    if not await verify_password(login_data.password, user_data.password):
        return auth.LoginResponse(success=False)

    token = await create_token({"sub": str(user_data.id), "email": user_data.email})

    session_data = Session(
        user_id=user_data.id,
        token=token,
        expires_at=datetime.now()
        + timedelta(minutes=settings.access_token_expire_minutes),
    )

    create_db_entity(session_data, session)

    return auth.LoginResponse(
        success=True,
        user_id=user_data.id,
        user_email=user_data.email,
        access_token=session_data.token,
    )


async def register(session: SessionDep, register_data: auth.Register):
    if register_data.password != register_data.confirm_password:
        return "No successfully"

    user_create = user_schemas.UserCreate(
        first_name=register_data.first_name,
        last_name=register_data.last_name,
        email=register_data.email,
        password=register_data.password,
    )

    user_data = await user.create_user(user_create, session)

    if not user_data:
        return "No successfully"

    return "Register successfully"
