from pwdlib import PasswordHash
from datetime import timedelta, timezone, datetime
import jwt
from app.config import get_settings
from typing import Any
from fastapi.security import HTTPBearer

http_bearer = HTTPBearer()

settings = get_settings()
password_hash = PasswordHash.recommended()


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


async def hash_password(password: str) -> str:
    return password_hash.hash(password)


async def create_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
