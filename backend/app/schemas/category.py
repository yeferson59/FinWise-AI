from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(description="Category name", max_length=100)
    description: str | None = Field(
        default=None, description="Category description", max_length=255
    )


class CategoryUpdate(BaseModel):
    name: str | None = Field(description="Category name", max_length=100)
    description: str | None = Field(
        default=None, description="Category description", max_length=255
    )
