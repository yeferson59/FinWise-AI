from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.api.deps import CurrentSession
from app.config import get_settings
from app.core.exceptions import (
    AuthProcessError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    PasswordMismatchError,
    TermsNotAcceptedError,
    UserNotFoundError,
)
from app.core.security import create_token, verify_password
from app.db.session import SessionDep
from app.models.auth import Session
from app.schemas import auth
from app.schemas import user as user_schemas
from app.services import user
from app.utils.db import create_db_entity, delete_db_entity


async def login(session: SessionDep, login_data: auth.Login) -> auth.LoginResponse:
    user_data = await user.get_user_by_email(login_data.email, session)

    if not user_data:
        raise InvalidCredentialsError()

    if not user_data.password:
        raise InvalidCredentialsError()

    if not await verify_password(login_data.password, user_data.password):
        raise InvalidCredentialsError()

    try:
        token = await create_token({"sub": str(user_data.id), "email": user_data.email})
        settings = get_settings()

        session_data = Session(
            user_id=user_data.id,
            token=token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.access_token_expire_minutes),
        )

        create_db_entity(session_data, session)

        access_token = await create_token(
            {"sub": str(session_data.id), "access_token": token}
        )

        return auth.LoginResponse(
            user=auth.User(
                id=user_data.id,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
            ),
            access_token=access_token,
            success=True,
        )
    except HTTPException:
        raise UserNotFoundError
    except Exception:
        raise AuthProcessError(
            detail="Error al procesar login",
            error_code="LOGIN_PROCESS_ERROR",
        )


async def register(
    session: SessionDep, register_data: auth.Register
) -> auth.RegisterResponse:
    """
    Register a new user.

    Raises:
        PasswordMismatchError: If passwords don't match
        TermsNotAcceptedError: If terms not accepted
        EmailAlreadyExistsError: If email already registered
        AuthProcessError: If user creation fails
    """
    if register_data.password != register_data.confirm_password:
        raise PasswordMismatchError()

    if not register_data.terms_and_conditions:
        raise TermsNotAcceptedError()

    # Check if email already exists
    existing_user = await user.get_user_by_email(register_data.email, session)
    if existing_user:
        raise EmailAlreadyExistsError()

    user_create = user_schemas.CreateUser(
        first_name=register_data.first_name,
        last_name=register_data.last_name,
        email=register_data.email,
        password=register_data.password,
    )

    try:
        user_data = await user.create_user(user_create, session)

        if not user_data:
            raise AuthProcessError(
                detail="Error al crear el usuario",
                error_code="USER_CREATION_FAILED",
            )

        return auth.RegisterResponse(
            message="Usuario registrado exitosamente",
            success=True,
        )
    except HTTPException:
        raise
    except Exception:
        raise AuthProcessError(
            detail="Error al procesar el registro",
            error_code="REGISTRATION_PROCESS_ERROR",
        )


async def logout(session: SessionDep, current_session: CurrentSession):
    """
    Logout user by invalidating session.

    Raises:
        AuthProcessError: If session deletion fails
    """
    try:
        delete_db_entity(Session, current_session.id, session)
    except HTTPException:
        raise
    except Exception:
        raise AuthProcessError(
            detail="Error al cerrar sesión",
            error_code="LOGOUT_FAILED",
        )
