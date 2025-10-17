from pydantic import BaseModel, Field
from datetime import datetime, timezone


class CreateTransaction(BaseModel):
    user_id: int = Field(description="User ID", ge=1)
    category_id: int = Field(description="Category ID", ge=1)
    source_id: int = Field(description="Source ID", ge=1)
    description: str | None = Field(
        description="Transaction description", default=None, min_length=10
    )
    amount: float = Field(description="Transaction amount", default=1.0, ge=1)
    date: datetime = Field(
        description="Transaction date", le=datetime.now(timezone.utc)
    )


class UpdateTransaction(BaseModel):
    user_id: int | None = Field(default=None, description="User ID")
    category_id: int | None = Field(default=None, description="Category ID")
    source_id: int | None = Field(default=None, description="Source ID")
    description: str | None = Field(default=None, description="Transaction description")
    amount: float | None = Field(description="Transaction amount", default=1.0, ge=1)
    date: datetime | None = Field(
        default=None, description="Transaction date", le=datetime.now(timezone.utc)
    )
