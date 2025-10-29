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


class TransactionFilters(BaseModel):
    """Filters for querying transactions."""

    user_id: int | None = Field(default=None, description="Filter by user ID", ge=1)
    category_id: int | None = Field(
        default=None, description="Filter by category ID", ge=1
    )
    source_id: int | None = Field(default=None, description="Filter by source ID", ge=1)
    state: str | None = Field(default=None, description="Filter by transaction state")
    start_date: datetime | None = Field(
        default=None, description="Filter by start date (inclusive)"
    )
    end_date: datetime | None = Field(
        default=None, description="Filter by end date (inclusive)"
    )
    min_amount: float | None = Field(
        default=None, description="Filter by minimum amount", ge=0
    )
    max_amount: float | None = Field(
        default=None, description="Filter by maximum amount", ge=0
    )
    sort_by: str | None = Field(
        default="date",
        description="Field to sort by (date, amount, created_at, updated_at)",
    )
    sort_desc: bool = Field(
        default=True, description="Sort in descending order (default: True)"
    )
