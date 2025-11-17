from typing import Annotated
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError

from app.core.security import http_bearer
from app.config import get_settings
from app.db.session import SessionDep
from app.utils.db import get_entity_by_id
from app.models.auth import Session
from app.models.user import User


# Common pagination parameters
def pagination_params(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> dict[str, int]:
    """
    Common pagination parameters for API endpoints.

    Args:
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)

    Returns:
        Dictionary with offset and limit
    """
    return {"offset": offset, "limit": limit}


PaginationParams = Annotated[dict[str, int], Depends(pagination_params)]


async def get_current_session(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)],
    session: SessionDep,
) -> Session:
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Bearer token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()

    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error validating token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_id = payload.get("sub")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing session identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        session_id = int(session_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: corrupt session identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_db = get_entity_by_id(Session, session_id, session)
    if not session_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = payload.get("access_token")
    if session_db.token != access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or it has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    current_time = datetime.now(timezone.utc)
    expires_at = session_db.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < current_time:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        data_token = jwt.decode(
            jwt=access_token,
            key=settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error validating token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not data_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if int(data_token.get("sub")) != session_db.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return session_db


async def get_current_user(
    current_session: Annotated[Session, Depends(get_current_session)],
    session: SessionDep,
) -> User:
    user = get_entity_by_id(User, current_session.user_id, session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive. Contact the administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if hasattr(current_user, "is_active") and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User disabled.",
        )

    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentSession = Annotated[Session, Depends(get_current_session)]
