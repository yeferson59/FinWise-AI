from pydantic import BaseModel, Field


class Login(BaseModel):
    email: str = Field(examples=["user@example.com"])
    password: str = Field(examples=["password"])


class LoginResponse(BaseModel):
    access_token: str | None = Field(default=None, examples=["access_token"])
    user_id: int | None = Field(default=None, examples=["user_id"])
    user_email: str | None = Field(default=None, examples=["user@example.com"])
    success: bool = Field(default=True, examples=[True, False])


class Register(BaseModel):
    first_name: str = Field(description="first name user register", examples=["Jhon"])
    last_name: str = Field(description="last name user register", examples=["Doe"])
    email: str = Field(
        description="email for user register",
        examples=["jhondoe@mail.com"],
        max_length=255,
        min_length=2,
        pattern=__import__("re").compile(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        ),
    )
    password: str = Field(
        description="password for user register",
        examples=["example"],
        min_length=8,
        max_length=20,
        pattern=__import__("re").compile(
            "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@#$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$"
        ),
    )
    confirm_password: str = Field(
        description="confirm password for user register",
        examples=["example"],
        min_length=8,
        max_length=20,
        pattern=__import__("re").compile(
            "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@#$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$"
        ),
    )
    terms_and_conditions: bool = Field(
        description="terms and conditions for user register",
        examples=[True, False],
        default=True,
    )
