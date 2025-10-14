from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import uuid4, UUID


class Base(SQLModel):
    id: int = Field(default=None, primary_key=True, description="Primary key of table")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp", nullable=False
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp",
        nullable=False,
    )


class BaseUuid(SQLModel):
    id: UUID = Field(
        default_factory=uuid4, primary_key=True, description="Primary key of table"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp", nullable=False
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp",
        nullable=False,
    )
