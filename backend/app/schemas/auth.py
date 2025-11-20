from pydantic import BaseModel, Field


class Login(BaseModel):
    email: str = Field(examples=["user@example.com"])
    password: str = Field(examples=["password"])


class User(BaseModel):
    id: int = Field(description="user id", examples=[1])
    email: str = Field(description="user email", examples=["user@example.com"])
    first_name: str = Field(description="user first name", examples=["Jhon"])
    last_name: str = Field(description="user last name", examples=["Doe"])


class LoginResponse(BaseModel):
    access_token: str | None = Field(default=None, examples=["access_token"])
    user: User = Field(
        examples=[
            User(id=1, email="user@example.com", first_name="Jhon", last_name="Doe")
        ]
    )
    success: bool = Field(default=True, examples=[True, False])


class RegisterResponse(BaseModel):
    message: str = Field(examples=["Register successfully"])
    success: bool = Field(examples=[True])


class ErrorResponse(BaseModel):
    detail: str = Field(description="Error message")
    error_code: str = Field(description="Machine-readable error code")
    status_code: int = Field(description="HTTP status code")


class Register(BaseModel):
    first_name: str = Field(description="first name user register", examples=["Jhon"])
    last_name: str = Field(description="last name user register", examples=["Doe"])
    email: str = Field(
        description="email for user register",
        examples=["jhondoe@mail.com"],
        max_length=255,
        min_length=2,
        pattern=r"^[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$",
    )
    password: str = Field(
        description="password for user register",
        examples=["example"],
        min_length=8,
        max_length=20,
        pattern=r"^[A-Za-z\d@#$!%*?&]{8,20}$",
    )
    confirm_password: str = Field(
        description="confirm password for user register",
        examples=["example"],
        min_length=8,
        max_length=20,
        pattern=r"^[A-Za-z\d@#$!%*?&]{8,20}$",
    )
    terms_and_conditions: bool = Field(
        description="terms and conditions for user register",
        examples=[True, False],
        default=True,
    )
