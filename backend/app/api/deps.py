from typing import Annotated
from app.core.security import http_bearer
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import Depends
import jwt
from app.config import get_settings


settings = get_settings()


async def get_token_header(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)],
):
    if credentials.scheme != "Bearer":
        return

    if credentials.credentials == "":
        return

    payload = jwt.decode(
        jwt=credentials.credentials.strip(),
        key=settings.secret_key,
        algorithms=[settings.algorithm],
    )

    user_id = payload.get("sub")

    if user_id is None:
        return

    return user_id
