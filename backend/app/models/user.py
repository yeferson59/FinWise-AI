from sqlmodel import Field
from .base import Base


class User(Base, table=True):
    first_name: str = Field(
        description="User's first name",
        nullable=False,
        min_length=2,
        max_length=100,
    )
    last_name: str = Field(
        description="User's last name",
        nullable=False,
        min_length=2,
        max_length=100,
    )
    email: str = Field(
        description="User's email address",
        unique=True,
        nullable=False,
        min_length=8,
        max_length=255,
    )
    password: str | None = Field(
        default=None,
        description="User's password",
        nullable=False,
        min_length=8,
        max_length=300,
    )
