from sqlmodel import SQLModel, Field
from datetime import datetime


class Base(SQLModel):
    id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default=datetime.now(), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default=datetime.now(), description="Last update timestamp"
    )
