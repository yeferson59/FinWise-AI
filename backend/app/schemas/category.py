from pydantic import BaseModel, Field


class CreateCategory(BaseModel):
    name: str = Field(description="Category name", max_length=100)
    description: str | None = Field(
        default=None, description="Category description", max_length=255
    )
    is_default: bool = Field(
        default=False, description="Is default category (user-created categories are not default)"
    )
    user_id: int | None = Field(
        default=None, description="User ID for custom categories"
    )


class UpdateCategory(BaseModel):
    name: str | None = Field(description="Category name", max_length=100)
    description: str | None = Field(
        default=None, description="Category description", max_length=255
    )
