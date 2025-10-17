from sqlmodel import Field
from app.models.base import BaseUuid, Base
from datetime import datetime


class Source(Base, table=True):
    name: str = Field(description="Source name", index=True)


class Transaction(BaseUuid, table=True):
    user_id: int = Field(foreign_key="user.id", index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    source_id: int = Field(foreign_key="source.id", index=True)
    description: str = Field(description="Transaction description")
    amount: float = Field(description="Transaction amount", default=0.0, index=True)
    date: datetime = Field(description="Transaction date", index=True)
    state: str = Field(description="Transaction state", default="pending", index=True)
    origin_json: dict[str, str | bool | int | float] = Field(
        description="Transaction origin JSON"
    )
