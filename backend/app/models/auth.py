from sqlmodel import Field
from app.models.base import Base
from datetime import datetime


class Session(Base, table=True):
    user_id: int = Field(
        description="User ID", default=None, foreign_key="user.id", nullable=False
    )
    token: str = Field(description="Token", unique=True, nullable=False)
    expires_at: datetime = Field(
        description="Expiration date", default=None, nullable=False
    )
    ip_address: str | None = Field(
        description="IP Address", default=None, nullable=True
    )
    user_agent: str | None = Field(
        description="User Agent", default=None, nullable=True
    )
