from sqlmodel import Field
from app.models.base import Base


class Category(Base, table=True):
    name: str = Field(unique=True, description="Category name", max_length=100)
    description: str | None = Field(
        default=None, description="Category description", max_length=255
    )
