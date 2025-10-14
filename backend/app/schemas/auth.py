from pydantic import BaseModel, Field


class Login(BaseModel):
    email: str = Field(examples=["user@example.com"])
    password: str = Field(examples=["password"])


class LoginResponse(BaseModel):
    access_token: str | None = Field(default=None, examples=["access_token"])
    user_id: int | None = Field(default=None, examples=["user_id"])
    user_email: str | None = Field(default=None, examples=["user@example.com"])
    success: bool = Field(default=True, examples=[True])
