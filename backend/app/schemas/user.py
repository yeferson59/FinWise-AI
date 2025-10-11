from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=100, examples=["John"])
    last_name: str = Field(min_length=2, max_length=100, examples=["Doe"])
    email: str = Field(min_length=8, max_length=255, examples=["john.doe@example.com"])
    password: str = Field(min_length=8, max_length=20, examples=["SecurePass123"])


class UserUpdate(BaseModel):
    first_name: str | None = Field(
        default=None, min_length=2, max_length=100, examples=["John"]
    )
    last_name: str | None = Field(
        default=None, min_length=2, max_length=100, examples=["Doe"]
    )
    email: str | None = Field(
        default=None, min_length=8, max_length=255, examples=["john.doe@example.com"]
    )
    password: str | None = Field(
        default=None, min_length=8, max_length=20, examples=["SecurePass123"]
    )
