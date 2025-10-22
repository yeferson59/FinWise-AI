from pydantic import BaseModel, Field


class CreateCategory(BaseModel):
    name: str = Field(description="Category name", max_length=100)
    description: str | None = Field(
        default=None, description="Category description", max_length=255
    )


class UpdateCategory(BaseModel):
    name: str | None = Field(description="Category name", max_length=100)
    description: str | None = Field(
        default=None, description="Category description", max_length=255
    )
