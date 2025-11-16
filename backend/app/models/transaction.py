from sqlmodel import Field
from app.models.base import BaseUuid, Base
from datetime import datetime, timezone


class Source(Base, table=True):
    name: str = Field(unique=True, description="Source name", max_length=100)
    description: str | None = Field(
        default=None, description="Source description", max_length=255
    )
    is_default: bool = Field(
        default=True, description="Is default source", index=True
    )
    user_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        description="User ID",
        index=True,
    )


class Transaction(BaseUuid, table=True):
    user_id: int = Field(
        description="User ID", foreign_key="user.id", index=True, nullable=False
    )
    category_id: int = Field(
        description="Category ID", foreign_key="category.id", index=True, nullable=False
    )
    source_id: int = Field(
        description="Source ID", foreign_key="source.id", index=True, nullable=False
    )
    description: str = Field(description="Transaction description", max_length=300)
    amount: float = Field(
        default=0.0, description="Transaction amount", index=True, ge=0, nullable=False
    )
    date: datetime = Field(description="Transaction date", index=True, nullable=False)
    state: str = Field(
        description="Transaction state", default="pending", index=True, nullable=False
    )
